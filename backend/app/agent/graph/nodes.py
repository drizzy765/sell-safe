"""Harness nodes: observe, route, sales_agent, respond."""

import json
from pathlib import Path

from app.agent.graph.state import State, Turn
from app.agent.reply_check import ReplyCheckError, check_reply, fallback_reply
from app.agent.tools.catalog import CatalogTools
from app.agent.tools.orders import OrderTools
from app.channels.base import ChannelAdapter
from app.db.echo_store import EchoStore
from app.decisions.base import JevClient
from app.llm.base import LLMProvider

_MAX_STEPS = 6
_MAX_TOOL_CALLS = 3


def _load_style(language: str) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / f"{language}.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""


def _system_prompt(
    language: str,
    tools: list[dict],
    order: dict | None,
    business_name: str | None = None,
) -> str:
    style = _load_style(language)
    lines = [
        "You are Sell-Safe, a WhatsApp shop assistant for Nigerian small sellers.",
        f"Business: {business_name or 'the shop'}.",
        style,
        "You have access to the following tools. Use them when needed.",
        "If a tool result includes crypto_instructions, copy that sentence exactly.",
        "Do not invent a wallet address or a USDC amount.",
        "When the buyer asks for account number / how to pay, call get_payment_details.",
        "If payment_details.configured is true, share bank_name, "
        "account_name, and account_number exactly.",
        "If configured is false, say the shop has not added transfer "
        "details yet — do not ask for a receipt first.",
        "Never invent bank account numbers. Never ask for a transfer "
        "receipt before sharing pay-to details.",
        json.dumps(tools, ensure_ascii=False),
    ]
    if order:
        summary = (
            f"Current open order: {order['ref']} "
            f"total {order['total_kobo']} kobo status {order['status']}."
        )
        lines.append(summary)
    return "\n\n".join(lines)


def _history_messages(history: list[Turn]) -> list[dict]:
    return [{"role": t.role, "content": t.content} for t in history]


def observe(
    state: State,
    store: EchoStore,
) -> State:
    state.bump()
    recent = store.recent_messages(state.seller_id, state.buyer_id, limit=8)
    state.history = [
        Turn(
            role="user" if row.get("direction") == "in" else "assistant",
            content=str(row.get("text") or ""),
        )
        for row in recent
        if row.get("text")
    ]
    state.history.append(Turn(role="user", content=state.message.text or ""))
    return state


async def route(
    state: State,
    jev: JevClient,
    seller_language: str,
) -> State:
    state.bump()
    scores = await jev.ask(
        text=state.message.text or "",
        seller_default_language=seller_language,
        image_extraction=state.extraction,
    )
    state.intent = scores.intent
    state.language = scores.language if scores.language != "other" else seller_language
    state.route_scores = scores.model_dump()
    return state


async def sales_agent(
    state: State,
    provider: LLMProvider,
    catalog_tools: CatalogTools,
    order_tools: OrderTools,
    business_name: str | None = None,
) -> State:
    state.bump()
    tools = catalog_tools.schemas() + order_tools.schemas()
    system = _system_prompt(state.language, tools, state.order, business_name)
    messages = [{"role": "system", "content": system}] + _history_messages(state.history)

    allowed_prices: set[int] = set()
    allowed_accounts: set[str] = set()
    tool_call_count = 0

    while state.steps < _MAX_STEPS and tool_call_count < _MAX_TOOL_CALLS:
        state.bump()
        result = await provider.chat(messages, tools=tools)

        if result.tool_calls:
            tool_messages = []
            for call in result.tool_calls:
                tool_call_count += 1
                if tool_call_count > _MAX_TOOL_CALLS:
                    break
                try:
                    args = json.loads(call.arguments) if call.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                try:
                    output = _dispatch_tool(call.name, args, catalog_tools, order_tools)
                except Exception as exc:
                    output = {"error": str(exc)}
                state.tool_calls.append({"name": call.name, "arguments": args, "result": output})
                tool_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id or call.name,
                        "content": json.dumps(output, ensure_ascii=False),
                    }
                )
                if isinstance(output, list):
                    for item in output:
                        price = item.get("price_kobo")
                        if price is not None:
                            allowed_prices.add(int(price))
                elif isinstance(output, dict):
                    price = output.get("price_kobo")
                    if price is not None:
                        allowed_prices.add(int(price))
                    _collect_allowed_accounts(output, allowed_accounts)
            tool_call_payloads = [tc.model_dump() for tc in result.tool_calls]
            messages.append(
                {
                    "role": "assistant",
                    "content": result.text or "",
                    "tool_calls": tool_call_payloads,
                }
            )
            messages.extend(tool_messages)
            if tool_call_count >= _MAX_TOOL_CALLS:
                break
            continue

        try:
            state.reply = check_reply(
                result.text,
                language=state.language,
                allowed_prices_kobo=allowed_prices or None,
                allowed_account_numbers=allowed_accounts or None,
                verdict=state.verdict.get("verdict") if state.verdict else None,
            )
            return state
        except ReplyCheckError as exc:
            state.errors.append(str(exc))
            messages.append(
                {
                    "role": "user",
                    "content": f"Your last reply broke a rule: {exc}. Rewrite it safely.",
                }
            )
            if len(state.errors) >= 2:
                break
            continue

    state.reply = fallback_reply(state.language)
    return state


def _dispatch_tool(
    name: str, arguments: dict, catalog_tools: CatalogTools, order_tools: OrderTools
) -> object:
    if name in ("search_catalog", "get_product"):
        return catalog_tools.dispatch(name, arguments)
    return order_tools.dispatch(name, arguments)


def _collect_allowed_accounts(output: dict, allowed: set[str]) -> None:
    """Allowlist shop payout digits returned by payment tools."""
    direct = output.get("account_number")
    if isinstance(direct, str) and direct.strip():
        allowed.add("".join(ch for ch in direct if ch.isdigit()))
    nested = output.get("payment_details")
    if isinstance(nested, dict):
        nested_acct = nested.get("account_number")
        if isinstance(nested_acct, str) and nested_acct.strip():
            allowed.add("".join(ch for ch in nested_acct if ch.isdigit()))


def _product_from_tools(state: State) -> dict | None:
    """Pick the best catalog hit from this turn's tool results for a product card."""
    best: dict | None = None
    for call in state.tool_calls:
        result = call.get("result")
        rows: list[dict] = []
        if isinstance(result, list):
            rows = [r for r in result if isinstance(r, dict)]
        elif isinstance(result, dict) and result.get("price_kobo") is not None:
            rows = [result]
        for row in rows:
            if row.get("price_kobo") is None:
                continue
            image = str(row.get("image_path") or row.get("image_url") or "")
            candidate = {
                "id": row.get("id"),
                "name": row.get("name") or "Product",
                "price_kobo": int(row["price_kobo"]),
                "price_ngn": int(row["price_kobo"]) // 100,
                "image_url": image,
                "description": row.get("description") or "",
                "stock": row.get("stock"),
                "active": row.get("active", True),
            }
            if best is None or (image and not best.get("image_url")):
                best = candidate
    return best


def _needs_smart_approval(
    state: State,
    *,
    product: dict | None,
    smart_threshold_ngn: int,
) -> bool:
    text = (state.reply or "").lower()
    if any(word in text for word in ("discount", "refund", "owo pada", "slash price")):
        return True
    if state.intent in {"payment_proof", "complaint"}:
        return True
    if product and int(product.get("price_ngn") or 0) >= int(smart_threshold_ngn or 0):
        return True
    return False


async def respond(
    state: State,
    adapter: ChannelAdapter,
    sender_id: str,
    store: EchoStore,
    *,
    inbox_control: object | None = None,
    reply_mode: str = "auto",
    smart_threshold_ngn: int = 50_000,
) -> State:
    state.bump()
    if not (state.reply or "").strip():
        return state

    product = _product_from_tools(state)
    if product and product.get("active") is False:
        # Out of stock — keep text reply (sales_agent should already say so).
        product = None

    mode = (reply_mode or "auto").lower()
    if inbox_control is not None:
        ctrl = inbox_control.get_control(state.seller_id, state.buyer_id)
        if ctrl.paused:
            # Seller took over — do not send AI replies.
            return state
        if ctrl.reply_mode:
            mode = ctrl.reply_mode.lower()

    needs_approval = mode == "approve" or (
        mode == "smart"
        and _needs_smart_approval(state, product=product, smart_threshold_ngn=smart_threshold_ngn)
    )

    if needs_approval and inbox_control is not None:
        inbox_control.create_reply_draft(
            seller_id=state.seller_id,
            buyer_id=state.buyer_id,
            buyer_external_id=sender_id,
            channel=state.channel,
            customer_text=state.message.text or "",
            draft_text=state.reply,
            mode=mode,
            product=product,
        )
        # Persist a local draft bubble so the dashboard thread shows it immediately.
        store.save_outbound(
            seller_id=state.seller_id,
            buyer_id=state.buyer_id,
            channel=state.channel,
            external_msg_id=f"draft-{state.trace_id}",
            text=state.reply,
            message_type="draft",
            media_path=(product or {}).get("image_url") or None,
            meta={"status": "pending", "mode": mode, "product": product},
        )
        return state

    meta = {"mode": mode}
    if product:
        meta["product"] = product

    # Prefer photo + caption when catalog returned an image URL (http/https).
    image_url = (product or {}).get("image_url") or ""
    sent_image = False
    if image_url.startswith("http://") or image_url.startswith("https://"):
        send_image = getattr(adapter, "send_image", None)
        if callable(send_image):
            try:
                await send_image(sender_id, image_url, state.reply)
                sent_image = True
            except Exception:
                sent_image = False

    if not sent_image:
        await adapter.send_text(sender_id, state.reply)

    store.save_outbound(
        seller_id=state.seller_id,
        buyer_id=state.buyer_id,
        channel=state.channel,
        external_msg_id=f"out-{state.trace_id}",
        text=state.reply,
        message_type="product" if product else "text",
        media_path=image_url or None,
        meta=meta,
    )
    return state

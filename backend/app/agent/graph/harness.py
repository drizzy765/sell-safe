"""Top-level harness: one inbound turn -> outbound reply."""

from app.agent.graph.nodes import observe, respond, route, sales_agent
from app.agent.graph.seller_cmd import seller_command_agent
from app.agent.graph.state import State
from app.agent.graph.verify import verify_payment_turn
from app.agent.official_page import (
    connect_reply_for_settings,
    is_official_ig_account,
    official_ids_from_settings,
)
from app.agent.tools.catalog import CatalogTools
from app.agent.tools.orders import OrderTools
from app.channels.base import ChannelAdapter, InboundMessage
from app.db.catalog_store import CatalogStore
from app.db.echo_store import EchoStore
from app.db.fraud_store import FraudStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore
from app.decisions.base import JevClient
from app.llm.base import LLMProvider

_PAYMENT_DETAILS_PHRASES = (
    "account number",
    "acct number",
    "account details",
    "bank details",
    "payment details",
    "your account",
    "business account",
    "send account",
    "how do i pay",
    "how can i pay",
    "how to pay",
    "how i go pay",
    "how do i make payment",
    "where do i pay",
    "where should i pay",
    "nomba account",
)

_PAYMENT_DETAILS_MISSING = {
    "en": ("The seller has not added their bank details yet. Please hold on while they add them."),
    "pcm": ("Seller never add bank details yet. Abeg hold on small make dem add am."),
    "yo": "Olùtajà kò tí fi ẹ̀kúnrẹ́rẹ́ báńkì wọn síbẹ̀. Ẹ jọ̀wọ́ dúró díẹ̀ kí wọ́n fi síbẹ̀.",
}


_CATALOG_BROWSE_PHRASES = (
    "wetin dey your catalog",
    "wetin dey catalog",
    "wetin you get",
    "wetin you dey sell",
    "wetin dey shop",
    "what do you have",
    "what do you sell",
    "what is in your catalog",
    "what's in your catalog",
    "show me your products",
    "show me your catalog",
    "send picture",
    "send pictures",
    "your catalog",
    "your products",
    "list your products",
    "i wan buy something",
    "i want to buy something",
)

_CATALOG_EMPTY = {
    "en": "We don't have any products listed yet. Please check back soon.",
    "pcm": "We never add any product yet. Abeg check back small time.",
    "yo": "A kò tí fi ọja kankan síbẹ̀. Ẹ jọ̀wọ́ padà wá díẹ̀ lẹ́yìn.",
}


def is_catalog_browse_request(text: str) -> bool:
    """True when a buyer asks what the shop sells (deterministic, no LLM)."""
    normalized = " ".join((text or "").lower().split())
    if not normalized or normalized.startswith("/"):
        return False
    return any(phrase in normalized for phrase in _CATALOG_BROWSE_PHRASES)


def _format_price(price_kobo: object) -> str:
    try:
        kobo = int(price_kobo or 0)
    except (TypeError, ValueError):
        return ""
    naira = kobo / 100
    return f"₦{naira:,.0f}" if naira == int(naira) else f"₦{naira:,.2f}"


def _catalog_browse_reply(products: list[dict], language: str) -> str:
    if not products:
        return _CATALOG_EMPTY.get(language, _CATALOG_EMPTY["en"])
    lines = []
    for product in products[:5]:
        name = str(product.get("name") or "Product")
        price = _format_price(product.get("price_kobo"))
        lines.append(f"• {name} — {price}" if price else f"• {name}")
    if language == "pcm":
        return "Na wetin we get be this:\n" + "\n".join(lines) + "\nTell me which one you want."
    if language == "yo":
        return "Èyí ni ohun tí a ní:\n" + "\n".join(lines) + "\nSọ èyí tí o fẹ́ fún mi."
    return "Here's what we have:\n" + "\n".join(lines) + "\nTell me which one you want."


def is_payment_details_request(text: str) -> bool:
    """True when a buyer is asking how/where to pay (deterministic, no LLM)."""
    normalized = " ".join((text or "").lower().split())
    if not normalized or normalized.startswith("/"):
        return False
    return any(phrase in normalized for phrase in _PAYMENT_DETAILS_PHRASES)


async def run_turn(
    message: InboundMessage,
    *,
    seller_id: str,
    buyer_id: str,
    channel_adapter: ChannelAdapter,
    store: EchoStore,
    jev: JevClient,
    provider: LLMProvider,
    catalog_store: CatalogStore,
    order_store: OrderStore,
    payment_store: PaymentStore | None = None,
    fraud_store: FraudStore | None = None,
    pii_salt: str = "",
    business_name: str | None = None,
    inbox_control: object | None = None,
    reply_mode: str = "auto",
    smart_threshold_ngn: int = 50_000,
    settings: object | None = None,
    shop_store: object | None = None,
) -> State:
    """Run one inbound turn through the agent graph."""
    state = State(
        trace_id=f"{message.external_id}-{seller_id}",
        channel=message.channel,
        seller_id=seller_id,
        buyer_id=buyer_id,
        buyer_external_id=message.sender_id,
        message=message,
    )

    if inbox_control is not None:
        ctrl = inbox_control.get_control(seller_id, buyer_id)
        if ctrl.paused:
            # Seller is handling this chat manually.
            return state

    # Official Sell-Safe IG: connect/marketing only — never catalog or payments.
    if (
        message.channel == "instagram"
        and settings is not None
        and is_official_ig_account(seller_id, official_ids=official_ids_from_settings(settings))
    ):
        state.intent = "official_connect"
        state.language = "en"
        state.reply = connect_reply_for_settings(settings)
        state = await respond(
            state,
            channel_adapter,
            message.sender_id,
            store,
            inbox_control=inbox_control,
            reply_mode="auto",
            smart_threshold_ngn=smart_threshold_ngn,
        )
        return state

    state = observe(state, store)
    seller_language = store.get_seller_language(seller_id)
    state = await route(state, jev, seller_language)

    catalog_tools = CatalogTools(seller_id, catalog_store)
    seller = store.get_seller(seller_id) or {}
    bank_name = ""
    account_name = ""
    account_number = ""
    shop = _resolve_shop(shop_store, store, seller_id, seller)
    if shop is not None:
        bank_name = str(getattr(shop, "bank_name", "") or "")
        account_name = str(getattr(shop, "account_name", "") or "")
        account_number = str(getattr(shop, "account_number", "") or "")
        if not business_name:
            business_name = str(getattr(shop, "name", "") or "") or None
    order_tools = OrderTools(
        seller_id,
        buyer_id,
        order_store,
        crypto_wallet=str(seller.get("crypto_wallet") or ""),
        crypto_network=str(seller.get("crypto_network") or "base-sepolia"),
        bank_name=bank_name,
        account_name=account_name,
        account_number=account_number,
    )

    if state.intent != "payment_proof" and is_payment_details_request(message.text or ""):
        # Deterministic: Jev/LLM must not gate payment details. Buyers asking
        # for the account number get the saved payout (or a clear not-set reply).
        state.intent = "payment_details"
        payout = order_tools.payment_details()
        state.tool_calls.append({"name": "get_payment_details", "arguments": {}, "result": payout})
        if payout.get("configured"):
            state.reply = str(payout.get("message") or "")
        else:
            state.reply = _PAYMENT_DETAILS_MISSING.get(
                state.language, _PAYMENT_DETAILS_MISSING["en"]
            )
    elif is_catalog_browse_request(message.text or ""):
        # Deterministic: browsing asks get the real catalog list with prices,
        # never an LLM guess or a generic fallback (pidgin asks included).
        state.intent = "catalog_browse"
        products = catalog_tools.search_catalog(query="", max_results=5)
        state.tool_calls.append(
            {"name": "search_catalog", "arguments": {"query": ""}, "result": products}
        )
        state.reply = _catalog_browse_reply(products, state.language)
    elif state.intent in ("price_question", "order", "chit_chat"):
        state = await sales_agent(state, provider, catalog_tools, order_tools, business_name)
    elif state.intent == "payment_proof":
        if payment_store is None:
            state.reply = fallback_for_language(state.language, "payment_check")
        else:
            verify_result = await verify_payment_turn(
                message,
                seller_id=seller_id,
                buyer_id=buyer_id,
                channel_adapter=channel_adapter,
                store=store,
                order_store=order_store,
                payment_store=payment_store,
                provider=provider,
                jev=jev,
                pii_salt=pii_salt,
                fraud_store=fraud_store,
            )
            state.reply = verify_result.verdict.verdict
            state.verdict = verify_result.verdict.model_dump()
    elif state.intent == "complaint":
        state.reply = fallback_for_language(state.language, "escalate")
    elif state.intent == "seller_command":
        if payment_store is None:
            state.reply = fallback_for_language(state.language, "seller_command")
        else:
            state.reply = await seller_command_agent(
                message.text or "",
                seller_id=seller_id,
                buyer_id=buyer_id,
                sender_id=message.sender_id,
                channel_adapter=channel_adapter,
                store=store,
                order_store=order_store,
                payment_store=payment_store,
                fraud_store=fraud_store,
                pii_salt=pii_salt,
            )
    elif state.intent == "order_status":
        state.reply = fallback_for_language(state.language, "order_status")
    else:
        state.reply = fallback_for_language(state.language, "unknown")

    state = await respond(
        state,
        channel_adapter,
        message.sender_id,
        store,
        inbox_control=inbox_control,
        reply_mode=reply_mode,
        smart_threshold_ngn=smart_threshold_ngn,
    )
    return state


def _resolve_shop(
    shop_store: object | None,
    store: EchoStore,
    seller_id: str,
    seller: dict,
) -> object | None:
    """Find the connected shop profile for payout details."""
    if shop_store is None:
        return None
    shop_id = str(seller.get("shop_id") or "").strip()
    if shop_id and hasattr(shop_store, "get"):
        found = shop_store.get(shop_id)
        if found is not None:
            return found
    if hasattr(shop_store, "get_by_ig_account"):
        found = shop_store.get_by_ig_account(seller_id)
        if found is not None:
            return found
        # Seller row may be the IG-scoped id while shop is keyed by user_id (or vice versa).
        for key, value in (seller.get("channel_ids") or {}).items():
            if str(key).startswith("instagram") or key == "instagram":
                alt = shop_store.get_by_ig_account(str(value))
                if alt is not None:
                    return alt
    return None


def fallback_for_language(language: str, kind: str) -> str:
    maps = {
        "en": {
            "payment_check": "I will check this payment and get back to you.",
            "escalate": "I have passed this to the seller.",
            "seller_command": "Seller commands are not available yet.",
            "order_status": "Please send the order reference to check status.",
            "unknown": "I'm not sure I understand. Can you rephrase?",
        },
        "pcm": {
            "payment_check": "I go check this payment come back.",
            "escalate": "I don send am to the seller.",
            "seller_command": "Seller command no dey yet.",
            "order_status": "Send the order ref make I check am.",
            "unknown": "I no too understand. Abeg talk am again.",
        },
        "yo": {
            "payment_check": "N ṣe ayẹ̀wò owo yìí, n óò padà.",
            "escalate": "Mo ti fi ránṣẹ́ sí onísò.",
            "seller_command": "Àṣẹ onísò kò sí láàárín.",
            "order_status": "Jọ̀wọ́ ránṣẹ́ nọ́mba àṣẹ láti ṣe ayẹ̀wò rẹ̀.",
            "unknown": "N ko gbọ́ dáadáa. Ṣé o lè sọ rẹ̀ padà?",
        },
    }
    return maps.get(language, maps["en"]).get(kind, maps["en"]["unknown"])

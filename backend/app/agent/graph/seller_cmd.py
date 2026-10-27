"""Seller command branch: /release, /reject, /fake, /notfake."""

from __future__ import annotations

from typing import Any

from app.agent.templates import order_cancelled, order_released
from app.channels.base import ChannelAdapter
from app.db.echo_store import EchoStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore


async def seller_command_agent(
    message_text: str,
    *,
    seller_id: str,
    buyer_id: str,
    sender_id: str,
    channel_adapter: ChannelAdapter,
    store: EchoStore,
    order_store: OrderStore,
    payment_store: PaymentStore,
) -> str:
    """Handle a seller command message and return a reply text."""
    parts = message_text.strip().split()
    if len(parts) < 2:
        return "Use: /release SS-XXXX, /reject SS-XXXX, /fake SS-XXXX, or /notfake SS-XXXX"

    command = parts[0].lower()
    ref = parts[1]

    order = order_store.get_order_by_ref(ref)
    if order is None:
        return f"Order {ref} not found."

    if command == "/release":
        return await _release_order(
            order,
            seller_id=seller_id,
            buyer_id=buyer_id,
            sender_id=sender_id,
            channel_adapter=channel_adapter,
            store=store,
            order_store=order_store,
            payment_store=payment_store,
        )

    if command == "/reject":
        return await _reject_order(
            order,
            seller_id=seller_id,
            buyer_id=buyer_id,
            sender_id=sender_id,
            channel_adapter=channel_adapter,
            store=store,
            order_store=order_store,
            payment_store=payment_store,
        )

    if command in ("/fake", "/notfake"):
        return "Fraud memory commands are coming in the next phase."

    return "Unknown command. Use /release, /reject, /fake, or /notfake."


async def _release_order(
    order: dict[str, Any],
    *,
    seller_id: str,
    buyer_id: str,
    sender_id: str,
    channel_adapter: ChannelAdapter,
    store: EchoStore,
    order_store: OrderStore,
    payment_store: PaymentStore,
) -> str:
    payment = payment_store.get_payment_for_order(order["id"])
    verdict = (payment or {}).get("verdict") if payment else None
    if not verdict:
        latest = payment_store.get_latest_verdict(payment["id"]) if payment else None
        verdict = latest

    if not verdict or verdict.get("verdict") != "CONFIRMED":
        return f"Order {order['ref']} cannot be released: no confirmed payment."

    if not verdict.get("release_allowed"):
        payment_store.save_verdict(
            payment_id=payment["id"],
            verdict="CONFIRMED",
            confidence=verdict.get("confidence", 0.0),
            release_allowed=True,
            reasons=verdict.get("reasons", []),
            rule_hits=verdict.get("rule_hits", []),
            jev_scores=verdict.get("jev_scores"),
            decided_by="seller",
        )

    order_store.update_order_status(order["ref"], "released")
    text = order_released(order["ref"])
    await channel_adapter.send_text(sender_id, text)
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id=f"out-release-{seller_id}-{buyer_id}",
        text=text,
    )
    return text


async def _reject_order(
    order: dict[str, Any],
    *,
    seller_id: str,
    buyer_id: str,
    sender_id: str,
    channel_adapter: ChannelAdapter,
    store: EchoStore,
    order_store: OrderStore,
    payment_store: PaymentStore,
) -> str:
    payment = payment_store.get_payment_for_order(order["id"])
    if payment:
        payment_store.save_verdict(
            payment_id=payment["id"],
            verdict="SUSPICIOUS",
            confidence=0.0,
            release_allowed=False,
            reasons=["seller_rejected"],
            rule_hits=[],
            decided_by="seller",
        )

    order_store.update_order_status(order["ref"], "cancelled")
    text = order_cancelled(order["ref"])
    await channel_adapter.send_text(sender_id, text)
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id=f"out-reject-{seller_id}-{buyer_id}",
        text=text,
    )
    return text

"""Buyer pasted a transaction hash in chat."""

import re
from datetime import UTC, datetime

from app.agent.templates import crypto_result
from app.channels.base import ChannelAdapter
from app.db.echo_store import EchoStore
from app.db.orders import OrderStore
from app.payments.crypto.checkout import crypto_checkout, expected_usdc_base
from app.payments.crypto.rpc import CryptoRpc
from app.payments.crypto.service import verify_tx
from app.payments.crypto.store import CryptoPaymentStore

_TX_HASH = re.compile(r"0x[a-fA-F0-9]{64}")

_REASON_TEXT = {
    "screenshot_only": "Only a screenshot was sent, and a screenshot cannot confirm USDC",
    "reused_hash": "This transaction hash was already used",
    "missing_tx": "No transaction was found for that hash",
    "wrong_network": "The transaction is not on the configured network",
    "failed_tx": "The transaction failed",
    "wrong_token": "The transfer is not the configured USDC contract",
    "wrong_address": "The USDC did not go to the seller wallet",
    "amount_too_small": "The USDC amount is below the order",
    "tx_before_order": "The transaction is older than the order",
    "pending_confirmations": "Waiting for more confirmations",
    "amount_not_set": "This order has no USDC amount",
    "rpc_not_configured": "On-chain checks are not configured",
}


def extract_tx_hash(text: str) -> str | None:
    match = _TX_HASH.search(text or "")
    if match is None:
        return None
    return match.group(0)


def order_created_at(order: dict) -> datetime:
    raw = order.get("created_at")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=UTC)
    if not raw:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(str(raw))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def checkout_for_order(order: dict, *, wallet: str, network: str) -> str | None:
    amount = expected_usdc_base(order)
    if amount is None or not wallet:
        return None
    return crypto_checkout(wallet=wallet, usdc_base=amount, ref=str(order["ref"]), network=network)


async def handle_crypto_hash(
    *,
    text: str,
    seller_id: str,
    buyer_id: str,
    sender_id: str,
    adapter: ChannelAdapter,
    store: EchoStore,
    orders: OrderStore,
    payments: CryptoPaymentStore,
    rpc_url: str,
    token_contract: str,
    chain_id: int,
    network: str,
    min_confirmations: int,
    transport: object | None = None,
) -> str:
    """Verify a pasted hash and reply. Screenshot-only claims stay suspicious."""
    seller = store.get_seller(seller_id) or {}
    wallet = str(seller.get("crypto_wallet") or "")
    order = orders.get_open_order(seller_id, buyer_id)
    tx_hash = extract_tx_hash(text)
    if order is None or not wallet or tx_hash is None:
        reply = crypto_result("SUSPICIOUS", "unknown", "No open order, wallet, or transaction hash")
        await adapter.send_text(sender_id, reply)
        return reply
    rpc = CryptoRpc(rpc_url, transport) if rpc_url else None
    result = await verify_tx(
        tx_hash=tx_hash,
        order=order,
        seller_wallet=wallet,
        token_contract=token_contract,
        min_confirmations=min_confirmations,
        chain_id=chain_id,
        network=network,
        rpc=rpc,
        store=payments,
        order_created_at=order_created_at(order),
        screenshot_only=False,
    )
    reason = _REASON_TEXT.get(result.reason or "", result.reason)
    reply = crypto_result(result.status, str(order["ref"]), reason)
    await adapter.send_text(sender_id, reply)
    return reply


def crypto_instructions_for_items(
    items: list[dict],
    *,
    wallet: str,
    network: str,
    ref: str,
) -> tuple[int | None, str | None]:
    if not wallet or any("unit_usdc_base" not in item for item in items):
        return None, None
    total = sum(int(item["qty"]) * int(item["unit_usdc_base"]) for item in items)
    return total, crypto_checkout(wallet=wallet, usdc_base=total, ref=ref, network=network)

"""On-chain USDC checks. The model does not decide these outcomes.

CONFIRMED matches a level-4 Paystack match: release is allowed.
PENDING matches NOT FOUND: goods stay, and a later check can confirm.
SUSPICIOUS matches a failed Paystack or bank-alert check: do not release.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.payments.crypto.address import require_checksum_address, to_checksum_address

USDC_DECIMALS = 6
USDC_BASE = 10**USDC_DECIMALS
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


class Transfer(BaseModel):
    token: str
    sender: str
    recipient: str
    amount: int


class ChainView(BaseModel):
    """Facts read from JSON-RPC. Tests build this without calling a node."""

    receipt_found: bool = False
    status_success: bool = False
    block_number: int | None = None
    block_timestamp: datetime | None = None
    latest_block: int | None = None
    chain_id: int | None = None
    transfers: list[Transfer] = []


class CryptoCheck(BaseModel):
    status: str
    reason: str | None = None
    release_allowed: bool = False
    amount: int | None = None
    confirmations: int | None = None
    sender: str | None = None
    recipient: str | None = None

    def verdict_name(self) -> str:
        """Map onto the existing verdict enum. PENDING stays NOT FOUND."""
        if self.status == "CONFIRMED":
            return "CONFIRMED"
        if self.status == "PENDING":
            return "NOT_FOUND"
        return "SUSPICIOUS"


def _same(left: str, right: str) -> bool:
    return require_checksum_address(left) == require_checksum_address(right)


def _confirmations(view: ChainView) -> int | None:
    if view.latest_block is None or view.block_number is None:
        return None
    return view.latest_block - view.block_number + 1


def judge(
    view: ChainView,
    *,
    seller_wallet: str,
    token_contract: str,
    expected_amount: int,
    min_confirmations: int,
    order_created_at: datetime,
    expected_chain_id: int,
    already_used: bool = False,
    screenshot_only: bool = False,
) -> CryptoCheck:
    """Apply every crypto rule. The first failure wins."""
    if screenshot_only:
        return CryptoCheck(status="SUSPICIOUS", reason="screenshot_only")
    if already_used:
        return CryptoCheck(status="SUSPICIOUS", reason="reused_hash")
    if not view.receipt_found:
        return CryptoCheck(status="SUSPICIOUS", reason="missing_tx")
    if view.chain_id != expected_chain_id:
        return CryptoCheck(status="SUSPICIOUS", reason="wrong_network")
    if not view.status_success:
        return CryptoCheck(status="SUSPICIOUS", reason="failed_tx")

    token = require_checksum_address(token_contract)
    seller = require_checksum_address(seller_wallet)
    matching = [row for row in view.transfers if _same(row.token, token)]
    if not matching:
        return CryptoCheck(status="SUSPICIOUS", reason="wrong_token")
    to_seller = [row for row in matching if _same(row.recipient, seller)]
    if not to_seller:
        return CryptoCheck(status="SUSPICIOUS", reason="wrong_address")

    amount = sum(row.amount for row in to_seller)
    sender = to_seller[0].sender
    if amount < expected_amount:
        return CryptoCheck(
            status="SUSPICIOUS",
            reason="amount_too_small",
            amount=amount,
            sender=sender,
            recipient=seller,
        )
    if view.block_timestamp is None or view.block_timestamp < order_created_at:
        return CryptoCheck(
            status="SUSPICIOUS",
            reason="tx_before_order",
            amount=amount,
            sender=sender,
            recipient=seller,
        )

    confirmations = _confirmations(view)
    if confirmations is None or confirmations < min_confirmations:
        return CryptoCheck(
            status="PENDING",
            reason="pending_confirmations",
            release_allowed=False,
            amount=amount,
            confirmations=confirmations,
            sender=sender,
            recipient=seller,
        )
    return CryptoCheck(
        status="CONFIRMED",
        reason=None,
        release_allowed=True,
        amount=amount,
        confirmations=confirmations,
        sender=sender,
        recipient=seller,
    )


def decode_transfer_logs(logs: list[dict[str, Any]]) -> list[Transfer]:
    """Decode ERC-20 Transfer logs. Other events are ignored."""
    found: list[Transfer] = []
    for log in logs:
        topics = log.get("topics") or []
        if not topics or str(topics[0]).lower() != TRANSFER_TOPIC:
            continue
        if len(topics) < 3:
            continue
        data = str(log.get("data") or "0x0")
        found.append(
            Transfer(
                token=to_checksum_address(str(log.get("address"))),
                sender=_topic_address(str(topics[1])),
                recipient=_topic_address(str(topics[2])),
                amount=int(data, 16),
            )
        )
    return found


def _topic_address(topic: str) -> str:
    body = topic.lower().removeprefix("0x")
    return to_checksum_address("0x" + body[-40:])

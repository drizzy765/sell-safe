"""On-chain USDC rules. Each failure reason has its own case."""

from datetime import UTC, datetime, timedelta

from app.payments.crypto.address import AddressError, require_checksum_address, to_checksum_address
from app.payments.crypto.verify import ChainView, Transfer, decode_transfer_logs, judge

SELLER = "0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1"
BUYER = "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359"
USDC_CONTRACT = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
OTHER = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
ORDER_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
CHAIN_ID = 84532
AMOUNT = 15_000_000  # 15 USDC


def _view(**overrides: object) -> ChainView:
    base = ChainView(
        receipt_found=True,
        status_success=True,
        block_number=100,
        block_timestamp=ORDER_AT + timedelta(minutes=5),
        latest_block=110,
        chain_id=CHAIN_ID,
        transfers=[
            Transfer(token=USDC_CONTRACT, sender=BUYER, recipient=SELLER, amount=AMOUNT),
        ],
    )
    return base.model_copy(update=overrides)


def _judge(view: ChainView, **overrides: object):
    args = {
        "seller_wallet": SELLER,
        "token_contract": USDC_CONTRACT,
        "expected_amount": AMOUNT,
        "min_confirmations": 3,
        "order_created_at": ORDER_AT,
        "expected_chain_id": CHAIN_ID,
    }
    args.update(overrides)
    return judge(view, **args)


def test_checksum_address_accepts_eip55() -> None:
    assert require_checksum_address(SELLER) == SELLER


def test_checksum_address_rejects_lowercase() -> None:
    try:
        require_checksum_address(SELLER.lower())
        raise AssertionError("expected AddressError")
    except AddressError:
        pass


def test_confirmed_when_all_rules_pass() -> None:
    result = _judge(_view())
    assert result.status == "CONFIRMED"
    assert result.release_allowed is True
    assert result.amount == AMOUNT
    assert result.confirmations == 11
    assert result.verdict_name() == "CONFIRMED"


def test_pending_when_confirmations_short() -> None:
    result = _judge(_view(latest_block=101))
    assert result.status == "PENDING"
    assert result.release_allowed is False
    assert result.reason == "pending_confirmations"
    assert result.verdict_name() == "NOT_FOUND"


def test_suspicious_missing_tx() -> None:
    result = _judge(_view(receipt_found=False, transfers=[]))
    assert result.status == "SUSPICIOUS"
    assert result.reason == "missing_tx"


def test_suspicious_wrong_network() -> None:
    result = _judge(_view(chain_id=1))
    assert result.reason == "wrong_network"


def test_suspicious_failed_tx() -> None:
    result = _judge(_view(status_success=False))
    assert result.reason == "failed_tx"


def test_suspicious_wrong_token() -> None:
    transfers = [Transfer(token=OTHER, sender=BUYER, recipient=SELLER, amount=AMOUNT)]
    result = _judge(_view(transfers=transfers))
    assert result.reason == "wrong_token"


def test_suspicious_wrong_address() -> None:
    transfers = [Transfer(token=USDC_CONTRACT, sender=BUYER, recipient=OTHER, amount=AMOUNT)]
    result = _judge(_view(transfers=transfers))
    assert result.reason == "wrong_address"


def test_suspicious_amount_too_small() -> None:
    transfers = [Transfer(token=USDC_CONTRACT, sender=BUYER, recipient=SELLER, amount=AMOUNT - 1)]
    result = _judge(_view(transfers=transfers))
    assert result.reason == "amount_too_small"


def test_suspicious_tx_before_order() -> None:
    result = _judge(_view(block_timestamp=ORDER_AT - timedelta(minutes=1)))
    assert result.reason == "tx_before_order"


def test_suspicious_reused_hash() -> None:
    result = _judge(_view(), already_used=True)
    assert result.reason == "reused_hash"


def test_suspicious_screenshot_only() -> None:
    result = _judge(_view(), screenshot_only=True)
    assert result.reason == "screenshot_only"


def test_decode_transfer_logs_ignores_other_events() -> None:
    topic_from = "0x" + "0" * 24 + BUYER[2:].lower()
    topic_to = "0x" + "0" * 24 + SELLER[2:].lower()
    logs = [
        {
            "address": USDC_CONTRACT.lower(),
            "topics": [
                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
                topic_from,
                topic_to,
            ],
            "data": hex(AMOUNT),
        },
        {
            "address": USDC_CONTRACT.lower(),
            "topics": ["0x" + "11" * 32],
            "data": "0x1",
        },
    ]
    transfers = decode_transfer_logs(logs)
    assert len(transfers) == 1
    assert transfers[0].amount == AMOUNT
    assert transfers[0].recipient == to_checksum_address(SELLER)

"""tx_hash uniqueness for crypto_payments."""

from app.payments.crypto.store import MemoryCryptoStore


def test_same_hash_cannot_confirm_second_order() -> None:
    store = MemoryCryptoStore()
    first = store.save(
        {
            "order_id": "order-1",
            "tx_hash": "0x" + "ab" * 32,
            "network": "base-sepolia",
            "from_address": None,
            "to_address": None,
            "amount": 1_000_000,
            "confirmations": 3,
            "status": "CONFIRMED",
            "reason": None,
        }
    )
    second = store.save(
        {
            "order_id": "order-2",
            "tx_hash": "0x" + "AB" * 32,
            "network": "base-sepolia",
            "from_address": None,
            "to_address": None,
            "amount": 1_000_000,
            "confirmations": 3,
            "status": "CONFIRMED",
            "reason": None,
        }
    )
    assert first["order_id"] == "order-1"
    assert second["order_id"] == "order-1"
    assert len(store.rows) == 1


def test_pending_row_can_update_to_confirmed() -> None:
    store = MemoryCryptoStore()
    store.save(
        {
            "order_id": "order-1",
            "tx_hash": "0x" + "cd" * 32,
            "network": "base-sepolia",
            "from_address": None,
            "to_address": None,
            "amount": 1_000_000,
            "confirmations": 1,
            "status": "PENDING",
            "reason": "pending_confirmations",
        }
    )
    updated = store.save(
        {
            "order_id": "order-1",
            "tx_hash": "0x" + "cd" * 32,
            "network": "base-sepolia",
            "from_address": "0x1",
            "to_address": "0x2",
            "amount": 1_000_000,
            "confirmations": 5,
            "status": "CONFIRMED",
            "reason": None,
        }
    )
    assert updated["status"] == "CONFIRMED"
    assert updated["confirmations"] == 5
    assert len(store.rows) == 1

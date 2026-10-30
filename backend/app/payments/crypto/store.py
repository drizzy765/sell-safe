"""crypto_payments rows. tx_hash is unique so a hash cannot pay two orders."""

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


class CryptoPaymentStore(Protocol):
    def get(self, tx_hash: str) -> dict | None: ...

    def save(self, row: dict) -> dict: ...


class MemoryCryptoStore:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def get(self, tx_hash: str) -> dict | None:
        key = tx_hash.lower()
        for row in self.rows:
            if str(row["tx_hash"]).lower() == key:
                return row
        return None

    def save(self, row: dict) -> dict:
        existing = self.get(str(row["tx_hash"]))
        if existing is None:
            stored = {
                "id": str(uuid4()),
                "checked_at": datetime.now(UTC).isoformat(),
                **row,
            }
            self.rows.append(stored)
            return stored
        if existing["order_id"] != row["order_id"] or existing["status"] == "CONFIRMED":
            return existing
        existing.update(row)
        existing["checked_at"] = datetime.now(UTC).isoformat()
        return existing

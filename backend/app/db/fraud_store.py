"""Fraud signal persistence. Raw PII is never stored — only salted hashes."""

from typing import Protocol
from uuid import uuid4


class FraudStore(Protocol):
    def insert_signal(
        self,
        *,
        kind: str,
        value_hash: str,
        reported_by_seller_id: str,
        evidence_id: str | None = None,
        severity: int = 2,
        confirmed: bool = True,
    ) -> dict: ...

    def set_confirmed_for_evidence(
        self,
        *,
        evidence_ids: list[str],
        confirmed: bool,
    ) -> int: ...

    def find_confirmed_by_hashes(self, value_hashes: list[str]) -> list[dict]: ...


class MemoryFraudStore:
    def __init__(self) -> None:
        self.signals: list[dict] = []

    def insert_signal(
        self,
        *,
        kind: str,
        value_hash: str,
        reported_by_seller_id: str,
        evidence_id: str | None = None,
        severity: int = 2,
        confirmed: bool = True,
    ) -> dict:
        row = {
            "id": str(uuid4()),
            "kind": kind,
            "value_hash": value_hash,
            "reported_by_seller_id": reported_by_seller_id,
            "evidence_id": evidence_id,
            "severity": severity,
            "confirmed": confirmed,
        }
        self.signals.append(row)
        return row

    def set_confirmed_for_evidence(
        self,
        *,
        evidence_ids: list[str],
        confirmed: bool,
    ) -> int:
        ids = set(evidence_ids)
        count = 0
        for signal in self.signals:
            if signal.get("evidence_id") in ids:
                signal["confirmed"] = confirmed
                count += 1
        return count

    def find_confirmed_by_hashes(self, value_hashes: list[str]) -> list[dict]:
        wanted = set(value_hashes)
        return [s for s in self.signals if s.get("confirmed") and s.get("value_hash") in wanted]


class SupabaseFraudStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def insert_signal(
        self,
        *,
        kind: str,
        value_hash: str,
        reported_by_seller_id: str,
        evidence_id: str | None = None,
        severity: int = 2,
        confirmed: bool = True,
    ) -> dict:
        payload: dict = {
            "kind": kind,
            "value_hash": value_hash,
            "reported_by_seller_id": reported_by_seller_id,
            "severity": severity,
            "confirmed": confirmed,
        }
        if evidence_id is not None:
            payload["evidence_id"] = evidence_id
        created = self._client.table("fraud_signals").insert(payload).execute()
        return created.data[0]

    def set_confirmed_for_evidence(
        self,
        *,
        evidence_ids: list[str],
        confirmed: bool,
    ) -> int:
        if not evidence_ids:
            return 0
        updated = (
            self._client.table("fraud_signals")
            .update({"confirmed": confirmed})
            .in_("evidence_id", evidence_ids)
            .execute()
        )
        return len(updated.data or [])

    def find_confirmed_by_hashes(self, value_hashes: list[str]) -> list[dict]:
        if not value_hashes:
            return []
        found = (
            self._client.table("fraud_signals")
            .select("*")
            .eq("confirmed", True)
            .in_("value_hash", value_hashes)
            .execute()
        )
        return found.data or []


def build_fraud_store(settings: object) -> SupabaseFraudStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabaseFraudStore(create_client(url, key))

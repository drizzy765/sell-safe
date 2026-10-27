"""Payments and payment_evidence persistence."""

from typing import Protocol
from uuid import uuid4


class PaymentStore(Protocol):
    def get_or_create_payment(
        self,
        *,
        order_id: str,
        method: str,
        expected_kobo: int,
    ) -> dict: ...

    def insert_evidence(
        self,
        *,
        payment_id: str,
        evidence_type: str,
        source_id: str,
        extracted: dict,
        trust_level: int,
        raw_path: str | None = None,
        image_sha256: str | None = None,
        image_phash: str | None = None,
    ) -> dict: ...

    def get_evidence_for_order(self, order_id: str) -> list[dict]: ...

    def get_payment_for_order(self, order_id: str) -> dict | None: ...


class MemoryPaymentStore:
    def __init__(self) -> None:
        self.payments: list[dict] = []
        self.evidence: list[dict] = []

    def get_or_create_payment(
        self,
        *,
        order_id: str,
        method: str,
        expected_kobo: int,
    ) -> dict:
        for payment in self.payments:
            if payment["order_id"] == order_id:
                return payment
        payment = {
            "id": str(uuid4()),
            "order_id": order_id,
            "method": method,
            "expected_kobo": expected_kobo,
            "status": "pending",
        }
        self.payments.append(payment)
        return payment

    def insert_evidence(
        self,
        *,
        payment_id: str,
        evidence_type: str,
        source_id: str,
        extracted: dict,
        trust_level: int,
        raw_path: str | None = None,
        image_sha256: str | None = None,
        image_phash: str | None = None,
    ) -> dict:
        row = {
            "id": str(uuid4()),
            "payment_id": payment_id,
            "type": evidence_type,
            "source_id": source_id,
            "extracted": extracted,
            "trust_level": trust_level,
            "raw_path": raw_path,
            "image_sha256": image_sha256,
            "image_phash": image_phash,
        }
        self.evidence.append(row)
        return row

    def get_evidence_for_order(self, order_id: str) -> list[dict]:
        payment = self.get_payment_for_order(order_id)
        if payment is None:
            return []
        return [e for e in self.evidence if e["payment_id"] == payment["id"]]

    def get_payment_for_order(self, order_id: str) -> dict | None:
        for payment in self.payments:
            if payment["order_id"] == order_id:
                return payment
        return None


class SupabasePaymentStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def get_or_create_payment(
        self,
        *,
        order_id: str,
        method: str,
        expected_kobo: int,
    ) -> dict:
        found = (
            self._client.table("payments")
            .select("id, order_id, method, expected_kobo, status")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        if rows:
            return rows[0]
        created = (
            self._client.table("payments")
            .insert(
                {
                    "order_id": order_id,
                    "method": method,
                    "expected_kobo": expected_kobo,
                    "status": "pending",
                }
            )
            .execute()
        )
        return created.data[0]

    def insert_evidence(
        self,
        *,
        payment_id: str,
        evidence_type: str,
        source_id: str,
        extracted: dict,
        trust_level: int,
        raw_path: str | None = None,
        image_sha256: str | None = None,
        image_phash: str | None = None,
    ) -> dict:
        payload: dict = {
            "payment_id": payment_id,
            "type": evidence_type,
            "source_id": source_id,
            "extracted": extracted,
            "trust_level": trust_level,
        }
        if raw_path is not None:
            payload["raw_path"] = raw_path
        if image_sha256 is not None:
            payload["image_sha256"] = image_sha256
        if image_phash is not None:
            payload["image_phash"] = image_phash
        created = self._client.table("payment_evidence").insert(payload).execute()
        return created.data[0]

    def get_evidence_for_order(self, order_id: str) -> list[dict]:
        payment = self.get_payment_for_order(order_id)
        if payment is None:
            return []
        found = (
            self._client.table("payment_evidence")
            .select("*")
            .eq("payment_id", payment["id"])
            .execute()
        )
        return found.data or []

    def get_payment_for_order(self, order_id: str) -> dict | None:
        found = (
            self._client.table("payments").select("*").eq("order_id", order_id).limit(1).execute()
        )
        rows = found.data or []
        return rows[0] if rows else None


def build_payment_store(settings: object) -> SupabasePaymentStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabasePaymentStore(create_client(url, key))

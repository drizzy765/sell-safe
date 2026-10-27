"""Paystack webhook signature check and event handling."""

import hashlib
import hmac
from typing import Any

from app.db.payments import PaymentStore
from app.db.webhook_events import WebhookEventStore
from app.payments.paystack.dva import PaystackClient


def verify_paystack_signature(secret: str, raw_body: bytes, signature_header: str | None) -> bool:
    """Check HMAC-SHA512(secret, raw_body) against the x-paystack-signature header."""
    if not secret or not signature_header:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha512).hexdigest()
    if len(signature_header) != len(expected):
        return False
    return hmac.compare_digest(signature_header, expected)


def _extract_evidence(data: dict[str, Any]) -> dict[str, Any]:
    """Build payment_evidence.extracted from a Paystack transaction."""
    amount_kobo = int(data.get("amount") or 0)
    return {
        "is_transfer_receipt": True,
        "amount_kobo": amount_kobo,
        "currency": data.get("currency") or "NGN",
        "sender_name": data.get("customer", {}).get("first_name")
        or data.get("metadata", {}).get("sender_name"),
        "sender_bank": data.get("authorization", {}).get("bank"),
        "recipient_name": None,
        "recipient_acct_last4": None,
        "reference": data.get("reference"),
        "status_text": data.get("status"),
        "txn_time_iso": data.get("paid_at") or data.get("created_at"),
        "app_style": "paystack",
        "visual_anomalies": [],
    }


class PaystackWebhookHandler:
    """Process a verified Paystack webhook event."""

    def __init__(
        self,
        *,
        client: PaystackClient,
        payment_store: PaymentStore,
        event_store: WebhookEventStore,
    ) -> None:
        self._client = client
        self._payment_store = payment_store
        self._event_store = event_store

    async def handle(
        self,
        event_id: str,
        payload: dict[str, Any],
        *,
        order_id: str,
        expected_kobo: int,
    ) -> dict[str, Any] | None:
        """Verify transaction and insert level-4 evidence. Returns the evidence row or None."""
        if self._event_store.is_duplicate("paystack", event_id):
            return None

        data = payload.get("data") or {}
        transaction_id = data.get("id")
        if not transaction_id:
            return None

        verified = await self._client.verify_transaction(transaction_id)
        self._event_store.record("paystack", event_id, payload)

        payment = self._payment_store.get_or_create_payment(
            order_id=order_id,
            method="bank_transfer",
            expected_kobo=expected_kobo,
        )
        extracted = _extract_evidence(verified)
        return self._payment_store.insert_evidence(
            payment_id=payment["id"],
            evidence_type="va_webhook",
            source_id=str(event_id),
            extracted=extracted,
            trust_level=4,
        )

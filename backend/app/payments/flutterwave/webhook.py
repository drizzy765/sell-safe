"""Flutterwave webhook signature check and event handling.

Flutterwave webhooks include a `verif-hash` header that must match the secret
configured in the dashboard. The payload is trusted for level-4 evidence; we do
not re-fetch the transaction because the webhook already carries the confirmed
transaction details.
"""

from typing import Any

from app.db.payments import PaymentStore
from app.db.webhook_events import WebhookEventStore


def verify_flutterwave_hash(header: str | None, secret: str) -> bool:
    """Check the verif-hash header against the configured secret."""
    if not header or not secret:
        return False
    if len(header) != len(secret):
        return False
    # Use constant-time comparison to avoid timing leaks.
    result = 0
    for a, b in zip(header, secret):
        result |= ord(a) ^ ord(b)
    return result == 0


def _extract_evidence(data: dict[str, Any]) -> dict[str, Any]:
    """Build payment_evidence.extracted from a Flutterwave transaction."""
    amount_kobo = int(data.get("amount") or 0)
    return {
        "is_transfer_receipt": True,
        "amount_kobo": amount_kobo,
        "currency": data.get("currency") or "NGN",
        "sender_name": data.get("customer", {}).get("name")
        or data.get("customer", {}).get("full_name"),
        "sender_bank": data.get("bank") or data.get("authorization", {}).get("bank"),
        "recipient_name": None,
        "recipient_acct_last4": None,
        "reference": data.get("tx_ref") or data.get("reference"),
        "status_text": data.get("status"),
        "txn_time_iso": data.get("created_at") or data.get("paid_at"),
        "app_style": "flutterwave",
        "visual_anomalies": [],
    }


class FlutterwaveWebhookHandler:
    """Process a verified Flutterwave webhook event."""

    def __init__(
        self,
        *,
        payment_store: PaymentStore,
        event_store: WebhookEventStore,
    ) -> None:
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
        """Insert level-4 evidence from a trusted Flutterwave webhook."""
        if self._event_store.is_duplicate("flutterwave", event_id):
            return None

        data = payload.get("data") or {}
        self._event_store.record("flutterwave", event_id, payload)

        payment = self._payment_store.get_or_create_payment(
            order_id=order_id,
            method="bank_transfer",
            expected_kobo=expected_kobo,
        )
        extracted = _extract_evidence(data)
        return self._payment_store.insert_evidence(
            payment_id=payment["id"],
            evidence_type="va_webhook",
            source_id=str(event_id),
            extracted=extracted,
            trust_level=4,
        )

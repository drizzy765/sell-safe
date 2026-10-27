"""Tests for the payment recheck job and seller confirmation flow."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.db.storage import MemoryStorage
from app.db.webhook_events import MemoryWebhookEventStore
from app.decisions.fake import FakeJev
from app.main import create_app

WA_SECRET = "test-app-secret"
PAYSTACK_SECRET = "test-paystack-secret"


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        meta_app_secret=WA_SECRET,
        meta_verify_token="verify-me",
        whatsapp_access_token="test-token",
        whatsapp_phone_number_id="1234567890",
        graph_api_version="v21.0",
        paystack_secret_key=PAYSTACK_SECRET,
        internal_api_token="internal-token",
    )


def _store_with_order():
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("1234567890")
    buyer_id = store.ensure_buyer("whatsapp", "15550000001", "Ada")
    store.seller_details[seller_id]["business_name"] = "Tolu"
    store.seller_details[seller_id]["virtual_account"] = {"last4": "1234", "bank": "Test Bank"}

    orders = MemoryOrderStore()
    order = orders.create_order(
        seller_id=seller_id,
        buyer_id=buyer_id,
        items=[{"product_id": "p1", "qty": 1, "unit_price_kobo": 1_500_000}],
        total_kobo=1_500_000,
    )
    order["created_at"] = (datetime.now(tz=UTC) - timedelta(minutes=5)).isoformat()

    payments = MemoryPaymentStore()
    return store, orders, payments, order


def _build_app(store, orders, payments, jev=None, transport=None):
    app = create_app(
        _settings(),
        store=store,
        orders=orders,
        payments=payments,
        catalog=MemoryCatalogStore(),
        storage=MemoryStorage(),
        transport=transport,
        jev=jev
        or FakeJev(
            intent="payment_proof",
            language="en",
            evidence_match=1.0,
            receipt_tampered=0.0,
        ),
    )
    app.state.webhook_events = MemoryWebhookEventStore()
    return TestClient(app)


def _message_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_recheck_confirms_after_late_webhook() -> None:
    store, orders, payments, order = _store_with_order()

    # Manually insert a screenshot evidence with a NOT_FOUND verdict.
    payment = payments.get_or_create_payment(
        order_id=order["id"], method="bank_transfer", expected_kobo=1_500_000
    )
    payments.insert_evidence(
        payment_id=payment["id"],
        evidence_type="screenshot",
        source_id="screenshot-1",
        extracted={
            "is_transfer_receipt": True,
            "amount_kobo": 1_500_000,
            "currency": "NGN",
            "sender_name": "Ada",
            "sender_bank": "GTBank",
            "recipient_name": "Tolu",
            "recipient_acct_last4": "1234",
            "reference": "SS-1001",
            "status_text": "successful",
            "txn_time_iso": "2026-10-27T10:15:00Z",
            "app_style": "GTWorld",
            "visual_anomalies": [],
        },
        trust_level=1,
        image_sha256="sha1",
        image_phash="phash1",
    )
    payments.save_verdict(
        payment_id=payment["id"],
        verdict="NOT_FOUND",
        confidence=0.5,
        release_allowed=False,
        reasons=["clean_screenshot_no_matching_evidence"],
        rule_hits=[],
    )

    # Late Paystack webhook evidence.
    payments.insert_evidence(
        payment_id=payment["id"],
        evidence_type="va_webhook",
        source_id="evt-late",
        extracted={
            "is_transfer_receipt": True,
            "amount_kobo": 1_500_000,
            "currency": "NGN",
            "sender_name": "Ada",
            "sender_bank": "GTBank",
            "reference": "SS-1001",
            "status_text": "success",
            "txn_time_iso": "2026-10-27T10:15:00Z",
            "app_style": "paystack",
            "visual_anomalies": [],
        },
        trust_level=4,
    )

    client = _build_app(store, orders, payments, transport=_message_transport())
    response = client.post(
        "/jobs/recheck",
        headers={"x-internal-token": "internal-token"},
    )
    assert response.status_code == 200
    actions = response.json()["actions"]
    assert any(a["ref"] == order["ref"] and a["action"] == "confirmed_by_recheck" for a in actions)
    assert orders.get_order_by_ref(order["ref"])["status"] == "paid"


def test_mid_band_confirmed_requires_seller_release() -> None:
    store, orders, payments, order = _store_with_order()

    payment = payments.get_or_create_payment(
        order_id=order["id"], method="bank_transfer", expected_kobo=1_500_000
    )
    payments.save_verdict(
        payment_id=payment["id"],
        verdict="CONFIRMED",
        confidence=0.75,
        release_allowed=False,
        reasons=["mid_confidence_seller_confirmation"],
        rule_hits=[],
    )

    client = _build_app(store, orders, payments)

    # Direct release endpoint should work for mid-band verdicts.
    release = client.post(
        f"/orders/{order['ref']}/release",
        headers={"x-internal-token": "internal-token"},
    )
    assert release.status_code == 200
    assert orders.get_order_by_ref(order["ref"])["status"] == "released"


@pytest.mark.asyncio
async def test_seller_reject_command_cancels_order() -> None:
    store, orders, payments, order = _store_with_order()

    client = _build_app(store, orders, payments)

    # Simulate seller sending /reject via the WhatsApp webhook.
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "15550000001",
                                    "id": "wamid.reject",
                                    "type": "text",
                                    "text": {"body": f"/reject {order['ref']}"},
                                }
                            ],
                            "metadata": {"phone_number_id": "1234567890"},
                        }
                    }
                ]
            }
        ],
    }
    import hashlib
    import hmac
    import json

    raw = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(WA_SECRET.encode(), raw, hashlib.sha256).hexdigest()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})
        return httpx.Response(404)

    client = _build_app(
        store,
        orders,
        payments,
        transport=httpx.MockTransport(handler),
        jev=FakeJev(intent="seller_command", language="en"),
    )
    response = client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Hub-Signature-256": signature, "content-type": "application/json"},
    )
    assert response.status_code == 200
    assert orders.get_order_by_ref(order["ref"])["status"] == "cancelled"

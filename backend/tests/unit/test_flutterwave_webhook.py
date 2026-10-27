import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.db.webhook_events import MemoryWebhookEventStore
from app.decisions.fake import FakeJev
from app.main import create_app

SECRET = "test-flutterwave-secret"


def _payload(event_id: str = "evt-1", tx_ref: str = "SS-1001") -> dict:
    return {
        "event": "charge.completed",
        "data": {
            "id": 67890,
            "tx_ref": tx_ref,
            "amount": 15000,
            "currency": "NGN",
            "status": "successful",
            "created_at": "2026-10-27T10:15:00Z",
            "customer": {"name": "Ada"},
        },
    }


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        flutterwave_secret_key=SECRET,
        flutterwave_webhook_hash=SECRET,
    )


def test_header_mismatch_returns_401() -> None:
    app = create_app(_settings())
    client = TestClient(app)
    raw = json.dumps(_payload()).encode()
    response = client.post(
        "/webhooks/flutterwave",
        content=raw,
        headers={"verif-hash": "invalid", "content-type": "application/json"},
    )
    assert response.status_code == 401


def _store_with_seller() -> MemoryEchoStore:
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("1234567890")
    store.seller_details[seller_id]["business_name"] = "Tolu"
    store.seller_details[seller_id]["virtual_account"] = {"last4": "1234"}
    return store


@pytest.mark.asyncio
async def test_matching_event_confirms_through_verdict_engine() -> None:
    store = _store_with_seller()
    orders = MemoryOrderStore()
    orders.orders.append(
        {
            "id": "order-1",
            "seller_id": store.sellers["1234567890"],
            "buyer_id": "buyer-1",
            "ref": "SS-1001",
            "total_kobo": 1_500_000,
            "status": "awaiting_payment",
            "created_at": "2026-10-27T10:00:00Z",
        }
    )
    payments = MemoryPaymentStore()
    events = MemoryWebhookEventStore()

    app = create_app(
        _settings(),
        store=store,
        orders=orders,
        payments=payments,
        jev=FakeJev(
            intent="payment_proof",
            language="en",
            evidence_match=1.0,
            receipt_tampered=0.0,
        ),
    )
    app.state.webhook_events = events
    client = TestClient(app)

    raw = json.dumps(_payload()).encode()
    response = client.post(
        "/webhooks/flutterwave",
        content=raw,
        headers={"verif-hash": SECRET, "content-type": "application/json"},
    )
    assert response.status_code == 200
    assert len(payments.evidence) == 1
    assert payments.evidence[0]["trust_level"] == 4
    assert orders.orders[0]["status"] == "paid"


@pytest.mark.asyncio
async def test_duplicate_delivery_stored_once() -> None:
    store = _store_with_seller()
    orders = MemoryOrderStore()
    orders.orders.append(
        {
            "id": "order-1",
            "seller_id": store.sellers["1234567890"],
            "buyer_id": "buyer-1",
            "ref": "SS-1001",
            "total_kobo": 1_500_000,
            "status": "awaiting_payment",
            "created_at": "2026-10-27T10:00:00Z",
        }
    )
    payments = MemoryPaymentStore()
    events = MemoryWebhookEventStore()

    app = create_app(
        _settings(),
        store=store,
        orders=orders,
        payments=payments,
        jev=FakeJev(
            intent="payment_proof",
            language="en",
            evidence_match=1.0,
            receipt_tampered=0.0,
        ),
    )
    app.state.webhook_events = events
    client = TestClient(app)

    raw = json.dumps(_payload()).encode()
    headers = {"verif-hash": SECRET, "content-type": "application/json"}

    response = client.post("/webhooks/flutterwave", content=raw, headers=headers)
    assert response.status_code == 200
    assert len(payments.evidence) == 1

    response = client.post("/webhooks/flutterwave", content=raw, headers=headers)
    assert response.status_code == 200
    assert len(payments.evidence) == 1

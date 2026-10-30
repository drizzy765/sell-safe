import hashlib
import hmac
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.db.webhook_events import MemoryWebhookEventStore
from app.decisions.fake import FakeJev
from app.main import create_app

SECRET = "test-paystack-secret"


def _sign(raw: bytes) -> str:
    return hmac.new(SECRET.encode(), raw, hashlib.sha512).hexdigest()


def _payload(event_id: str = "evt-1", reference: str = "SS-1001") -> dict:
    return {
        "event": "charge.success",
        "data": {
            "id": 12345,
            "reference": reference,
            "amount": 1500000,
            "currency": "NGN",
            "status": "success",
            "paid_at": "2026-10-27T10:15:00Z",
            "customer": {"first_name": "Ada"},
            "authorization": {"bank": "GTBank"},
        },
    }


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        paystack_secret_key=SECRET,
    )


def _app(
    orders: MemoryOrderStore | None = None,
    payments: MemoryPaymentStore | None = None,
    events: MemoryWebhookEventStore | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
):
    orders = orders or MemoryOrderStore()
    payments = payments or MemoryPaymentStore()
    events = events or MemoryWebhookEventStore()
    app = create_app(
        _settings(),
        orders=orders,
        transport=transport,
    )
    app.state.payments = payments
    app.state.webhook_events = events
    app.state.jev = FakeJev(
        intent="payment_proof",
        language="en",
        evidence_match=1.0,
        receipt_tampered=0.0,
    )
    return app


def test_bad_signature_returns_401() -> None:
    app = _app()
    client = TestClient(app)
    raw = json.dumps(_payload()).encode()
    response = client.post(
        "/webhooks/paystack",
        content=raw,
        headers={"x-paystack-signature": "invalid"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_event_id_stores_one_evidence() -> None:
    orders = MemoryOrderStore()
    orders.orders.append(
        {
            "id": "order-1",
            "ref": "SS-1001",
            "total_kobo": 1_500_000,
            "status": "awaiting_payment",
        }
    )
    payments = MemoryPaymentStore()
    events = MemoryWebhookEventStore()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/transaction/verify/12345":
            return httpx.Response(
                200,
                json={
                    "status": True,
                    "data": {
                        "id": 12345,
                        "reference": "SS-1001",
                        "amount": 1500000,
                        "currency": "NGN",
                        "status": "success",
                        "paid_at": "2026-10-27T10:15:00Z",
                        "customer": {"first_name": "Ada"},
                        "authorization": {"bank": "GTBank"},
                    },
                },
            )
        return httpx.Response(404)

    app = _app(orders, payments, events, transport=httpx.MockTransport(handler))
    client = TestClient(app)
    raw = json.dumps(_payload()).encode()
    headers = {"x-paystack-signature": _sign(raw)}

    response = client.post("/webhooks/paystack", content=raw, headers=headers)
    assert response.status_code == 200
    assert len(payments.evidence) == 1

    response = client.post("/webhooks/paystack", content=raw, headers=headers)
    assert response.status_code == 200
    assert len(payments.evidence) == 1


@pytest.mark.asyncio
async def test_verify_transaction_failure_stores_no_evidence() -> None:
    orders = MemoryOrderStore()
    orders.orders.append(
        {
            "id": "order-1",
            "ref": "SS-1001",
            "total_kobo": 1_500_000,
            "status": "awaiting_payment",
        }
    )
    payments = MemoryPaymentStore()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"status": False, "message": "error"})

    app = _app(orders, payments, transport=httpx.MockTransport(handler))
    client = TestClient(app)
    raw = json.dumps(_payload()).encode()
    headers = {"x-paystack-signature": _sign(raw)}

    response = client.post("/webhooks/paystack", content=raw, headers=headers)
    assert response.status_code == 200
    assert len(payments.evidence) == 0

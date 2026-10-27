import hashlib
import hmac
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.db.storage import MemoryStorage
from app.db.webhook_events import MemoryWebhookEventStore
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider
from app.main import create_app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"
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


def _wa_sign(raw: bytes) -> str:
    digest = hmac.new(WA_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _paystack_sign(raw: bytes) -> str:
    return hmac.new(PAYSTACK_SECRET.encode(), raw, hashlib.sha512).hexdigest()


def _whatsapp_image_raw(name: str) -> bytes:
    image = (FIXTURES / "image.json").read_bytes()
    payload = json.loads(image)
    payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = f"wamid.{name}"
    return json.dumps(payload).encode()


def _paystack_payload(event_id: str = "evt-1", reference: str = "SS-1001") -> bytes:
    return json.dumps(
        {
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
    ).encode()


def _receipt_vision(amount_kobo: int = 1_500_000) -> dict:
    return {
        "is_transfer_receipt": True,
        "amount_kobo": amount_kobo,
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
    }


def _setup_order(store: MemoryEchoStore) -> MemoryOrderStore:
    seller_id = store.ensure_seller("1234567890")
    buyer_id = store.ensure_buyer("whatsapp", "15550000001")
    store.seller_details[seller_id]["business_name"] = "Tolu"
    store.seller_details[seller_id]["virtual_account"] = {"last4": "1234", "bank": "Test Bank"}
    orders = MemoryOrderStore()
    orders.orders.append(
        {
            "id": "order-1",
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "ref": "SS-1001",
            "total_kobo": 1_500_000,
            "status": "awaiting_payment",
            "created_at": "2026-10-27T10:00:00Z",
        }
    )
    return orders


def _build_app(
    store: MemoryEchoStore,
    orders: MemoryOrderStore,
    payments: MemoryPaymentStore,
    events: MemoryWebhookEventStore,
    provider: FakeProvider,
    transport: httpx.AsyncBaseTransport,
    storage: MemoryStorage | None = None,
) -> TestClient:
    app = create_app(
        _settings(),
        store=store,
        transport=transport,
        provider=provider,
        jev=FakeJev(
            intent="payment_proof",
            language="en",
            evidence_match=1.0,
            receipt_tampered=0.0,
        ),
        catalog=MemoryCatalogStore(),
        orders=orders,
        payments=payments,
        storage=storage or MemoryStorage(),
    )
    app.state.webhook_events = events
    return TestClient(app)


def test_screenshot_first_then_webhook_confirms_and_allows_release() -> None:
    store = MemoryEchoStore()
    orders = _setup_order(store)
    payments = MemoryPaymentStore()
    events = MemoryWebhookEventStore()
    provider = FakeProvider(vision=_receipt_vision())

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/media-image-1"):
            return httpx.Response(200, json={"url": "https://cdn.example/obj"})
        if request.method == "GET" and request.url.host == "cdn.example":
            return httpx.Response(200, content=b"jpeg-bytes")
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
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})
        return httpx.Response(404)

    client = _build_app(store, orders, payments, events, provider, httpx.MockTransport(handler))

    raw = _whatsapp_image_raw("receipt")
    response = client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Hub-Signature-256": _wa_sign(raw), "content-type": "application/json"},
    )
    assert response.status_code == 200
    assert len(payments.evidence) == 1
    assert orders.orders[0]["status"] == "awaiting_payment"

    webhook_raw = _paystack_payload()
    response = client.post(
        "/webhooks/paystack",
        content=webhook_raw,
        headers={
            "x-paystack-signature": _paystack_sign(webhook_raw),
            "content-type": "application/json",
        },
    )
    assert response.status_code == 200
    assert orders.orders[0]["status"] == "paid"

    release = client.post(
        "/orders/SS-1001/release",
        headers={"x-internal-token": "internal-token"},
    )
    assert release.status_code == 200
    assert orders.orders[0]["status"] == "released"


def test_webhook_first_then_screenshot_confirms() -> None:
    store = MemoryEchoStore()
    orders = _setup_order(store)
    payments = MemoryPaymentStore()
    events = MemoryWebhookEventStore()
    provider = FakeProvider(vision=_receipt_vision())

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/media-image-1"):
            return httpx.Response(200, json={"url": "https://cdn.example/obj"})
        if request.method == "GET" and request.url.host == "cdn.example":
            return httpx.Response(200, content=b"jpeg-bytes")
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
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})
        return httpx.Response(404)

    client = _build_app(store, orders, payments, events, provider, httpx.MockTransport(handler))

    webhook_raw = _paystack_payload()
    response = client.post(
        "/webhooks/paystack",
        content=webhook_raw,
        headers={
            "x-paystack-signature": _paystack_sign(webhook_raw),
            "content-type": "application/json",
        },
    )
    assert response.status_code == 200
    assert orders.orders[0]["status"] == "paid"

    raw = _whatsapp_image_raw("receipt")
    response = client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Hub-Signature-256": _wa_sign(raw), "content-type": "application/json"},
    )
    assert response.status_code == 200


def test_edited_amount_blocks_release_with_409() -> None:
    store = MemoryEchoStore()
    orders = _setup_order(store)
    payments = MemoryPaymentStore()
    events = MemoryWebhookEventStore()
    provider = FakeProvider(vision=_receipt_vision(amount_kobo=1_000_000))

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/media-image-1"):
            return httpx.Response(200, json={"url": "https://cdn.example/obj"})
        if request.method == "GET":
            return httpx.Response(200, content=b"jpeg-bytes")
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})
        return httpx.Response(404)

    client = _build_app(store, orders, payments, events, provider, httpx.MockTransport(handler))

    raw = _whatsapp_image_raw("receipt-bad")
    response = client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Hub-Signature-256": _wa_sign(raw), "content-type": "application/json"},
    )
    assert response.status_code == 200

    release = client.post(
        "/orders/SS-1001/release",
        headers={"x-internal-token": "internal-token"},
    )
    assert release.status_code == 409
    assert orders.orders[0]["status"] == "awaiting_payment"

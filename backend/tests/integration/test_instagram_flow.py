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
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider
from app.main import create_app
from app.speech.fake import FakeSpeechClient

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "instagram"
SECRET = "test-app-secret"
IG_ACCOUNT = "ig-account-1"


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        meta_app_secret=SECRET,
        meta_verify_token="verify-me",
        fb_page_access_token="test-page-token",
        fb_page_id="page-1",
        instagram_account_id=IG_ACCOUNT,
        graph_api_version="v21.0",
    )


def _sign(raw: bytes) -> str:
    digest = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post(client: TestClient, name: str, text: str) -> None:
    payload = json.loads((FIXTURES / "text.json").read_text(encoding="utf-8"))
    payload["entry"][0]["messaging"][0]["message"]["text"] = text
    payload["entry"][0]["messaging"][0]["message"]["mid"] = f"igmid.{name}"
    raw = json.dumps(payload).encode()
    headers = {"X-Hub-Signature-256": _sign(raw), "content-type": "application/json"}
    response = client.post("/webhooks/instagram", content=raw, headers=headers)
    assert response.status_code == 200


def test_instagram_bad_signature_returns_401() -> None:
    app = create_app(_settings(), store=MemoryEchoStore())
    client = TestClient(app)
    raw = b'{"object":"instagram"}'
    headers = {
        "X-Hub-Signature-256": "sha256=deadbeef",
        "content-type": "application/json",
    }
    response = client.post("/webhooks/instagram", content=raw, headers=headers)
    assert response.status_code == 401


def test_instagram_buyer_places_order() -> None:
    store = MemoryEchoStore()
    catalog = MemoryCatalogStore()
    orders = MemoryOrderStore()
    seller_id = store.ensure_seller(IG_ACCOUNT, channel="instagram")
    catalog.products.append(
        {
            "id": "p1",
            "seller_id": seller_id,
            "name": "Black tote",
            "description": "Leather bag",
            "price_kobo": 1_500_000,
        }
    )

    sent: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request.content)
        return httpx.Response(200, json={"message_id": "igmid.out"})

    provider = FakeProvider(
        chat=[
            {
                "text": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "name": "search_catalog",
                        "arguments": '{"query":"black tote"}',
                    }
                ],
            },
            {"text": "The black tote is ₦15,000."},
            {
                "text": "",
                "tool_calls": [
                    {
                        "id": "call-2",
                        "name": "search_catalog",
                        "arguments": '{"query":"black tote"}',
                    },
                    {
                        "id": "call-3",
                        "name": "create_order",
                        "arguments": (
                            '{"items":[{"product_id":"p1","qty":1,"unit_price_kobo":1500000}]}'
                        ),
                    },
                ],
            },
            {"text": "Order SS-1001 created. Total ₦15,000."},
        ]
    )

    app = create_app(
        _settings(),
        store=store,
        transport=httpx.MockTransport(handler),
        provider=provider,
        jev=FakeJev(intent="price_question", language="pcm"),
        catalog=catalog,
        orders=orders,
        payments=MemoryPaymentStore(),
    )
    client = TestClient(app)

    _post(client, "price", "Abeg how much for the black tote?")
    assert "15,000" in json.loads(sent[0])["message"]["text"]

    _post(client, "order", "I go take 1")
    assert orders.orders
    assert orders.orders[0]["status"] == "awaiting_payment"
    assert orders.orders[0]["total_kobo"] == 1_500_000
    assert orders.orders[0]["ref"].startswith("SS-")
    assert orders.orders[0]["ref"] in json.loads(sent[1])["message"]["text"]


def test_instagram_voice_note_creates_order() -> None:
    store = MemoryEchoStore()
    catalog = MemoryCatalogStore()
    orders = MemoryOrderStore()
    seller_id = store.ensure_seller(IG_ACCOUNT, channel="instagram")
    catalog.products.append(
        {
            "id": "p1",
            "seller_id": seller_id,
            "name": "Black tote",
            "price_kobo": 1_500_000,
        }
    )

    sent: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, content=b"ogg-bytes")
        sent.append(request.content)
        return httpx.Response(200, json={"message_id": "igmid.out"})

    provider = FakeProvider(
        chat=[
            {
                "text": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "name": "search_catalog",
                        "arguments": '{"query":"black tote"}',
                    },
                    {
                        "id": "call-2",
                        "name": "create_order",
                        "arguments": (
                            '{"items":[{"product_id":"p1","qty":1,"unit_price_kobo":1500000}]}'
                        ),
                    },
                ],
            },
            {"text": "Order SS-2001 created."},
        ]
    )

    payload = json.loads((FIXTURES / "audio.json").read_text(encoding="utf-8"))
    raw = json.dumps(payload).encode()
    headers = {"X-Hub-Signature-256": _sign(raw), "content-type": "application/json"}

    app = create_app(
        _settings(),
        store=store,
        transport=httpx.MockTransport(handler),
        provider=provider,
        jev=FakeJev(intent="order", language="pcm"),
        catalog=catalog,
        orders=orders,
        payments=MemoryPaymentStore(),
        speech=FakeSpeechClient(
            text="I want the black tote",
            language="pcm",
            confidence=0.9,
        ),
    )
    client = TestClient(app)

    response = client.post("/webhooks/instagram", content=raw, headers=headers)
    assert response.status_code == 200
    assert orders.orders
    assert orders.orders[0]["status"] == "awaiting_payment"
    saved = store.messages["igmid.test-audio-1"]
    assert saved["transcript"] == "I want the black tote"
    assert saved["language"] == "pcm"
    assert saved["asr_confidence"] == 0.9
    assert b"ogg-bytes" not in repr(store.messages).encode()

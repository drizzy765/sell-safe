import hashlib
import hmac
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.agent.templates import ask_price, saved_product
from app.config import Settings
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.db.storage import MemoryStorage
from app.llm.fake import FakeProvider
from app.main import create_app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"
SECRET = "test-app-secret"


def _sign(raw: bytes) -> str:
    digest = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post(
    client: TestClient, name: str, raw: bytes | None = None, text: str | None = None
) -> bytes:
    if raw is None:
        payload = json.loads((FIXTURES / "text.json").read_text(encoding="utf-8"))
        payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = text
        payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = f"wamid.{name}"
        raw = json.dumps(payload).encode()
    headers = {"X-Hub-Signature-256": _sign(raw), "content-type": "application/json"}
    response = client.post("/webhooks/whatsapp", content=raw, headers=headers)
    assert response.status_code == 200
    return raw


def test_photo_asks_for_price_then_saves_confirmed_kobo() -> None:
    echo = MemoryEchoStore()
    catalog = MemoryCatalogStore()
    storage = MemoryStorage()
    provider = FakeProvider(
        vision={
            "name": "Black tote",
            "description": "Leather tote",
            "suggested_price_kobo": 999,
            "category": "bags",
            "colors": ["black"],
            "confidence": 0.91,
        }
    )
    sent: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/media-image-1"):
            return httpx.Response(200, json={"url": "https://cdn.example/obj"})
        if request.method == "GET":
            return httpx.Response(200, content=b"jpeg-bytes")
        sent.append(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})

    app = create_app(
        Settings(
            llm_provider="groq",
            meta_app_secret=SECRET,
            meta_verify_token="verify-me",
            whatsapp_access_token="test-token",
            whatsapp_phone_number_id="1234567890",
            graph_api_version="v21.0",
        ),
        store=echo,
        transport=httpx.MockTransport(handler),
        provider=provider,
        storage=storage,
        catalog=catalog,
        orders=MemoryOrderStore(),
        payments=MemoryPaymentStore(),
    )
    client = TestClient(app)
    image = (FIXTURES / "image.json").read_bytes()

    _post(client, "image", raw=image)
    assert catalog.products == []
    assert len(provider.vision_calls) == 1
    assert json.loads(sent[0])["text"]["body"] == ask_price("Black tote")
    assert storage.objects
    assert "http" not in json.loads(sent[0])["text"]["body"]

    _post(client, "price", text="15000")
    assert catalog.products[0]["price_kobo"] == 1_500_000
    assert catalog.products[0]["name"] == "Black tote"
    assert json.loads(sent[1])["text"]["body"] == saved_product("Black tote", 1_500_000)
    assert "15000" not in json.loads(sent[1])["text"]["body"]

    _post(client, "image-again", raw=image)
    assert len(provider.vision_calls) == 1

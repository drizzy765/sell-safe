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

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"
SECRET = "test-app-secret"


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        meta_app_secret=SECRET,
        meta_verify_token="verify-me",
        whatsapp_access_token="test-token",
        whatsapp_phone_number_id="1234567890",
        graph_api_version="v21.0",
    )


def _sign(raw: bytes) -> str:
    digest = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_voice_note_is_transcribed_and_replied() -> None:
    store = MemoryEchoStore()
    sent: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/media-audio-1"):
            return httpx.Response(200, json={"url": "https://cdn.example/audio"})
        if request.method == "GET":
            return httpx.Response(200, content=b"ogg-bytes")
        sent.append(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})

    payload = json.loads((FIXTURES / "audio.json").read_text(encoding="utf-8"))
    raw = json.dumps(payload).encode()
    headers = {"X-Hub-Signature-256": _sign(raw), "content-type": "application/json"}

    app = create_app(
        _settings(),
        store=store,
        transport=httpx.MockTransport(handler),
        provider=FakeProvider(chat_text="ok"),
        jev=FakeJev(intent="chit_chat", language="en"),
        catalog=MemoryCatalogStore(),
        orders=MemoryOrderStore(),
        payments=MemoryPaymentStore(),
        speech=FakeSpeechClient(text="hello", language="en"),
    )
    client = TestClient(app)

    response = client.post("/webhooks/whatsapp", content=raw, headers=headers)
    assert response.status_code == 200
    assert len(sent) == 1
    assert json.loads(sent[0])["text"]["body"] == "ok"

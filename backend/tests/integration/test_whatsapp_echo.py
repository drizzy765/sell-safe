import hashlib
import hmac
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.echo_store import MemoryEchoStore
from app.main import create_app

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


def _client(store: MemoryEchoStore, transport: httpx.BaseTransport | None = None) -> TestClient:
    app = create_app(_settings(), store=store, transport=transport)
    return TestClient(app)


def test_verify_handshake_echoes_challenge() -> None:
    response = _client(MemoryEchoStore()).get(
        "/webhooks/meta",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "abc123",
        },
    )

    assert response.status_code == 200
    assert response.text == "abc123"


def test_verify_handshake_rejects_wrong_token() -> None:
    response = _client(MemoryEchoStore()).get(
        "/webhooks/meta",
        params={"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "abc123"},
    )

    assert response.status_code == 403


def test_bad_signature_stores_nothing() -> None:
    store = MemoryEchoStore()
    raw = (FIXTURES / "text.json").read_bytes()
    response = _client(store).post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Hub-Signature-256": "sha256=" + ("0" * 64), "content-type": "application/json"},
    )

    assert response.status_code == 401
    assert store.messages == {}


def test_text_is_echoed_once_and_duplicate_is_ignored() -> None:
    store = MemoryEchoStore()
    sent: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out-1"}]})

    raw = (FIXTURES / "text.json").read_bytes()
    headers = {"X-Hub-Signature-256": _sign(raw), "content-type": "application/json"}
    client = _client(store, transport=httpx.MockTransport(handler))

    first = client.post("/webhooks/whatsapp", content=raw, headers=headers)
    second = client.post("/webhooks/whatsapp", content=raw, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(sent) == 1
    assert json.loads(sent[0])["text"]["body"] == "hello"
    assert "wamid.test-text-1" in store.messages
    assert len(store.sellers) == 1
    assert ("whatsapp", "15550000001") in store.buyers

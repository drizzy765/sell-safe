import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.config import Settings

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"
SECRET = "test-app-secret"


def _settings() -> Settings:
    return Settings(
        meta_app_secret=SECRET,
        whatsapp_access_token="test-token",
        whatsapp_phone_number_id="1234567890",
        graph_api_version="v21.0",
    )


def _sign(raw: bytes, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_signature_passes_and_mutated_body_fails() -> None:
    adapter = WhatsAppAdapter(_settings())
    raw = b'{"ok":true}'
    headers = {"X-Hub-Signature-256": _sign(raw)}

    assert adapter.verify_signature(raw, headers) is True
    assert adapter.verify_signature(b'{"ok":false}', headers) is False


def test_missing_secret_rejects_every_signature() -> None:
    adapter = WhatsAppAdapter(Settings(meta_app_secret=""))
    raw = b"{}"
    headers = {"X-Hub-Signature-256": _sign(raw)}

    assert adapter.verify_signature(raw, headers) is False


def test_parse_text_image_audio_and_ignore_status() -> None:
    adapter = WhatsAppAdapter(_settings())

    text = adapter.parse(_load("text.json"))
    assert len(text) == 1
    assert text[0].type == "text"
    assert text[0].text == "hello"
    assert text[0].external_id == "wamid.test-text-1"
    assert text[0].sender_id == "15550000001"
    assert text[0].display_name == "Ada"
    assert text[0].channel == "whatsapp"
    assert text[0].ts == datetime.fromtimestamp(1710000000, tz=UTC)

    image = adapter.parse(_load("image.json"))
    assert image[0].type == "image"
    assert image[0].media_id == "media-image-1"
    assert image[0].text == "black bag"

    audio = adapter.parse(_load("audio.json"))
    assert audio[0].type == "audio"
    assert audio[0].media_id == "media-audio-1"
    assert audio[0].text is None

    assert adapter.parse(_load("status.json")) == []


@pytest.mark.asyncio
async def test_send_text_posts_to_graph() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out-1"}]})

    adapter = WhatsAppAdapter(_settings(), transport=httpx.MockTransport(handler))
    message_id = await adapter.send_text("15550000001", "hello")

    assert message_id == "wamid.out-1"
    assert len(seen) == 1
    assert seen[0].url.path == "/v21.0/1234567890/messages"
    assert seen[0].headers["authorization"] == "Bearer test-token"
    assert json.loads(seen[0].content) == {
        "messaging_product": "whatsapp",
        "to": "15550000001",
        "type": "text",
        "text": {"body": "hello"},
    }


@pytest.mark.asyncio
async def test_send_image_and_fetch_media_are_not_implemented() -> None:
    adapter = WhatsAppAdapter(_settings())
    with pytest.raises(NotImplementedError):
        await adapter.send_image("15550000001", "https://example.test/a.jpg", "bag")
    with pytest.raises(NotImplementedError):
        await adapter.fetch_media("media-image-1")

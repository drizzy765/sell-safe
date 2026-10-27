import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from app.channels.instagram.adapter import InstagramAdapter
from app.config import Settings

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "instagram"
SECRET = "test-app-secret"


def _settings() -> Settings:
    return Settings(
        meta_app_secret=SECRET,
        fb_page_access_token="test-page-token",
        fb_page_id="page-1",
        instagram_account_id="ig-account-1",
        graph_api_version="v21.0",
    )


def _sign(raw: bytes, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_signature_passes_and_mutated_body_fails() -> None:
    adapter = InstagramAdapter(_settings())
    raw = b'{"ok":true}'
    headers = {"X-Hub-Signature-256": _sign(raw)}

    assert adapter.verify_signature(raw, headers) is True
    assert adapter.verify_signature(b'{"ok":false}', headers) is False


def test_missing_secret_rejects_every_signature() -> None:
    adapter = InstagramAdapter(Settings(meta_app_secret=""))
    raw = b"{}"
    headers = {"X-Hub-Signature-256": _sign(raw)}

    assert adapter.verify_signature(raw, headers) is False


def test_parse_text_image_audio() -> None:
    adapter = InstagramAdapter(_settings())

    text = adapter.parse(_load("text.json"))
    assert len(text) == 1
    assert text[0].type == "text"
    assert text[0].text == "hello"
    assert text[0].external_id == "igmid.test-text-1"
    assert text[0].sender_id == "ig-buyer-1"
    assert text[0].channel == "instagram"
    assert text[0].ts == datetime.fromtimestamp(1710000000, tz=UTC)

    image = adapter.parse(_load("image.json"))
    assert image[0].type == "image"
    assert image[0].media_id == "https://cdn.example/ig-image-1.jpg"
    assert image[0].text is None

    audio = adapter.parse(_load("audio.json"))
    assert audio[0].type == "audio"
    assert audio[0].media_id == "https://cdn.example/ig-audio-1.ogg"
    assert audio[0].text is None


@pytest.mark.asyncio
async def test_send_text_posts_to_graph() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"message_id": "igmid.out-1"})

    adapter = InstagramAdapter(_settings(), transport=httpx.MockTransport(handler))
    message_id = await adapter.send_text("ig-buyer-1", "hello")

    assert message_id == "igmid.out-1"
    assert len(seen) == 1
    assert seen[0].url.path == "/v21.0/page-1/messages"
    assert seen[0].headers["authorization"] == "Bearer test-page-token"
    assert json.loads(seen[0].content) == {
        "recipient": {"id": "ig-buyer-1"},
        "message": {"text": "hello"},
    }


@pytest.mark.asyncio
async def test_fetch_media_downloads_cdn_url() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=b"jpeg-bytes")

    adapter = InstagramAdapter(_settings(), transport=httpx.MockTransport(handler))
    payload = await adapter.fetch_media("https://cdn.example/ig-image-1.jpg")

    assert payload == b"jpeg-bytes"
    assert len(seen) == 1
    assert str(seen[0].url) == "https://cdn.example/ig-image-1.jpg"

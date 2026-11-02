"""Instagram Messaging API: signature check, parse, and text send.

Webhook payloads follow the Messenger Platform shape with
`object: "instagram"`. Media attachments usually include a CDN URL rather
than a Graph media id; `fetch_media` accepts either.
"""

import hashlib
import hmac
from datetime import UTC, datetime

import httpx

from app.channels.base import InboundMessage
from app.config import Settings

_GRAPH_HOST = "https://graph.facebook.com"
_IG_LOGIN_HOST = "https://graph.instagram.com"


def _header(headers: object, name: str) -> str:
    if headers is None:
        return ""
    getter = getattr(headers, "get", None)
    if getter is None:
        return ""
    value = getter(name)
    if value is None:
        value = getter(name.lower())
    return "" if value is None else str(value)


class InstagramAdapter:
    name = "instagram"

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def verify_signature(self, raw: bytes, headers: object) -> bool:
        secret = self._settings.instagram_app_secret or self._settings.meta_app_secret
        if not secret:
            return False
        provided = _header(headers, "X-Hub-Signature-256")
        prefix = "sha256="
        if not provided.startswith(prefix):
            return False
        expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        given = provided[len(prefix) :]
        if len(given) != len(expected):
            return False
        return hmac.compare_digest(given, expected)

    def parse(self, payload: dict) -> list[InboundMessage]:
        messages: list[InboundMessage] = []
        for entry in payload.get("entry") or []:
            # Messenger-style Instagram Messaging events.
            for event in entry.get("messaging") or []:
                parsed = _parse_messaging_event(event)
                if parsed is not None:
                    messages.append(parsed)
            # Also accept a WhatsApp-like changes envelope if Meta ever sends it.
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                for item in value.get("messages") or []:
                    parsed = _parse_change_message(item)
                    if parsed is not None:
                        messages.append(parsed)
        return messages

    async def send_text(self, to: str, text: str) -> str:
        version = self._settings.graph_api_version
        body = {
            "recipient": {"id": to},
            "message": {"text": text},
        }
        login_token = self._settings.instagram_access_token
        if version and login_token:
            url = f"{_IG_LOGIN_HOST}/{version}/me/messages"
            token = login_token
        else:
            page_id = self._settings.fb_page_id or self._settings.instagram_account_id
            token = self._settings.fb_page_access_token
            if not version or not page_id or not token:
                raise RuntimeError("Instagram send is not configured")
            url = f"{_GRAPH_HOST}/{version}/{page_id}/messages"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
        return str(data.get("message_id") or data.get("id") or "")

    async def send_image(self, to: str, url: str, caption: str) -> str:
        """Send an image attachment via Instagram Messaging API."""
        version = self._settings.graph_api_version
        body: dict = {
            "recipient": {"id": to},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {"url": url, "is_reusable": True},
                }
            },
        }
        login_token = self._settings.instagram_access_token
        if version and login_token:
            endpoint = f"{_IG_LOGIN_HOST}/{version}/me/messages"
            token = login_token
        else:
            page_id = self._settings.fb_page_id or self._settings.instagram_account_id
            token = self._settings.fb_page_access_token
            if not version or not page_id or not token:
                raise RuntimeError("Instagram send is not configured")
            endpoint = f"{_GRAPH_HOST}/{version}/{page_id}/messages"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(endpoint, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
        message_id = str(data.get("message_id") or data.get("id") or "")
        if caption and caption.strip():
            # Messaging API image payload has no caption field — follow with text.
            await self.send_text(to, caption.strip())
        return message_id

    async def fetch_media(self, media_id: str) -> bytes:
        token = self._settings.fb_page_access_token
        version = self._settings.graph_api_version
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(transport=self._transport) as client:
            if media_id.startswith("http://") or media_id.startswith("https://"):
                response = await client.get(media_id, headers=headers)
                response.raise_for_status()
                return response.content
            if not version or not token:
                raise RuntimeError("Instagram media download is not configured")
            meta_url = f"{_GRAPH_HOST}/{version}/{media_id}"
            meta = await client.get(meta_url, headers=headers)
            meta.raise_for_status()
            download_url = str(meta.json()["url"])
            media = await client.get(download_url, headers=headers)
            media.raise_for_status()
            return media.content


def _parse_messaging_event(event: dict) -> InboundMessage | None:
    message = event.get("message") or {}
    if not message or message.get("is_echo"):
        return None
    sender = str((event.get("sender") or {}).get("id") or "")
    external_id = str(message.get("mid") or "")
    if not sender or not external_id:
        return None

    text: str | None = None
    media_id: str | None = None
    kind = "text"

    if message.get("text"):
        text = str(message["text"])
        kind = "text"
    else:
        attachments = message.get("attachments") or []
        if not attachments:
            return None
        attachment = attachments[0]
        att_type = str(attachment.get("type") or "")
        payload = attachment.get("payload") or {}
        url = payload.get("url")
        if att_type in ("image", "story_mention"):
            kind = "image"
            media_id = str(url) if url else None
        elif att_type in ("audio", "file", "video"):
            # Voice notes and audio files go through STT as audio.
            kind = "audio"
            media_id = str(url) if url else None
        else:
            return None
        if not media_id:
            return None

    ts_raw = event.get("timestamp") or 0
    try:
        # IG timestamps are often milliseconds.
        ts_int = int(ts_raw)
        if ts_int > 10_000_000_000:
            ts_int = ts_int // 1000
        ts = datetime.fromtimestamp(ts_int, tz=UTC)
    except (TypeError, ValueError, OSError):
        ts = datetime.now(tz=UTC)

    return InboundMessage(
        channel="instagram",
        external_id=external_id,
        sender_id=sender,
        type=kind,  # type: ignore[arg-type]
        text=text,
        media_id=media_id,
        display_name=None,
        ts=ts,
    )


def _parse_change_message(item: dict) -> InboundMessage | None:
    kind = item.get("type")
    if kind not in ("text", "image", "audio"):
        return None
    sender = str(item.get("from") or "")
    external_id = str(item.get("id") or "")
    if not sender or not external_id:
        return None
    text: str | None = None
    media_id: str | None = None
    if kind == "text":
        text = str((item.get("text") or {}).get("body") or item.get("text") or "")
    elif kind == "image":
        image = item.get("image") or {}
        media_id = image.get("id") or image.get("url")
        caption = image.get("caption")
        text = str(caption) if caption else None
    else:
        audio = item.get("audio") or {}
        media_id = audio.get("id") or audio.get("url")
    try:
        ts = datetime.fromtimestamp(int(item.get("timestamp") or 0), tz=UTC)
    except (TypeError, ValueError, OSError):
        ts = datetime.now(tz=UTC)
    return InboundMessage(
        channel="instagram",
        external_id=external_id,
        sender_id=sender,
        type=kind,
        text=text,
        media_id=str(media_id) if media_id else None,
        display_name=None,
        ts=ts,
    )

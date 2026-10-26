"""WhatsApp Cloud API: signature check, parse, and text send."""

import hashlib
import hmac
from collections.abc import Mapping
from datetime import UTC, datetime

import httpx

from app.channels.base import InboundMessage
from app.config import Settings

_GRAPH_HOST = "https://graph.facebook.com"


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


class WhatsAppAdapter:
    name = "whatsapp"

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def verify_signature(self, raw: bytes, headers: object) -> bool:
        secret = self._settings.meta_app_secret
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
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                names = _contact_names(value)
                for item in value.get("messages") or []:
                    parsed = _parse_message(item, names)
                    if parsed is not None:
                        messages.append(parsed)
        return messages

    async def send_text(self, to: str, text: str) -> str:
        version = self._settings.graph_api_version
        phone_id = self._settings.whatsapp_phone_number_id
        token = self._settings.whatsapp_access_token
        if not version or not phone_id or not token:
            raise RuntimeError("WhatsApp send is not configured")
        url = f"{_GRAPH_HOST}/{version}/{phone_id}/messages"
        body = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
        return str(data["messages"][0]["id"])

    async def send_image(self, to: str, url: str, caption: str) -> str:
        raise NotImplementedError

    async def fetch_media(self, media_id: str) -> bytes:
        version = self._settings.graph_api_version
        token = self._settings.whatsapp_access_token
        if not version or not token:
            raise RuntimeError("WhatsApp media download is not configured")
        headers = {"Authorization": f"Bearer {token}"}
        meta_url = f"{_GRAPH_HOST}/{version}/{media_id}"
        async with httpx.AsyncClient(transport=self._transport) as client:
            meta = await client.get(meta_url, headers=headers)
            meta.raise_for_status()
            download_url = str(meta.json()["url"])
            media = await client.get(download_url, headers=headers)
            media.raise_for_status()
        return media.content


def _contact_names(value: dict) -> dict[str, str]:
    names: dict[str, str] = {}
    for contact in value.get("contacts") or []:
        wa_id = contact.get("wa_id")
        profile = contact.get("profile") or {}
        name = profile.get("name")
        if wa_id and name:
            names[str(wa_id)] = str(name)
    return names


def _parse_message(item: dict, names: Mapping[str, str]) -> InboundMessage | None:
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
        text = str((item.get("text") or {}).get("body") or "")
    elif kind == "image":
        image = item.get("image") or {}
        media_id = image.get("id")
        caption = image.get("caption")
        text = str(caption) if caption else None
    else:
        media_id = (item.get("audio") or {}).get("id")
    ts = datetime.fromtimestamp(int(item.get("timestamp") or 0), tz=UTC)
    return InboundMessage(
        channel="whatsapp",
        external_id=external_id,
        sender_id=sender,
        type=kind,
        text=text,
        media_id=str(media_id) if media_id else None,
        display_name=names.get(sender),
        ts=ts,
    )

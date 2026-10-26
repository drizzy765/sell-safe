"""Normalized inbound messages and the channel adapter contract."""

from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel

ChannelName = Literal["whatsapp", "instagram", "messenger"]
MessageType = Literal["text", "image", "audio"]


class InboundMessage(BaseModel):
    channel: ChannelName
    external_id: str
    sender_id: str
    seller_id: str | None = None
    type: MessageType
    text: str | None = None
    media_id: str | None = None
    display_name: str | None = None
    ts: datetime


class ChannelAdapter(Protocol):
    name: ChannelName

    def verify_signature(self, raw: bytes, headers: object) -> bool: ...

    def parse(self, payload: dict) -> list[InboundMessage]: ...

    async def send_text(self, to: str, text: str) -> str: ...

    async def send_image(self, to: str, url: str, caption: str) -> str: ...

    async def fetch_media(self, media_id: str) -> bytes: ...

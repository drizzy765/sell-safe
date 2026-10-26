"""Jev routing contract. Model names and keys come from the environment."""

from typing import Protocol

from pydantic import BaseModel, Field


class RouteScores(BaseModel):
    intent: str
    intent_scores: dict[str, float] = Field(default_factory=dict)
    language: str
    language_scores: dict[str, float] = Field(default_factory=dict)
    scam_pressure: float = 0.0
    image_kind: str | None = None
    image_kind_scores: dict[str, float] | None = None


class JevConfigError(RuntimeError):
    """A required key or configuration is missing."""


INTENTS = [
    "price_question",
    "order",
    "payment_proof",
    "order_status",
    "complaint",
    "chit_chat",
    "seller_command",
]

LANGUAGES = ["en", "pcm", "yo", "ig", "ha", "other"]

IMAGE_KINDS = ["product_photo", "payment_receipt", "other"]


class JevClient(Protocol):
    async def ask(
        self,
        *,
        text: str,
        seller_default_language: str = "en",
        image_extraction: dict | None = None,
    ) -> RouteScores: ...

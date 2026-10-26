"""Speech client contract."""

from typing import Protocol

from pydantic import BaseModel


class TranscriptResult(BaseModel):
    text: str
    language: str = "en"
    confidence: float | None = None


class SpeechConfigError(RuntimeError):
    """Missing key or URL."""


class SpeechClient(Protocol):
    async def transcribe(
        self,
        audio: bytes,
        language_hint: str | None = None,
    ) -> TranscriptResult: ...

"""Fake speech client for tests."""

from app.speech.base import TranscriptResult


class FakeSpeechClient:
    def __init__(
        self,
        text: str = "hello",
        language: str = "en",
        confidence: float | None = 0.91,
    ) -> None:
        self.text = text
        self.language = language
        self.confidence = confidence

    async def transcribe(
        self,
        audio: bytes,
        language_hint: str | None = None,
    ) -> TranscriptResult:
        return TranscriptResult(
            text=self.text,
            language=self.language,
            confidence=self.confidence,
        )

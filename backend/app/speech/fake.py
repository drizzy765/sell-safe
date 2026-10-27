"""Fake speech client for tests."""

from app.speech.base import TranscriptResult


class FakeSpeechClient:
    def __init__(
        self,
        text: str = "hello",
        language: str = "en",
        confidence: float | None = 0.91,
        *,
        fail: bool = False,
    ) -> None:
        self.text = text
        self.language = language
        self.confidence = confidence
        self.fail = fail
        self.calls = 0

    async def transcribe(
        self,
        audio: bytes,
        language_hint: str | None = None,
    ) -> TranscriptResult:
        self.calls += 1
        if self.fail:
            raise RuntimeError("stt failed")
        return TranscriptResult(
            text=self.text,
            language=self.language,
            confidence=self.confidence,
        )

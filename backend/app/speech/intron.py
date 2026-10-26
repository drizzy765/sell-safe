"""Intron Sahara STT client. URL is TODO verify against the Intron docs."""

from typing import Any

import httpx

from app.config import Settings
from app.speech.base import SpeechConfigError, TranscriptResult


class IntronSpeechClient:
    """Transcribe audio with Intron Sahara v2.5.

    The endpoint shape is not confirmed. Update INTRON_STT_URL once the
    official docs are checked.
    """

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def _require(self, value: str, name: str) -> str:
        if not value:
            raise SpeechConfigError(f"{name} is not configured")
        return value

    async def transcribe(
        self,
        audio: bytes,
        language_hint: str | None = None,
    ) -> TranscriptResult:
        key = self._require(self._settings.intron_api_key, "INTRON_API_KEY")
        url = self._settings.intron_stt_url or "https://infer.voice.intron.io/stt/v1/transcribe"
        headers = {"Authorization": f"Bearer {key}"}
        files: dict[str, Any] = {"file": ("audio.ogg", audio, "audio/ogg")}
        data = {"language": language_hint or "en"}
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(url, data=data, files=files, headers=headers)
            response.raise_for_status()
            payload = response.json()
        return TranscriptResult(
            text=str(payload.get("text") or ""),
            language=str(payload.get("language") or language_hint or "en"),
            confidence=payload.get("confidence"),
        )

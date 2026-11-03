"""Intron Sahara STT client (file upload/sync contract).

Verified live 2026-11-03 against https://infer.voice.intron.io/file/v1/upload/sync:
multipart file part `audio_file_blob`, form fields `audio_file_name` and
`use_language_asr_input` (a language code such as "en"); the transcript is
`data.audio_transcript` in the JSON response.
"""

from typing import Any

import httpx

from app.config import Settings
from app.speech.base import SpeechConfigError, TranscriptResult


def _audio_format(audio: bytes) -> tuple[str, str]:
    if audio.startswith(b"RIFF"):
        return "wav", "audio/wav"
    if audio.startswith(b"OggS"):
        return "ogg", "audio/ogg"
    if audio.startswith(b"ID3") or audio[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3", "audio/mpeg"
    # Instagram voice notes are MP4/AAC; default to mp4.
    return "mp4", "audio/mp4"


class IntronSpeechClient:
    """Transcribe audio with Intron Sahara via the file upload/sync API."""

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
        url = self._settings.intron_stt_url or "https://infer.voice.intron.io/file/v1/upload/sync"
        headers = {"Authorization": f"Bearer {key}"}
        ext, mime = _audio_format(audio)
        filename = f"audio.{ext}"
        files: dict[str, Any] = {"audio_file_blob": (filename, audio, mime)}
        data = {
            "audio_file_name": filename,
            "use_language_asr_input": language_hint or "en",
        }
        # Do not log `audio` — may contain buyer speech content.
        async with httpx.AsyncClient(transport=self._transport, timeout=120) as client:
            response = await client.post(url, data=data, files=files, headers=headers)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(
                    f"Intron STT failed ({exc.response.status_code}): {exc.response.text[:500]}"
                ) from exc
            payload = response.json()
        body = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        confidence_raw = body.get("confidence", body.get("asr_confidence"))
        confidence: float | None
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else None
        except (TypeError, ValueError):
            confidence = None
        return TranscriptResult(
            text=str(
                body.get("audio_transcript") or body.get("text") or body.get("transcript") or ""
            ),
            language=str(body.get("language") or language_hint or "en"),
            confidence=confidence,
        )

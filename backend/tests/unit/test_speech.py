import pytest

from app.speech.fake import FakeSpeechClient


@pytest.mark.asyncio
async def test_fake_speech_returns_transcript() -> None:
    client = FakeSpeechClient(text="abeg how much", language="pcm", confidence=0.88)
    result = await client.transcribe(b"ogg-bytes")
    assert result.text == "abeg how much"
    assert result.language == "pcm"
    assert result.confidence == 0.88


@pytest.mark.asyncio
async def test_intron_client_sends_required_fields_and_parses_transcript() -> None:
    """Regression: Intron upload/sync requires audio_file_blob (file part),
    audio_file_name, and use_language_asr_input as a language code. The old
    client sent file+language and every voice note failed with 400."""
    import httpx

    from app.config import Settings
    from app.speech.intron import IntronSpeechClient

    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content.decode("utf-8", errors="ignore")
        return httpx.Response(
            200,
            json={
                "status": "Ok",
                "data": {
                    "audio_file_name": "audio_wav",
                    "audio_transcript": "How much is honey beans?",
                    "processing_status": "FILE_QUEUED",
                },
            },
        )

    settings = Settings(intron_api_key="test-key", intron_stt_url="https://intron.test/upload")
    client = IntronSpeechClient(settings, transport=httpx.MockTransport(handler))
    result = await client.transcribe(b"RIFF\x24\x00\x00\x00WAVEfmt ", language_hint="en")

    assert result.text == "How much is honey beans?"
    assert "audio_file_blob" in seen["body"]
    assert "audio_file_name" in seen["body"]
    assert "use_language_asr_input" in seen["body"]

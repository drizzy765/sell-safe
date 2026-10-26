import pytest

from app.speech.fake import FakeSpeechClient


@pytest.mark.asyncio
async def test_fake_speech_returns_transcript() -> None:
    client = FakeSpeechClient(text="abeg how much", language="pcm", confidence=0.88)
    result = await client.transcribe(b"ogg-bytes")
    assert result.text == "abeg how much"
    assert result.language == "pcm"
    assert result.confidence == 0.88

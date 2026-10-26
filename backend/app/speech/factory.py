"""Build a speech client from settings."""

from app.config import Settings
from app.speech.base import SpeechClient
from app.speech.fake import FakeSpeechClient
from app.speech.intron import IntronSpeechClient


def build_speech(settings: Settings) -> SpeechClient:
    if settings.intron_api_key:
        return IntronSpeechClient(settings)
    return FakeSpeechClient()

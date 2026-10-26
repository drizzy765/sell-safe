"""Build a Jev client from settings."""

from app.config import Settings
from app.decisions.base import JevClient
from app.decisions.client import TypeSafeClient
from app.decisions.fake import FakeJev


def build_jev(settings: Settings) -> JevClient:
    """Return a real TypeSafe client when a key is set, otherwise a fake for local dev."""
    if settings.typesafe_api_key:
        return TypeSafeClient(settings)
    return FakeJev()

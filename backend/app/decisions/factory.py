"""Build a Jev client from settings."""

from app.config import Settings
from app.decisions.base import JevClient
from app.decisions.client import TypeSafeClient
from app.decisions.heuristic import HeuristicJev


def build_jev(settings: Settings) -> JevClient:
    """Return TypeSafe when TYPESAFE_API_KEY is set, otherwise the heuristic router."""
    if settings.typesafe_api_key:
        return TypeSafeClient(settings)
    return HeuristicJev()

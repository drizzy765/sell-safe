"""Fake Jev client for tests."""

from app.decisions.base import RouteScores


class FakeJev:
    """Return canned routing scores. Tests set the answers they need."""

    def __init__(
        self,
        intent: str = "chit_chat",
        language: str = "en",
        scam_pressure: float = 0.0,
        image_kind: str | None = None,
        intent_scores: dict[str, float] | None = None,
        language_scores: dict[str, float] | None = None,
    ) -> None:
        self.intent = intent
        self.language = language
        self.scam_pressure = scam_pressure
        self.image_kind = image_kind
        self.intent_scores = intent_scores or {intent: 1.0}
        self.language_scores = language_scores or {language: 1.0}

    async def ask(
        self,
        *,
        text: str,
        seller_default_language: str = "en",
        image_extraction: dict | None = None,
    ) -> RouteScores:
        language = self.language if self.language != "other" else seller_default_language
        return RouteScores(
            intent=self.intent,
            intent_scores=self.intent_scores,
            language=language,
            language_scores=self.language_scores,
            scam_pressure=self.scam_pressure,
            image_kind=self.image_kind,
        )

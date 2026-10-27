"""TypeSafe Jev client. Exact request schema is TODO verify against docs.typesafe.ai."""

from typing import Any

import httpx

from app.config import Settings
from app.decisions.base import IMAGE_KINDS, INTENTS, LANGUAGES, JevConfigError, RouteScores


class TypeSafeClient:
    """Call TypeSafe /systemone with the question specs from docs/agent.md.

    The request body shape here is a working hypothesis. Verify it against the
    official docs before running a live test; the fake client is used in CI.
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
            raise JevConfigError(f"{name} is not configured")
        return value

    def _questions(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "intent",
                "type": "choice",
                "options": INTENTS,
            },
            {
                "id": "language",
                "type": "choice",
                "options": LANGUAGES,
            },
            {
                "id": "scam_pressure",
                "type": "score",
                "min": 0.0,
                "max": 1.0,
            },
            {
                "id": "image_kind",
                "type": "choice",
                "options": IMAGE_KINDS,
            },
            {
                "id": "receipt_tampered",
                "type": "score",
                "min": 0.0,
                "max": 1.0,
            },
            {
                "id": "evidence_match",
                "type": "score",
                "min": 0.0,
                "max": 1.0,
            },
        ]

    async def ask(
        self,
        *,
        text: str,
        seller_default_language: str = "en",
        image_extraction: dict | None = None,
    ) -> RouteScores:
        key = self._require(self._settings.typesafe_api_key, "TYPESAFE_API_KEY")
        base = self._settings.typesafe_api_base_url or "https://api.typesafe.ai"
        url = f"{base.rstrip('/')}/v1/systemone"
        context: dict[str, Any] = {
            "text": text,
            "seller_default_language": seller_default_language,
        }
        if image_extraction:
            context["image_extraction"] = image_extraction
        body = {
            "questions": self._questions(),
            "context": context,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
            payload = response.json()
        return self._parse(payload, seller_default_language)

    def _parse(self, payload: dict, seller_default_language: str) -> RouteScores:
        answers = payload.get("answers") or payload.get("results") or {}
        intent_scores = self._scores(answers.get("intent") or {})
        language_scores = self._scores(answers.get("language") or {})
        image_kind_scores = self._scores(answers.get("image_kind") or {})

        intent = (
            max(intent_scores, key=intent_scores.get, default="chit_chat")
            if intent_scores
            else "chit_chat"
        )
        language = (
            max(language_scores, key=language_scores.get, default=seller_default_language)
            if language_scores
            else seller_default_language
        )
        if language == "other":
            language = seller_default_language

        return RouteScores(
            intent=intent,
            intent_scores=intent_scores,
            language=language,
            language_scores=language_scores,
            scam_pressure=float(answers.get("scam_pressure", 0.0) or 0.0),
            image_kind=max(image_kind_scores, key=image_kind_scores.get)
            if image_kind_scores
            else None,
            image_kind_scores=image_kind_scores or None,
            receipt_tampered=float(answers.get("receipt_tampered", 0.0) or 0.0),
            evidence_match=float(answers.get("evidence_match", 0.0) or 0.0),
        )

    def _scores(self, value: Any) -> dict[str, float]:
        if isinstance(value, dict):
            return {str(k): float(v) for k, v in value.items()}
        return {}

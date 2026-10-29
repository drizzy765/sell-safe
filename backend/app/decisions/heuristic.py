"""Deterministic router used when TYPESAFE_API_KEY is empty.

Phrase rules set intent, language, and scam pressure. Receipt scores stay at
zero: this router never decides whether money arrived.
"""

import re
import unicodedata

from app.decisions.base import INTENTS, LANGUAGES, RouteScores

_MATCH = 0.9
_OTHER = 0.05
_SCAM_STEP = 0.25

# First matching buyer phrase wins. A leading "/" is handled separately so
# `/release SS-1042` stays a seller command instead of an order-status lookup.
_INTENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "payment_proof",
        ("receipt", "transfer", "screenshot", "i don pay", "i have paid", "money don land"),
    ),
    ("order", ("i go take", "i want", "reserve", "order am", "make i buy")),
    (
        "price_question",
        ("how much", "how much be", "elo ni", "price", "wetin be the price"),
    ),
    ("order_status", ("status", "where my order", "ss-")),
    ("complaint", ("scam", "fake", "refund", "complaint")),
)

_YORUBA_LETTERS = frozenset("ẹọṣ")
_YORUBA_MARKS = frozenset("\u0300\u0301")
_YORUBA_WORDS = ("elo", "jọwọ", "ṣe", "owo")
_PIDGIN_MARKERS = ("abeg", "dey", "wan", "wetin", "na so", "don", "no be")
_SCAM_PHRASES = (
    "send the goods first",
    "urgent",
    "trust me",
    "i don pay release am",
    "don't check",
)


class HeuristicJev:
    """Route one turn from buyer text. Image kind stays unset."""

    async def ask(
        self,
        *,
        text: str,
        seller_default_language: str = "en",
        image_extraction: dict | None = None,
    ) -> RouteScores:
        folded = _fold(text)
        intent = _intent(folded)
        language = _language(folded)
        return RouteScores(
            intent=intent,
            intent_scores=_scores(INTENTS, intent),
            language=language,
            language_scores=_scores(LANGUAGES, language),
            scam_pressure=_scam_pressure(folded),
            image_kind=None,
        )


def _fold(text: str) -> str:
    normalized = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    return unicodedata.normalize("NFC", normalized)


def _intent(text: str) -> str:
    if text.strip().startswith("/"):
        return "seller_command"
    for name, phrases in _INTENT_RULES:
        if any(phrase in text for phrase in phrases):
            return name
    return "chit_chat"


def _language(text: str) -> str:
    if _is_yoruba(text):
        return "yo"
    if _is_pidgin(text):
        return "pcm"
    return "en"


def _is_yoruba(text: str) -> bool:
    if any(char in _YORUBA_LETTERS for char in text):
        return True
    decomposed = unicodedata.normalize("NFD", text)
    if any(char in _YORUBA_MARKS for char in decomposed):
        return True
    return any(_has_marker(text, word) for word in _YORUBA_WORDS)


def _is_pidgin(text: str) -> bool:
    return any(_has_marker(text, marker) for marker in _PIDGIN_MARKERS)


def _has_marker(text: str, marker: str) -> bool:
    if marker == "don":
        return re.search(r"(?<!\w)don(?!'t)(?!\w)", text) is not None
    return re.search(rf"(?<!\w){re.escape(marker)}(?!\w)", text) is not None


def _scam_pressure(text: str) -> float:
    hits = sum(phrase in text for phrase in _SCAM_PHRASES)
    return min(1.0, hits * _SCAM_STEP)


def _scores(labels: list[str], winner: str) -> dict[str, float]:
    return {label: _MATCH if label == winner else _OTHER for label in labels}

"""Post-process and safety-check agent replies before sending."""

import json
import re

from app.agent.templates import format_naira


class ReplyCheckError(ValueError):
    """The reply failed a policy check."""


def _find_prices(text: str) -> set[int]:
    prices: set[int] = set()
    for match in re.finditer(r"₦\s?([\d,]+)", text):
        cleaned = match.group(1).replace(",", "")
        if cleaned.isdigit():
            prices.add(int(cleaned) * 100)
    for match in re.finditer(r"NGN\s?([\d,]+)", text, re.IGNORECASE):
        cleaned = match.group(1).replace(",", "")
        if cleaned.isdigit():
            prices.add(int(cleaned) * 100)
    return prices


def check_reply(
    reply: str,
    *,
    language: str,
    allowed_prices_kobo: set[int] | None = None,
    verdict: str | None = None,
) -> str:
    """Return the reply if it passes checks, otherwise raise ReplyCheckError."""
    if not reply or not reply.strip():
        raise ReplyCheckError("empty reply")

    text = reply.strip()

    # Detect invented prices.
    if allowed_prices_kobo is not None:
        for price in _find_prices(text):
            if price not in allowed_prices_kobo:
                raise ReplyCheckError(f"reply contains price {format_naira(price)} not from tools")

    # Never confirm payment unless verdict is CONFIRMED.
    lower = text.lower()
    confirmed_phrases = ["payment confirmed", "payment don confirm", "owo ti jọrisi", "don land"]
    if any(phrase in lower for phrase in confirmed_phrases) and verdict != "CONFIRMED":
        raise ReplyCheckError("reply claims payment confirmed without CONFIRMED verdict")

    # Do not expose full account numbers.
    if re.search(r"\b\d{10,}\b", text):
        raise ReplyCheckError("reply contains a long number that looks like an account number")

    return text


def fallback_reply(language: str) -> str:
    fallbacks = {
        "en": "I'm not sure I understood. Can you say that again?",
        "pcm": "I no too understand. Abeg talk am again.",
        "yo": "N ko gbọ́ dáadáa. Ṣé o lè sọ rẹ̀ padà?",
    }
    return fallbacks.get(language, fallbacks["en"])


def tool_results_to_json(results: list[dict]) -> str:
    return json.dumps(
        [{"name": r["name"], "result": r["result"]} for r in results], ensure_ascii=False
    )

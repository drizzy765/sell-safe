"""Parse Nigerian price hints from Instagram captions."""

from __future__ import annotations

import re

_DM_PRICE = re.compile(
    r"\b(dm\s+for\s+price|inbox\s+for\s+price|price\s+on\s+request|ask\s+for\s+price)\b",
    re.IGNORECASE,
)
_NAIRA_SYMBOL = re.compile(r"(?:₦|NGN|naira)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)
_K_SUFFIX = re.compile(r"(?:₦|NGN|naira)?\s*(\d+(?:\.\d+)?)\s*k\b", re.IGNORECASE)
_BARE_THOUSANDS = re.compile(r"\b(\d{1,3}(?:,\d{3})+)\b")


def parse_caption_price_ngn(caption: str) -> tuple[int | None, list[str]]:
    """Return (price_ngn, flags). price_ngn is whole naira, not kobo."""
    text = (caption or "").strip()
    flags: list[str] = []
    if not text:
        flags.append("missing_price")
        return None, flags
    if _DM_PRICE.search(text):
        flags.append("dm_for_price")
        return None, flags

    for match in _NAIRA_SYMBOL.finditer(text):
        naira = _to_naira(match.group(1))
        if naira is not None:
            return naira, flags

    for match in _K_SUFFIX.finditer(text):
        raw = float(match.group(1))
        naira = int(round(raw * 1000))
        if naira > 0:
            return naira, flags

    # Last resort: comma-formatted thousands that look like prices.
    for match in _BARE_THOUSANDS.finditer(text):
        naira = _to_naira(match.group(1))
        if naira is not None and naira >= 500:
            return naira, flags

    flags.append("missing_price")
    return None, flags


def _to_naira(raw: str) -> int | None:
    cleaned = raw.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    naira = int(round(value))
    return naira if naira > 0 else None

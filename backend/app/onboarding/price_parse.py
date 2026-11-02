"""Parse Nigerian price hints from Instagram captions and Drive filenames."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

_DM_PRICE = re.compile(
    r"\b(dm\s+for\s+price|inbox\s+for\s+price|price\s+on\s+request|ask\s+for\s+price)\b",
    re.IGNORECASE,
)
_NAIRA_SYMBOL = re.compile(r"(?:₦|NGN|naira)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)
_K_SUFFIX = re.compile(r"(?:₦|NGN|naira)?\s*(\d+(?:\.\d+)?)\s*k\b", re.IGNORECASE)
_BARE_THOUSANDS = re.compile(r"\b(\d{1,3}(?:,\d{3})+)\b")
# Drive catalog convention: "Honey beans - NGN 6000.jpg"
_FILENAME_PRICE = re.compile(
    r"^(?P<name>.+?)\s*[-–—]\s*(?:NGN|₦)\s*(?P<price>[\d,]+(?:\.\d+)?)\s*$",
    re.IGNORECASE,
)
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


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


def parse_filename_product(filename: str) -> tuple[str | None, int | None]:
    """Parse `<Name> - NGN <price>.jpg` → (name, price_ngn).

    Returns (None, None) when the filename does not match the convention.
    """
    stem = PurePosixPath((filename or "").strip()).stem
    if not stem:
        return None, None
    match = _FILENAME_PRICE.match(stem)
    if not match:
        return None, None
    name = re.sub(r"\s+", " ", match.group("name")).strip()
    price = _to_naira(match.group("price"))
    if not name or price is None:
        return None, None
    return name, price


def is_catalog_image_filename(filename: str) -> bool:
    ext = PurePosixPath((filename or "").strip()).suffix.lower()
    return ext in _IMAGE_EXTS


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

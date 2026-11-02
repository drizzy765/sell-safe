"""Official Sell-Safe Instagram page: marketing/connect only — never catalog sales.

DMs to the company page (sellsafe.ng) must not answer with a shop catalog.
Catalog, pricing, and payment flows run only on seller accounts that connected
via Instagram Login OAuth (e.g. sellsafe.testshop.ng).
"""

from __future__ import annotations

from app.agent.templates import official_connect_reply


def parse_official_ig_account_ids(raw: str | None) -> frozenset[str]:
    """Comma/space-separated IG account ids for the official Sell-Safe page."""
    text = (raw or "").strip()
    if not text:
        return frozenset()
    parts: list[str] = []
    for chunk in text.replace(";", ",").split(","):
        for piece in chunk.split():
            value = piece.strip()
            if value:
                parts.append(value)
    return frozenset(parts)


def is_official_ig_account(account_id: str | None, *, official_ids: frozenset[str]) -> bool:
    aid = str(account_id or "").strip()
    return bool(aid) and aid in official_ids


def official_ids_from_settings(settings: object) -> frozenset[str]:
    raw = getattr(settings, "sellsafe_official_ig_account_ids", "") or ""
    return parse_official_ig_account_ids(str(raw))


def site_url_from_settings(settings: object) -> str:
    """Public marketing site for Connect CTA (not the ephemeral tunnel)."""
    for attr in ("sellsafe_site_url", "web_base_url", "app_base_url"):
        value = str(getattr(settings, attr, "") or "").strip().rstrip("/")
        if value:
            return value
    return "https://sellsafe.ng"


def connect_reply_for_settings(settings: object) -> str:
    return official_connect_reply(site_url_from_settings(settings))

"""Feature 3 — seller dashboard summary (catalog + demo inbox/stats)."""

from __future__ import annotations

from fastapi import APIRouter, Header, Request

from app.api.internal.catalog_onboarding import _drafts, _shop_media
from app.api.internal.onboarding import SESSION_HEADER, _require_session, _shops

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_DEMO_CHATS = [
    {
        "id": "demo-1",
        "channel": "instagram",
        "buyer": "@kemi_lagos",
        "language": "pcm",
        "preview": "Abeg how much be the black bag?",
        "reply": "The black bag na ₦12,500. You want make I hold am?",
        "at": "today 10:14",
        "demo": True,
    },
    {
        "id": "demo-2",
        "channel": "instagram",
        "buyer": "@tunde",
        "language": "yo",
        "preview": "Ṣé ẹ ní àpótí pupa?",
        "reply": "Bẹ́ẹ̀ni — red box wà. Ó jẹ́ ₦8,000.",
        "at": "today 11:02",
        "demo": True,
    },
]

_DEMO_RECEIPTS = [
    {
        "id": "demo-r1",
        "verdict": "SUSPICIOUS",
        "amount_ngn": 20000,
        "reasons": ["edited amount", "no matching bank webhook"],
        "demo": True,
    },
    {
        "id": "demo-r2",
        "verdict": "CONFIRMED",
        "amount_ngn": 12500,
        "reasons": ["Paystack webhook matched order ref"],
        "demo": True,
    },
]


@router.get("/summary")
def dashboard_summary(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session_id, session = _require_session(request, x_ig_session)
    shop = _shops(request).get_by_ig_account(session.account_id)
    products = _drafts(request).list_products(shop.id) if shop else []
    drafts = _drafts(request).list_drafts(shop.id) if shop else []
    media = _shop_media(request).list_for_shop(shop.id) if shop else []
    empty = not products and not drafts

    return {
        "shop": shop.public_dict() if shop else None,
        "stats": {
            "chats_today": 2 if empty else max(len(_DEMO_CHATS), 1),
            "orders": 1 if empty else len(products),
            "naira_verified": 12500 if empty else sum((p.price_ngn or 0) for p in products),
            "fakes_caught": 1 if empty else 0,
            "avg_reply_seconds": 4,
            "demo": empty,
        },
        "products": [p.public_dict() for p in products],
        "drafts": [d.public_dict() for d in drafts],
        "media": [m.public_dict() for m in media],
        "inbox": _DEMO_CHATS,
        "receipts": _DEMO_RECEIPTS,
        "demo_mode": empty,
    }

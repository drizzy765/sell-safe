"""Feature 1 — Confirm your shop from the connected Instagram session."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.channels.instagram.profile import (
    IgProfile,
    InstagramProfileClient,
    InstagramProfileError,
)
from app.db.instagram_session_store import InstagramSessionStore
from app.db.shop_store import MemoryShopStore, ShopMedia, ShopProfile, ShopStore

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

SESSION_HEADER = "X-IG-Session"
ALLOWED_LANGS = {"en", "pcm", "yo"}


class ShopUpdateRequest(BaseModel):
    name: str | None = None
    handle: str | None = None
    bio: str | None = None
    category: str | None = None
    website: str | None = None
    phone: str | None = None
    location: str | None = None
    delivery_areas: str | None = None
    bank_name: str | None = None
    account_name: str | None = None
    account_number: str | None = None
    languages: list[str] | None = None
    opening_hours: str | None = None
    delivery_policy: str | None = None
    confirm: bool = Field(
        default=False,
        description="When true, marks the shop confirmed and ready for catalog setup.",
    )


def _sessions(request: Request) -> InstagramSessionStore:
    current = getattr(request.app.state, "instagram_sessions", None)
    if current is None:
        current = InstagramSessionStore()
        request.app.state.instagram_sessions = current
    return current


def _shops(request: Request) -> ShopStore:
    current = getattr(request.app.state, "shops", None)
    if current is None:
        current = MemoryShopStore()
        request.app.state.shops = current
    return current


def _session_id(request: Request, x_ig_session: str | None) -> str:
    header = (x_ig_session or "").strip()
    if header:
        return header
    return request.cookies.get("sellsafe_ig_session", "").strip()


def _require_session(request: Request, x_ig_session: str | None):
    session_id = _session_id(request, x_ig_session)
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Connect Instagram first.",
        )
    session = _sessions(request).get(session_id)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Instagram session expired. Disconnect and connect again.",
        )
    return session_id, session


def _profile_client(request: Request) -> InstagramProfileClient:
    return InstagramProfileClient(
        request.app.state.settings,
        transport=getattr(request.app.state, "transport", None),
    )


def _clean_handle(value: str) -> str:
    handle = (value or "").strip().lstrip("@")
    return "" if not handle or handle.isdigit() else handle


def _shop_from_profile(profile: IgProfile, existing: ShopProfile | None) -> ShopProfile:
    media = [
        ShopMedia(
            id=item.id,
            caption=item.caption,
            media_url=item.media_url,
            media_type=item.media_type,
            timestamp=item.timestamp,
            permalink=item.permalink,
            thumbnail_url=item.thumbnail_url,
        )
        for item in profile.media
    ]
    handle = _clean_handle(profile.username)
    display_name = (profile.name or "").strip()
    if display_name.isdigit():
        display_name = ""
    if existing is None:
        return ShopProfile(
            id=MemoryShopStore.new_id(),
            ig_account_id=profile.account_id,
            handle=handle,
            name=display_name or handle,
            bio=profile.biography,
            logo_url=profile.profile_picture_url,
            category=profile.category or profile.account_type,
            website=profile.website,
            followers_count=profile.followers_count,
            account_type=profile.account_type,
            recent_media=media,
        )
    if handle:
        existing.handle = handle
    if not existing.name:
        existing.name = display_name or handle
    if not existing.bio:
        existing.bio = profile.biography
    if not existing.logo_url:
        existing.logo_url = profile.profile_picture_url
    if not existing.category:
        existing.category = profile.category or profile.account_type
    if not existing.website:
        existing.website = profile.website
    existing.followers_count = profile.followers_count
    existing.account_type = profile.account_type or existing.account_type
    existing.recent_media = media or existing.recent_media
    return existing


def _link_seller(request: Request, shop: ShopProfile) -> None:
    store = getattr(request.app.state, "store", None)
    if store is None:
        return
    ensure = getattr(store, "ensure_seller", None)
    if ensure is None:
        return
    seller_id = ensure(shop.ig_account_id, channel="instagram")
    details = getattr(store, "seller_details", None)
    if isinstance(details, dict):
        row = details.setdefault(seller_id, {"id": seller_id})
        row["business_name"] = shop.name or shop.handle
        row["name"] = shop.name or shop.handle
        row["ig_handle"] = shop.handle
        row["shop_id"] = shop.id
        if shop.languages:
            langs = getattr(store, "seller_languages", None)
            if isinstance(langs, dict):
                langs[seller_id] = shop.languages[0]


@router.get("/shop")
async def get_shop(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
    refresh: bool = False,
) -> dict:
    """Return the seller shop draft, fetching Instagram profile when needed."""
    _session_id_value, session = _require_session(request, x_ig_session)
    shops = _shops(request)
    existing = shops.get_by_ig_account(session.account_id)

    # Fix shops that were seeded with the numeric IG user id as name/handle.
    if existing is not None:
        dirty = (existing.handle or "").isdigit() or (existing.name or "").isdigit()
        if dirty:
            existing.handle = "" if (existing.handle or "").isdigit() else existing.handle
            existing.name = "" if (existing.name or "").isdigit() else existing.name
            shops.upsert(existing)

    if existing is not None and existing.confirmed and not refresh:
        return {"shop": existing.public_dict(), "needs_reconnect": False}

    if existing is None or refresh or not existing.logo_url or not existing.handle:
        try:
            profile = await _profile_client(request).fetch_shop_profile(
                session.access_token,
                fallback_account_id=session.account_id,
                fallback_username=session.username,
            )
            shop = _shop_from_profile(profile, existing)
            shops.upsert(shop)
            _link_seller(request, shop)
            return {"shop": shop.public_dict(), "needs_reconnect": False}
        except InstagramProfileError as exc:
            if existing is not None:
                return {
                    "shop": existing.public_dict(),
                    "needs_reconnect": False,
                    "warning": str(exc),
                }
            # Always open Confirm Shop from the OAuth session if Graph enrich fails.
            # Meta often returns "Unsupported request - method type: get" for non-testers
            # or until long-lived exchange succeeds; that must not block onboarding.
            if session.account_id:
                raw_handle = (session.username or "").strip().lstrip("@")
                # Never treat the numeric IG user id as the shop name/handle.
                handle = "" if (not raw_handle or raw_handle.isdigit()) else raw_handle
                shop = ShopProfile(
                    id=MemoryShopStore.new_id(),
                    ig_account_id=session.account_id,
                    handle=handle,
                    name="",  # seller fills this — don't prefill with an id
                )
                shops.upsert(shop)
                _link_seller(request, shop)
                warning = str(exc)
                if "Unsupported request" in warning:
                    warning = (
                        "Instagram did not return the public profile yet "
                        "(accept the Instagram Tester invite, or reconnect "
                        "after a backend restart). Enter your shop name below "
                        "and continue."
                    )
                return {
                    "shop": shop.public_dict(),
                    "needs_reconnect": False,
                    "warning": warning,
                }
            raise HTTPException(status_code=401, detail=str(exc)) from None

    return {"shop": existing.public_dict(), "needs_reconnect": False}


@router.patch("/shop")
async def patch_shop(
    body: ShopUpdateRequest,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    """Save Confirm-your-shop edits. confirm=true advances to catalog setup."""
    _session_id_value, session = _require_session(request, x_ig_session)
    shops = _shops(request)
    shop = shops.get_by_ig_account(session.account_id)
    if shop is None:
        raise HTTPException(
            status_code=404,
            detail="Shop not found. Open Confirm your shop again to load Instagram.",
        )

    for field in (
        "name",
        "bio",
        "category",
        "website",
        "phone",
        "location",
        "delivery_areas",
        "bank_name",
        "account_name",
        "opening_hours",
        "delivery_policy",
    ):
        value = getattr(body, field)
        if value is not None:
            setattr(shop, field, value.strip() if isinstance(value, str) else value)

    if body.handle is not None:
        cleaned = _clean_handle(body.handle)
        if cleaned:
            shop.handle = cleaned
            # Keep OAuth session label aligned with the shop the seller confirmed.
            if not (session.username or "").strip():
                session.username = cleaned

    if body.account_number is not None:
        cleaned = "".join(ch for ch in body.account_number if ch.isdigit())
        shop.account_number = cleaned

    if body.languages is not None:
        langs = [lang for lang in body.languages if lang in ALLOWED_LANGS]
        shop.languages = langs or ["en"]

    if body.confirm:
        if not (shop.name or "").strip():
            raise HTTPException(status_code=422, detail="Shop name is required.")
        shop.confirmed = True

    shops.upsert(shop)
    _link_seller(request, shop)
    return {
        "shop": shop.public_dict(),
        "next": "/onboarding/catalog" if shop.confirmed else None,
        "skip_to": "/dashboard?tab=catalog" if shop.confirmed else None,
    }

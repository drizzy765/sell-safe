"""Feature 2 — catalog import + draft review APIs."""

from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.internal.onboarding import (
    SESSION_HEADER,
    _link_seller,
    _profile_client,
    _require_session,
    _shops,
)
from app.channels.instagram.profile import InstagramProfileError
from app.db.catalog_store import MemoryCatalogStore
from app.db.onboarding_catalog_store import MemoryOnboardingCatalogStore, OnboardingCatalogStore
from app.db.shop_media_store import MemoryShopMediaStore, ShopMediaAsset
from app.db.shop_store import ShopMedia
from app.llm.factory import build_provider
from app.onboarding.catalog_pipeline import (
    apply_shop_flags,
    build_draft,
    fetch_image_bytes,
    publish_to_catalog_store,
)

router = APIRouter(prefix="/api/onboarding/catalog", tags=["onboarding-catalog"])


class InstagramImportRequest(BaseModel):
    media_ids: list[str] = Field(default_factory=list, min_length=1)


class DraftPatchRequest(BaseModel):
    name: str | None = None
    price_ngn: int | None = None
    category: str | None = None
    description: str | None = None
    variants: list[str] | None = None
    stock_status: str | None = None
    clear_flags: bool = False


class ApproveRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)


class UploadItem(BaseModel):
    """Base64 image upload (web-friendly)."""

    filename: str = "upload.jpg"
    content_base64: str
    caption: str = ""


class UploadRequest(BaseModel):
    items: list[UploadItem] = Field(default_factory=list, min_length=1)


class DriveImportRequest(BaseModel):
    folder_url: str = Field(..., min_length=8)


def _drafts(request: Request) -> OnboardingCatalogStore:
    current = getattr(request.app.state, "onboarding_catalog", None)
    if current is None:
        current = MemoryOnboardingCatalogStore()
        request.app.state.onboarding_catalog = current
    return current


def _catalog(request: Request):
    current = getattr(request.app.state, "catalog", None)
    if current is None:
        current = MemoryCatalogStore()
        request.app.state.catalog = current
    return current


def _shop_media(request: Request) -> MemoryShopMediaStore:
    current = getattr(request.app.state, "shop_media", None)
    if current is None:
        current = MemoryShopMediaStore()
        request.app.state.shop_media = current
    return current


def _is_video(filename: str, content_type: str = "") -> bool:
    lower = (filename or "").lower()
    ctype = (content_type or "").lower()
    return ctype.startswith("video/") or lower.endswith((".mp4", ".mov", ".webm", ".m4v", ".avi"))


def _provider(request: Request):
    current = getattr(request.app.state, "provider", None)
    if current is not None:
        return current
    try:
        current = build_provider(request.app.state.settings)
        request.app.state.provider = current
        return current
    except Exception:
        return None


def _seller_id(request: Request, ig_account_id: str) -> str:
    store = getattr(request.app.state, "store", None)
    if store is not None and hasattr(store, "ensure_seller"):
        return str(store.ensure_seller(ig_account_id, channel="instagram"))
    return ig_account_id


def _require_shop(request: Request, x_ig_session: str | None):
    _session_id, session = _require_session(request, x_ig_session)
    shop = _shops(request).get_by_ig_account(session.account_id)
    if shop is None:
        raise HTTPException(
            status_code=404,
            detail="Confirm your shop first at /onboarding/shop.",
        )
    return session, shop


async def _refresh_media(request: Request, session, shop):
    profile = await _profile_client(request).fetch_shop_profile(session.access_token)
    shop.recent_media = [
        ShopMedia(
            id=m.id,
            caption=m.caption,
            media_url=m.media_url,
            media_type=m.media_type,
            timestamp=m.timestamp,
            permalink=m.permalink,
            thumbnail_url=m.thumbnail_url,
        )
        for m in profile.media
    ]
    _shops(request).upsert(shop)
    _link_seller(request, shop)
    return shop


@router.get("/media")
async def list_media(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    session, shop = _require_shop(request, x_ig_session)
    warning = None
    if not shop.recent_media:
        try:
            shop = await _refresh_media(request, session, shop)
        except InstagramProfileError as exc:
            # Do not block Step 2 — seller can upload, use Drive, or skip to dashboard.
            warning = str(exc)
            if "Unsupported request" in warning:
                warning = (
                    "Instagram posts are unavailable for this login right now. "
                    "Upload photos/videos, paste a Drive link, or skip to the dashboard catalog."
                )
    return {
        "shop_id": shop.id,
        "handle": shop.handle,
        "media": [
            {
                "id": m.id,
                "caption": m.caption,
                "media_url": m.media_url,
                "thumbnail_url": m.thumbnail_url or m.media_url,
                "permalink": m.permalink,
                "media_type": m.media_type,
            }
            for m in shop.recent_media
        ],
        "warning": warning,
        "skip_to": "/dashboard",
    }


@router.post("/import/instagram")
async def import_instagram(
    body: InstagramImportRequest,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    session, shop = _require_shop(request, x_ig_session)
    media_by_id = {m.id: m for m in shop.recent_media}
    missing = [mid for mid in body.media_ids if mid not in media_by_id]
    if missing:
        try:
            shop = await _refresh_media(request, session, shop)
        except InstagramProfileError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from None
        media_by_id = {m.id: m for m in shop.recent_media}
        missing = [mid for mid in body.media_ids if mid not in media_by_id]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown media ids: {', '.join(missing[:5])}",
            )

    seller_id = _seller_id(request, shop.ig_account_id)
    provider = _provider(request)
    store = _drafts(request)
    transport = getattr(request.app.state, "transport", None)
    created: list[dict] = []
    errors: list[dict] = []

    for media_id in body.media_ids:
        item = media_by_id[media_id]
        url = item.media_url or item.thumbnail_url
        if not url:
            errors.append({"media_id": media_id, "detail": "No image URL on this post."})
            continue
        try:
            image = await fetch_image_bytes(url, transport=transport)
            draft = await build_draft(
                shop_id=shop.id,
                seller_id=seller_id,
                image=image,
                image_url=url,
                caption=item.caption or "",
                source="instagram",
                source_ref=media_id,
                provider=provider,
                store=store,
            )
            created.append(draft.public_dict())
        except Exception as exc:
            errors.append({"media_id": media_id, "detail": str(exc)[:180]})

    return {"drafts": created, "errors": errors, "review": "/onboarding/catalog/review"}


@router.post("/import/upload")
async def import_upload(
    body: UploadRequest,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    provider = _provider(request)
    store = _drafts(request)
    media_store = _shop_media(request)
    created: list[dict] = []
    media_saved: list[dict] = []
    errors: list[dict] = []

    for index, item in enumerate(body.items):
        try:
            raw = item.content_base64
            mime = "application/octet-stream"
            if "," in raw and raw.strip().startswith("data:"):
                header, raw = raw.split(",", 1)
                if ";" in header:
                    mime = header[5:].split(";", 1)[0] or mime
            blob = base64.b64decode(raw, validate=False)
            if not blob:
                raise ValueError("Empty file")
            source_ref = f"upload:{item.filename}:{index}"
            data_url = f"data:{mime};base64,{base64.b64encode(blob).decode('ascii')}"
            kind = "video" if _is_video(item.filename, mime) else "image"
            asset = media_store.add(
                ShopMediaAsset(
                    id=MemoryShopMediaStore.new_id(),
                    shop_id=shop.id,
                    kind=kind,
                    filename=item.filename,
                    content_type=mime,
                    url=data_url,
                    caption=item.caption or "",
                    source="upload",
                    source_ref=source_ref,
                )
            )
            media_saved.append(asset.public_dict())

            if kind == "video":
                # Videos go to the shop shelf; drafting stays image/Muse for now.
                continue

            draft = await build_draft(
                shop_id=shop.id,
                seller_id=seller_id,
                image=blob,
                image_url=data_url,
                caption=item.caption or "",
                source="upload",
                source_ref=source_ref,
                provider=provider,
                store=store,
            )
            draft.image_urls = [data_url]
            store.upsert(draft)
            created.append(draft.public_dict())
        except (ValueError, binascii.Error) as exc:
            errors.append({"filename": item.filename, "detail": str(exc)[:180]})
        except Exception as exc:
            errors.append({"filename": item.filename, "detail": str(exc)[:180]})

    return {
        "drafts": created,
        "media": media_saved,
        "errors": errors,
        "review": "/onboarding/catalog/review" if created else "/dashboard?tab=catalog",
    }


@router.post("/import/drive")
async def import_drive(
    body: DriveImportRequest,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    """Accept a Google Drive folder/file URL.

    Full Drive fetch lands via MCP/`drive.readonly` next. For now we validate the
    URL shape, stash it on the shop media shelf as a pending source, and point
    the seller at the dashboard catalog.
    """
    _session, shop = _require_shop(request, x_ig_session)
    url = body.folder_url.strip()
    if "drive.google.com" not in url and "docs.google.com" not in url:
        raise HTTPException(
            status_code=422,
            detail="Paste a Google Drive folder or file link (drive.google.com).",
        )
    media_store = _shop_media(request)
    asset = media_store.add(
        ShopMediaAsset(
            id=MemoryShopMediaStore.new_id(),
            shop_id=shop.id,
            kind="image",
            filename="Google Drive link",
            content_type="text/uri-list",
            url=url,
            caption="Pending Drive import — MCP/Drive sync will pull images & videos",
            source="drive",
            source_ref=url,
        )
    )
    return {
        "accepted": True,
        "media": [asset.public_dict()],
        "detail": (
            "Drive link saved to your shop. Full image/video pull via Drive MCP "
            "is next — open Dashboard → Catalog to manage media."
        ),
        "next": "/dashboard?tab=catalog",
    }


@router.get("/shelf")
def list_shelf(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    rows = _shop_media(request).list_for_shop(shop.id)
    return {"media": [r.public_dict() for r in rows]}


@router.delete("/shelf/{asset_id}")
def delete_shelf_item(
    asset_id: str,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    ok = _shop_media(request).delete(shop.id, asset_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Media not found.")
    return {"ok": True}


@router.get("/drafts")
def list_drafts(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    drafts = _drafts(request).list_drafts(shop.id)
    return {"drafts": [d.public_dict() for d in drafts]}


@router.get("/products")
def list_products(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    products = _drafts(request).list_products(shop.id)
    return {"products": [p.public_dict() for p in products]}


@router.patch("/drafts/{draft_id}")
def patch_draft(
    draft_id: str,
    body: DraftPatchRequest,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    store = _drafts(request)
    draft = store.get(draft_id)
    if draft is None or draft.shop_id != shop.id or draft.status != "draft":
        raise HTTPException(status_code=404, detail="Draft not found.")

    if body.name is not None:
        draft.name = body.name.strip()
    if body.price_ngn is not None:
        draft.price_ngn = body.price_ngn if body.price_ngn > 0 else None
        draft.flags = [f for f in draft.flags if f not in {"missing_price", "dm_for_price"}]
        if draft.price_ngn is None:
            draft.flags.append("missing_price")
    if body.category is not None:
        draft.category = body.category.strip()
    if body.description is not None:
        draft.description = body.description.strip()
    if body.variants is not None:
        draft.variants = body.variants
    if body.stock_status is not None:
        draft.stock_status = body.stock_status.strip() or "unknown"
    if body.clear_flags:
        draft.flags = []

    peers = store.list_drafts(shop.id) + store.list_products(shop.id)
    draft = apply_shop_flags(peers, draft)
    store.upsert(draft)
    return {"draft": draft.public_dict()}


@router.delete("/drafts/{draft_id}")
def delete_draft(
    draft_id: str,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    store = _drafts(request)
    draft = store.get(draft_id)
    if draft is None or draft.shop_id != shop.id:
        raise HTTPException(status_code=404, detail="Draft not found.")
    store.delete(draft_id)
    return {"ok": True}


@router.post("/drafts/approve")
def approve_drafts(
    body: ApproveRequest,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    store = _drafts(request)
    catalog = _catalog(request)
    approved: list[dict] = []
    skipped: list[dict] = []

    ids = body.ids or [d.id for d in store.list_drafts(shop.id)]
    for draft_id in ids:
        draft = store.get(draft_id)
        if draft is None or draft.shop_id != shop.id or draft.status != "draft":
            skipped.append({"id": draft_id, "detail": "not found"})
            continue
        if draft.price_ngn is None:
            skipped.append({"id": draft_id, "detail": "missing price"})
            continue
        draft.status = "approved"
        store.upsert(draft)
        publish_to_catalog_store(catalog, draft)
        approved.append(draft.public_dict())

    return {"approved": approved, "skipped": skipped}

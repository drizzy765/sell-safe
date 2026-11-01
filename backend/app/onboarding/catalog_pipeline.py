"""Shared Feature 2 pipeline: image (+ caption) → draft product."""

from __future__ import annotations

import re
from statistics import median

import httpx

from app.agent.catalog import AskSeller, extract_catalog
from app.db.onboarding_catalog_store import (
    MemoryOnboardingCatalogStore,
    OnboardingCatalogStore,
    ProductDraft,
)
from app.llm.base import LLMProvider
from app.onboarding.price_parse import parse_caption_price_ngn


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def apply_shop_flags(drafts: list[ProductDraft], candidate: ProductDraft) -> ProductDraft:
    """Flag duplicates and price outliers against existing drafts/products."""
    flags = list(candidate.flags)
    peers = [d for d in drafts if d.id != candidate.id and d.status in {"draft", "approved"}]
    for peer in peers:
        if _norm_name(peer.name) and _norm_name(peer.name) == _norm_name(candidate.name):
            if "duplicate" not in flags:
                flags.append("duplicate")
            break

    prices = [d.price_ngn for d in peers if isinstance(d.price_ngn, int) and d.price_ngn > 0]
    if candidate.price_ngn and prices:
        mid = median(prices)
        if mid > 0 and (candidate.price_ngn >= mid * 5 or candidate.price_ngn <= max(mid / 5, 1)):
            if "price_outlier" not in flags:
                flags.append("price_outlier")

    candidate.flags = flags
    return candidate


async def fetch_image_bytes(
    url: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> bytes:
    async with httpx.AsyncClient(
        transport=transport, timeout=30.0, follow_redirects=True
    ) as client:
        response = await client.get(url)
    if response.status_code >= 400:
        raise ValueError("Could not download product image.")
    return response.content


async def build_draft(
    *,
    shop_id: str,
    seller_id: str,
    image: bytes,
    image_url: str,
    caption: str,
    source: str,
    source_ref: str,
    provider: LLMProvider | None,
    store: OnboardingCatalogStore,
) -> ProductDraft:
    caption_price, caption_flags = parse_caption_price_ngn(caption)
    name = ""
    description = (caption or "").strip()[:500]
    category = ""
    confidence = 0.35
    variants: list[str] = []
    price_ngn = caption_price
    flags = list(caption_flags)

    if provider is not None and image:
        try:
            extracted = await extract_catalog(provider, image)
        except Exception:
            extracted = AskSeller()
        if not isinstance(extracted, AskSeller):
            name = extracted.name.strip()
            description = extracted.description.strip() or description
            category = extracted.category.strip()
            confidence = float(extracted.confidence)
            variants = list(extracted.colors or [])
            if extracted.suggested_price_kobo is not None and price_ngn is None:
                price_ngn = max(int(extracted.suggested_price_kobo) // 100, 0) or None
                if price_ngn is None and "missing_price" not in flags:
                    flags.append("missing_price")
            elif price_ngn is None and "missing_price" not in flags:
                flags.append("missing_price")

    if not name:
        # Caption-first title when vision is unavailable.
        first_line = (caption or "").strip().splitlines()[0] if caption else ""
        name = first_line[:80] if first_line else f"Product from {source}"
        confidence = min(confidence, 0.4)

    if price_ngn is None and "missing_price" not in flags and "dm_for_price" not in flags:
        flags.append("missing_price")

    existing = None
    if isinstance(store, MemoryOnboardingCatalogStore):
        existing = store.find_by_source(shop_id, source, source_ref)

    draft = ProductDraft(
        id=existing.id if existing else MemoryOnboardingCatalogStore.new_id(),
        shop_id=shop_id,
        seller_id=seller_id,
        name=name,
        price_ngn=price_ngn,
        category=category,
        description=description,
        variants=variants,
        image_urls=[image_url] if image_url else [],
        stock_status="in_stock",
        source=source,
        source_ref=source_ref,
        confidence=confidence,
        flags=flags,
        status="draft",
        caption=caption or "",
    )
    peers = store.list_drafts(shop_id) + store.list_products(shop_id)
    draft = apply_shop_flags(peers, draft)
    return store.upsert(draft)


def publish_to_catalog_store(catalog: object, draft: ProductDraft) -> dict | None:
    """Write an approved draft into the runtime CatalogStore used by buyer chat."""
    if draft.price_ngn is None:
        return None
    products = getattr(catalog, "products", None)
    if not isinstance(products, list):
        # Supabase path not wired for onboarding approve in this slice.
        return {
            "id": draft.id,
            "seller_id": draft.seller_id,
            "name": draft.name,
            "description": draft.description,
            "price_kobo": draft.price_ngn * 100,
            "image_path": draft.image_urls[0] if draft.image_urls else "",
            "category": draft.category,
        }
    # Replace existing product with same source_ref if present.
    products[:] = [
        p
        for p in products
        if not (
            p.get("seller_id") == draft.seller_id
            and p.get("source_ref") == draft.source_ref
            and p.get("source") == draft.source
        )
    ]
    product = {
        "id": draft.id,
        "seller_id": draft.seller_id,
        "name": draft.name,
        "description": draft.description,
        "price_kobo": int(draft.price_ngn) * 100,
        "image_path": draft.image_urls[0] if draft.image_urls else "",
        "category": draft.category,
        "source": draft.source,
        "source_ref": draft.source_ref,
        "active": True,
    }
    products.append(product)
    return product

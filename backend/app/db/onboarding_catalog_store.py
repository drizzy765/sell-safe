"""Shop-scoped product drafts for Feature 2 onboarding import."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from threading import Lock
from uuid import uuid4


@dataclass
class ProductDraft:
    id: str
    shop_id: str
    seller_id: str
    name: str
    price_ngn: int | None
    category: str = ""
    description: str = ""
    variants: list[str] = field(default_factory=list)
    image_urls: list[str] = field(default_factory=list)
    stock_status: str = "unknown"
    source: str = "instagram"
    source_ref: str = ""
    confidence: float = 0.0
    flags: list[str] = field(default_factory=list)
    status: str = "draft"  # draft | approved | deleted
    caption: str = ""

    def public_dict(self) -> dict:
        return asdict(self)


class OnboardingCatalogStore:
    def list_drafts(self, shop_id: str) -> list[ProductDraft]: ...

    def list_products(self, shop_id: str) -> list[ProductDraft]: ...

    def get(self, draft_id: str) -> ProductDraft | None: ...

    def upsert(self, draft: ProductDraft) -> ProductDraft: ...

    def delete(self, draft_id: str) -> bool: ...


class MemoryOnboardingCatalogStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, ProductDraft] = {}

    def list_drafts(self, shop_id: str) -> list[ProductDraft]:
        with self._lock:
            rows = [
                deepcopy(item)
                for item in self._items.values()
                if item.shop_id == shop_id and item.status == "draft"
            ]
        return sorted(rows, key=lambda row: row.name.lower())

    def list_products(self, shop_id: str) -> list[ProductDraft]:
        with self._lock:
            rows = [
                deepcopy(item)
                for item in self._items.values()
                if item.shop_id == shop_id and item.status == "approved"
            ]
        return sorted(rows, key=lambda row: row.name.lower())

    def get(self, draft_id: str) -> ProductDraft | None:
        with self._lock:
            item = self._items.get(draft_id)
            return deepcopy(item) if item else None

    def upsert(self, draft: ProductDraft) -> ProductDraft:
        with self._lock:
            if not draft.id:
                draft.id = str(uuid4())
            self._items[draft.id] = deepcopy(draft)
            return deepcopy(draft)

    def delete(self, draft_id: str) -> bool:
        with self._lock:
            item = self._items.get(draft_id)
            if item is None:
                return False
            item.status = "deleted"
            self._items[draft_id] = item
            return True

    def find_by_source(self, shop_id: str, source: str, source_ref: str) -> ProductDraft | None:
        with self._lock:
            for item in self._items.values():
                if (
                    item.shop_id == shop_id
                    and item.source == source
                    and item.source_ref == source_ref
                    and item.status != "deleted"
                ):
                    return deepcopy(item)
        return None

    @staticmethod
    def new_id() -> str:
        return str(uuid4())

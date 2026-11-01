"""Per-shop media shelf (images + videos) for Feature 2/3 uploads."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from threading import Lock
from uuid import uuid4


@dataclass
class ShopMediaAsset:
    id: str
    shop_id: str
    kind: str  # image | video
    filename: str
    content_type: str
    # data URL or remote URL — hackathon local store; never log full data URLs
    url: str
    caption: str = ""
    source: str = "upload"  # upload | drive | instagram
    source_ref: str = ""

    def public_dict(self) -> dict:
        data = asdict(self)
        # Keep preview URL for UI; callers must not log it.
        return data


class MemoryShopMediaStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, ShopMediaAsset] = {}

    def list_for_shop(self, shop_id: str) -> list[ShopMediaAsset]:
        with self._lock:
            rows = [deepcopy(v) for v in self._items.values() if v.shop_id == shop_id]
        return sorted(rows, key=lambda r: r.filename.lower())

    def add(self, asset: ShopMediaAsset) -> ShopMediaAsset:
        with self._lock:
            if not asset.id:
                asset.id = str(uuid4())
            self._items[asset.id] = deepcopy(asset)
            return deepcopy(asset)

    def delete(self, shop_id: str, asset_id: str) -> bool:
        with self._lock:
            item = self._items.get(asset_id)
            if item is None or item.shop_id != shop_id:
                return False
            self._items.pop(asset_id, None)
            return True

    @staticmethod
    def new_id() -> str:
        return str(uuid4())

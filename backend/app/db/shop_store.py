"""In-memory shop profiles created from Instagram Login (Feature 1)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from threading import Lock
from uuid import uuid4


def mask_account_number(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) <= 4:
        return "*" * len(digits) if digits else ""
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


@dataclass
class ShopMedia:
    id: str
    caption: str = ""
    media_url: str = ""
    media_type: str = ""
    timestamp: str = ""
    permalink: str = ""
    thumbnail_url: str = ""


@dataclass
class ShopProfile:
    id: str
    ig_account_id: str
    handle: str
    name: str = ""
    bio: str = ""
    logo_url: str = ""
    category: str = ""
    website: str = ""
    followers_count: int | None = None
    account_type: str = ""
    phone: str = ""
    location: str = ""
    delivery_areas: str = ""
    bank_name: str = ""
    account_name: str = ""
    account_number: str = ""
    languages: list[str] = field(default_factory=lambda: ["en"])
    opening_hours: str = ""
    delivery_policy: str = ""
    recent_media: list[ShopMedia] = field(default_factory=list)
    confirmed: bool = False

    def public_dict(self) -> dict:
        data = asdict(self)
        raw = data.pop("account_number", "")
        data["account_number_masked"] = mask_account_number(str(raw or ""))
        data["account_number_set"] = bool(str(raw or "").strip())
        return data


class ShopStore:
    def get_by_ig_account(self, ig_account_id: str) -> ShopProfile | None: ...

    def get(self, shop_id: str) -> ShopProfile | None: ...

    def upsert(self, shop: ShopProfile) -> ShopProfile: ...


class MemoryShopStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._by_id: dict[str, ShopProfile] = {}
        self._by_ig: dict[str, str] = {}

    def get_by_ig_account(self, ig_account_id: str) -> ShopProfile | None:
        with self._lock:
            shop_id = self._by_ig.get(ig_account_id)
            if not shop_id:
                return None
            shop = self._by_id.get(shop_id)
            return deepcopy(shop) if shop else None

    def get(self, shop_id: str) -> ShopProfile | None:
        with self._lock:
            shop = self._by_id.get(shop_id)
            return deepcopy(shop) if shop else None

    def upsert(self, shop: ShopProfile) -> ShopProfile:
        with self._lock:
            if not shop.id:
                shop.id = str(uuid4())
            self._by_id[shop.id] = deepcopy(shop)
            self._by_ig[shop.ig_account_id] = shop.id
            return deepcopy(shop)

    @staticmethod
    def new_id() -> str:
        return str(uuid4())

"""Catalog drafts and confirmed products."""

from typing import Protocol
from uuid import uuid4


class CatalogStore(Protocol):
    def save_draft(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        image_path: str,
        extraction: dict,
    ) -> None: ...

    def pending_draft(self, seller_id: str, buyer_id: str) -> dict | None: ...

    def save_product(self, seller_id: str, buyer_id: str, price_kobo: int) -> dict | None: ...

    def search_products(self, seller_id: str, query: str, limit: int = 5) -> list[dict]: ...

    def get_product(self, seller_id: str, product_id: str) -> dict | None: ...


class MemoryCatalogStore:
    def __init__(self) -> None:
        self.drafts: list[dict] = []
        self.products: list[dict] = []

    def save_draft(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        image_path: str,
        extraction: dict,
    ) -> None:
        self.drafts = [
            draft for draft in self.drafts if not _is_pending(draft, seller_id, buyer_id)
        ]
        self.drafts.append(
            {
                "seller_id": seller_id,
                "buyer_id": buyer_id,
                "image_path": image_path,
                "extraction": extraction,
                "status": "pending",
            }
        )

    def pending_draft(self, seller_id: str, buyer_id: str) -> dict | None:
        for draft in self.drafts:
            if _is_pending(draft, seller_id, buyer_id):
                return draft
        return None

    def save_product(self, seller_id: str, buyer_id: str, price_kobo: int) -> dict | None:
        draft = self.pending_draft(seller_id, buyer_id)
        if draft is None:
            return None
        extraction = draft["extraction"]
        product = {
            "id": str(uuid4()),
            "seller_id": seller_id,
            "name": extraction["name"],
            "description": extraction.get("description"),
            "price_kobo": price_kobo,
            "image_path": draft["image_path"],
        }
        self.products.append(product)
        draft["status"] = "saved"
        return product

    def search_products(self, seller_id: str, query: str, limit: int = 5) -> list[dict]:
        q = query.lower()
        return [
            p
            for p in self.products
            if p["seller_id"] == seller_id
            and (q in p["name"].lower() or q in (p.get("description") or "").lower())
        ][:limit]

    def get_product(self, seller_id: str, product_id: str) -> dict | None:
        for p in self.products:
            if p["id"] == product_id and p["seller_id"] == seller_id:
                return p
        return None


def _is_pending(draft: dict, seller_id: str, buyer_id: str) -> bool:
    return (
        draft["seller_id"] == seller_id
        and draft["buyer_id"] == buyer_id
        and draft["status"] == "pending"
    )


class SupabaseCatalogStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def save_draft(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        image_path: str,
        extraction: dict,
    ) -> None:
        found = self.pending_draft(seller_id, buyer_id)
        payload = {
            "image_path": image_path,
            "extraction": extraction,
            "status": "pending",
        }
        if found:
            (self._client.table("catalog_drafts").update(payload).eq("id", found["id"]).execute())
            return
        payload["seller_id"] = seller_id
        payload["buyer_id"] = buyer_id
        self._client.table("catalog_drafts").insert(payload).execute()

    def pending_draft(self, seller_id: str, buyer_id: str) -> dict | None:
        found = (
            self._client.table("catalog_drafts")
            .select("id,image_path,extraction,status,seller_id,buyer_id")
            .eq("seller_id", seller_id)
            .eq("buyer_id", buyer_id)
            .eq("status", "pending")
            .limit(1)
            .execute()
        )
        rows = found.data or []
        return rows[0] if rows else None

    def save_product(self, seller_id: str, buyer_id: str, price_kobo: int) -> dict | None:
        draft = self.pending_draft(seller_id, buyer_id)
        if draft is None:
            return None
        extraction = draft["extraction"] or {}
        created = (
            self._client.table("products")
            .insert(
                {
                    "seller_id": seller_id,
                    "name": extraction["name"],
                    "description": extraction.get("description"),
                    "price_kobo": price_kobo,
                    "image_path": draft["image_path"],
                    "currency": "NGN",
                    "stock": 0,
                    "active": True,
                }
            )
            .execute()
        )
        (
            self._client.table("catalog_drafts")
            .update({"status": "saved"})
            .eq("id", draft["id"])
            .execute()
        )
        return created.data[0]

    def search_products(self, seller_id: str, query: str, limit: int = 5) -> list[dict]:
        found = (
            self._client.table("products")
            .select("id, name, description, price_kobo, stock, image_path")
            .eq("seller_id", seller_id)
            .eq("active", True)
            .ilike("name", f"%{query}%")
            .limit(limit)
            .execute()
        )
        return found.data or []

    def get_product(self, seller_id: str, product_id: str) -> dict | None:
        found = (
            self._client.table("products")
            .select("id, name, description, price_kobo, stock, image_path")
            .eq("seller_id", seller_id)
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        return rows[0] if rows else None


def build_catalog_store(settings: object) -> SupabaseCatalogStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabaseCatalogStore(create_client(url, key))

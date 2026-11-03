"""Seller login accounts linked to Instagram shops.

A seller logs in with Supabase Auth (magic link). Their auth user id is
linked to the Instagram account they connected, so after a browser or
server restart the dashboard can restore the saved Instagram session
without a fresh Instagram OAuth round-trip. Tests use the memory store.
"""

from typing import Protocol


class SellerAccountStore(Protocol):
    def link(self, *, user_id: str, email: str, ig_account_id: str, username: str) -> dict: ...

    def get(self, user_id: str) -> dict | None: ...


class MemorySellerAccountStore:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def link(self, *, user_id: str, email: str, ig_account_id: str, username: str) -> dict:
        row = {
            "user_id": user_id,
            "email": email,
            "ig_account_id": ig_account_id,
            "username": username,
        }
        self.rows[user_id] = row
        return dict(row)

    def get(self, user_id: str) -> dict | None:
        row = self.rows.get(user_id)
        return dict(row) if row else None


class SupabaseSellerAccountStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def link(self, *, user_id: str, email: str, ig_account_id: str, username: str) -> dict:
        row = {
            "user_id": user_id,
            "email": email,
            "ig_account_id": ig_account_id,
            "username": username,
        }
        created = self._client.table("seller_accounts").upsert(row).execute()
        rows = created.data or []
        return rows[0] if rows else row

    def get(self, user_id: str) -> dict | None:
        result = self._client.table("seller_accounts").select("*").eq("user_id", user_id).execute()
        rows = result.data or []
        return rows[0] if rows else None


def build_seller_account_store(settings: object) -> SellerAccountStore | None:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return SupabaseSellerAccountStore(create_client(url, key))
    except Exception:
        return None

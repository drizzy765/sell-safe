"""Order persistence. Money is integer kobo."""

import random
from typing import Protocol
from uuid import uuid4


class OrderStore(Protocol):
    def get_open_order(self, seller_id: str, buyer_id: str) -> dict | None: ...

    def create_order(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        items: list[dict],
        total_kobo: int,
    ) -> dict: ...

    def get_order_by_ref(self, ref: str) -> dict | None: ...

    def update_order_status(self, ref: str, status: str) -> dict | None: ...

    def cancel_order(self, ref: str) -> dict | None: ...

    def increment_reminder_count(self, ref: str) -> dict | None: ...

    def list_pending_payment_orders(self) -> list[dict]: ...


class MemoryOrderStore:
    def __init__(self) -> None:
        self.orders: list[dict] = []
        self._ref_counters: dict[str, int] = {}

    def get_open_order(self, seller_id: str, buyer_id: str) -> dict | None:
        for order in reversed(self.orders):
            if (
                order["seller_id"] == seller_id
                and order["buyer_id"] == buyer_id
                and order["status"] in ("draft", "awaiting_payment")
            ):
                return order
        return None

    def create_order(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        items: list[dict],
        total_kobo: int,
    ) -> dict:
        order = {
            "id": str(uuid4()),
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "ref": self._next_ref(seller_id),
            "items": items,
            "total_kobo": total_kobo,
            "status": "awaiting_payment",
            "reminder_count": 0,
            "expires_at": None,
        }
        self.orders.append(order)
        return order

    def get_order_by_ref(self, ref: str) -> dict | None:
        for order in self.orders:
            if order["ref"] == ref:
                return order
        return None

    def update_order_status(self, ref: str, status: str) -> dict | None:
        order = self.get_order_by_ref(ref)
        if order is None:
            return None
        order["status"] = status
        return order

    def cancel_order(self, ref: str) -> dict | None:
        return self.update_order_status(ref, "cancelled")

    def increment_reminder_count(self, ref: str) -> dict | None:
        order = self.get_order_by_ref(ref)
        if order is None:
            return None
        order["reminder_count"] = int(order.get("reminder_count", 0)) + 1
        return order

    def list_pending_payment_orders(self) -> list[dict]:
        return [
            order
            for order in self.orders
            if order.get("status") in ("awaiting_payment", "payment_review")
        ]

    def _next_ref(self, seller_id: str) -> str:
        counter = self._ref_counters.get(seller_id, 1000) + 1
        self._ref_counters[seller_id] = counter
        return f"SS-{counter}"


class SupabaseOrderStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def get_open_order(self, seller_id: str, buyer_id: str) -> dict | None:
        found = (
            self._client.table("orders")
            .select("id, ref, items, total_kobo, status")
            .eq("seller_id", seller_id)
            .eq("buyer_id", buyer_id)
            .in_("status", ["draft", "awaiting_payment"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        return rows[0] if rows else None

    def create_order(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        items: list[dict],
        total_kobo: int,
    ) -> dict:
        ref = self._unique_ref()
        created = (
            self._client.table("orders")
            .insert(
                {
                    "seller_id": seller_id,
                    "buyer_id": buyer_id,
                    "ref": ref,
                    "items": items,
                    "total_kobo": total_kobo,
                    "status": "awaiting_payment",
                }
            )
            .execute()
        )
        return created.data[0]

    def get_order_by_ref(self, ref: str) -> dict | None:
        found = (
            self._client.table("orders")
            .select("id, ref, items, total_kobo, status")
            .eq("ref", ref)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        return rows[0] if rows else None

    def update_order_status(self, ref: str, status: str) -> dict | None:
        order = self.get_order_by_ref(ref)
        if order is None:
            return None
        updated = (
            self._client.table("orders").update({"status": status}).eq("id", order["id"]).execute()
        )
        return updated.data[0]

    def cancel_order(self, ref: str) -> dict | None:
        return self.update_order_status(ref, "cancelled")

    def increment_reminder_count(self, ref: str) -> dict | None:
        order = self.get_order_by_ref(ref)
        if order is None:
            return None
        updated = (
            self._client.table("orders")
            .update({"reminder_count": int(order.get("reminder_count") or 0) + 1})
            .eq("id", order["id"])
            .execute()
        )
        return updated.data[0]

    def list_pending_payment_orders(self) -> list[dict]:
        found = (
            self._client.table("orders")
            .select("*")
            .in_("status", ["awaiting_payment", "payment_review"])
            .execute()
        )
        return found.data or []

    def _unique_ref(self) -> str:
        for _ in range(10):
            ref = f"SS-{random.randint(1000, 9999)}"
            if self.get_order_by_ref(ref) is None:
                return ref
        return f"SS-{uuid4().hex[:8].upper()}"


def build_order_store(settings: object) -> SupabaseOrderStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabaseOrderStore(create_client(url, key))

"""Seller, buyer, and inbound-message persistence for the echo bot.

The webhook dedupes on messages.external_msg_id. Tests use MemoryEchoStore.
SupabaseEchoStore is what the process uses when no store is injected.
"""

from typing import Protocol
from uuid import uuid4


class EchoStore(Protocol):
    def ensure_seller(self, phone_number_id: str) -> str: ...

    def ensure_buyer(
        self,
        channel: str,
        external_id: str,
        display_name: str | None = None,
    ) -> str: ...

    def save_inbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        message_type: str,
        text: str | None,
    ) -> bool: ...


class MemoryEchoStore:
    """In-memory store for tests. A repeated external_msg_id returns False."""

    def __init__(self) -> None:
        self.sellers: dict[str, str] = {}
        self.buyers: dict[tuple[str, str], str] = {}
        self.messages: dict[str, dict[str, str | None]] = {}

    def ensure_seller(self, phone_number_id: str) -> str:
        if phone_number_id not in self.sellers:
            self.sellers[phone_number_id] = str(uuid4())
        return self.sellers[phone_number_id]

    def ensure_buyer(
        self,
        channel: str,
        external_id: str,
        display_name: str | None = None,
    ) -> str:
        key = (channel, external_id)
        if key not in self.buyers:
            self.buyers[key] = str(uuid4())
        return self.buyers[key]

    def save_inbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        message_type: str,
        text: str | None,
    ) -> bool:
        if external_msg_id in self.messages:
            return False
        self.messages[external_msg_id] = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "type": message_type,
            "text": text,
        }
        return True


def _is_duplicate(exc: BaseException) -> bool:
    code = getattr(exc, "code", None)
    return str(code) == "23505" or "23505" in str(exc)


class SupabaseEchoStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def ensure_seller(self, phone_number_id: str) -> str:
        found = (
            self._client.table("sellers")
            .select("id")
            .contains("channel_ids", {"whatsapp": phone_number_id})
            .limit(1)
            .execute()
        )
        rows = found.data or []
        if rows:
            return str(rows[0]["id"])
        created = (
            self._client.table("sellers")
            .insert(
                {
                    "name": "Shop",
                    "business_name": "Shop",
                    "channel_ids": {"whatsapp": phone_number_id},
                    "default_language": "en",
                    "active": True,
                }
            )
            .execute()
        )
        return str(created.data[0]["id"])

    def ensure_buyer(
        self,
        channel: str,
        external_id: str,
        display_name: str | None = None,
    ) -> str:
        found = (
            self._client.table("buyers")
            .select("id")
            .eq("channel", channel)
            .eq("external_id", external_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        if rows:
            return str(rows[0]["id"])
        payload: dict[str, str] = {"channel": channel, "external_id": external_id}
        if display_name:
            payload["display_name"] = display_name
        created = self._client.table("buyers").insert(payload).execute()
        return str(created.data[0]["id"])

    def save_inbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        message_type: str,
        text: str | None,
    ) -> bool:
        row: dict[str, str | None] = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "direction": "in",
            "external_msg_id": external_msg_id,
            "type": message_type,
            "text": text,
        }
        try:
            self._client.table("messages").insert(row).execute()
        except Exception as exc:
            if _is_duplicate(exc):
                return False
            raise
        return True


def build_store(settings: object) -> SupabaseEchoStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabaseEchoStore(create_client(url, key))

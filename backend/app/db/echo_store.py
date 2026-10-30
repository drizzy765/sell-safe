"""Seller, buyer, and inbound-message persistence for the echo bot.

The webhook dedupes on messages.external_msg_id. Tests use MemoryEchoStore.
SupabaseEchoStore is what the process uses when no store is injected.
"""

from typing import Protocol
from uuid import uuid4


class EchoStore(Protocol):
    def ensure_seller(self, phone_number_id: str, *, channel: str = "whatsapp") -> str: ...

    def ensure_buyer(
        self,
        channel: str,
        external_id: str,
        display_name: str | None = None,
    ) -> str: ...

    def get_seller_language(self, seller_id: str) -> str: ...

    def get_seller_by_channel(
        self,
        channel: str,
        external_id: str,
    ) -> dict | None: ...

    def save_inbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        message_type: str,
        text: str | None,
        intent: str | None = None,
        language: str | None = None,
        transcript: str | None = None,
        asr_confidence: float | None = None,
    ) -> bool: ...

    def save_outbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        text: str,
    ) -> None: ...

    def recent_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 8,
    ) -> list[dict]: ...

    def get_seller(self, seller_id: str) -> dict | None: ...

    def set_crypto_wallet(self, seller_id: str, address: str, network: str) -> None: ...

    def get_buyer_by_id(self, buyer_id: str) -> dict | None: ...


class MemoryEchoStore:
    """In-memory store for tests. A repeated external_msg_id returns False."""

    def __init__(self) -> None:
        self.sellers: dict[str, str] = {}
        self.seller_languages: dict[str, str] = {"default": "en"}
        self.seller_details: dict[str, dict] = {}
        self.seller_channels: dict[tuple[str, str], str] = {}
        self.buyers: dict[tuple[str, str], str] = {}
        self.buyer_by_id: dict[str, dict[str, str]] = {}
        self.messages: dict[str, dict[str, str | float | None]] = {}

    def ensure_seller(self, phone_number_id: str, *, channel: str = "whatsapp") -> str:
        if phone_number_id not in self.sellers:
            seller_id = str(uuid4())
            self.sellers[phone_number_id] = seller_id
            self.seller_languages[seller_id] = "en"
            self.seller_details[seller_id] = {
                "id": seller_id,
                "business_name": "Shop",
                "virtual_account": {"last4": "1234", "bank": "Test Bank"},
            }
        seller_id = self.sellers[phone_number_id]
        self.seller_channels[(channel, phone_number_id)] = seller_id
        return seller_id

    def register_channel(
        self,
        seller_id: str,
        channel: str,
        external_id: str,
    ) -> None:
        self.seller_channels[(channel, external_id)] = seller_id

    def get_seller_by_channel(
        self,
        channel: str,
        external_id: str,
    ) -> dict | None:
        seller_id = self.seller_channels.get((channel, external_id))
        if seller_id is None:
            return None
        return self.seller_details.get(seller_id)

    def ensure_buyer(
        self,
        channel: str,
        external_id: str,
        display_name: str | None = None,
    ) -> str:
        key = (channel, external_id)
        if key not in self.buyers:
            buyer_id = str(uuid4())
            self.buyers[key] = buyer_id
            self.buyer_by_id[buyer_id] = {
                "id": buyer_id,
                "channel": channel,
                "external_id": external_id,
            }
        return self.buyers[key]

    def get_seller_language(self, seller_id: str) -> str:
        return self.seller_languages.get(seller_id, "en")

    def save_inbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        message_type: str,
        text: str | None,
        intent: str | None = None,
        language: str | None = None,
        transcript: str | None = None,
        asr_confidence: float | None = None,
    ) -> bool:
        if external_msg_id in self.messages:
            # Voice path re-saves ASR fields onto the original audio row.
            if transcript is not None:
                existing = self.messages[external_msg_id]
                existing["transcript"] = transcript
                existing["language"] = language
                existing["asr_confidence"] = asr_confidence
                if text is not None:
                    existing["text"] = text
                return True
            return False
        self.messages[external_msg_id] = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "direction": "in",
            "type": message_type,
            "text": text,
            "intent": intent,
            "language": language,
            "transcript": transcript,
            "asr_confidence": asr_confidence,
        }
        return True

    def save_outbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        text: str,
    ) -> None:
        self.messages[external_msg_id] = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "direction": "out",
            "type": "text",
            "text": text,
        }

    def recent_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 8,
    ) -> list[dict]:
        rows = [
            msg
            for msg in self.messages.values()
            if msg.get("seller_id") == seller_id and msg.get("buyer_id") == buyer_id
        ]
        rows.sort(
            key=lambda m: str(m.get("created_at", "") or m.get("external_msg_id", "")), reverse=True
        )
        return rows[-limit:]

    def get_seller(self, seller_id: str) -> dict | None:
        return self.seller_details.get(seller_id)

    def set_crypto_wallet(self, seller_id: str, address: str, network: str) -> None:
        details = self.seller_details.setdefault(seller_id, {"id": seller_id})
        details["crypto_wallet"] = address
        details["crypto_network"] = network

    def get_buyer_by_id(self, buyer_id: str) -> dict | None:
        return self.buyer_by_id.get(buyer_id)


def _is_duplicate(exc: BaseException) -> bool:
    code = getattr(exc, "code", None)
    return str(code) == "23505" or "23505" in str(exc)


class SupabaseEchoStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def ensure_seller(self, phone_number_id: str, *, channel: str = "whatsapp") -> str:
        found = (
            self._client.table("sellers")
            .select("id")
            .contains("channel_ids", {channel: phone_number_id})
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
                    "channel_ids": {channel: phone_number_id},
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

    def get_seller_language(self, seller_id: str) -> str:
        found = (
            self._client.table("sellers")
            .select("default_language")
            .eq("id", seller_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        if rows:
            return str(rows[0].get("default_language") or "en")
        return "en"

    def get_seller_by_channel(
        self,
        channel: str,
        external_id: str,
    ) -> dict | None:
        found = (
            self._client.table("sellers")
            .select("id, business_name, virtual_account")
            .contains("channel_ids", {channel: external_id})
            .limit(1)
            .execute()
        )
        rows = found.data or []
        return rows[0] if rows else None

    def save_inbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        message_type: str,
        text: str | None,
        intent: str | None = None,
        language: str | None = None,
        transcript: str | None = None,
        asr_confidence: float | None = None,
    ) -> bool:
        row: dict[str, str | float | None] = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "direction": "in",
            "external_msg_id": external_msg_id,
            "type": message_type,
            "text": text,
            "intent": intent,
            "language": language,
            "transcript": transcript,
            "asr_confidence": asr_confidence,
        }
        try:
            self._client.table("messages").insert(row).execute()
        except Exception as exc:
            if _is_duplicate(exc):
                if transcript is not None:
                    self._client.table("messages").update(
                        {
                            "transcript": transcript,
                            "language": language,
                            "asr_confidence": asr_confidence,
                            **({"text": text} if text is not None else {}),
                        }
                    ).eq("external_msg_id", external_msg_id).execute()
                    return True
                return False
            raise
        return True

    def save_outbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        text: str,
    ) -> None:
        row: dict[str, str | None] = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "direction": "out",
            "external_msg_id": external_msg_id,
            "type": "text",
            "text": text,
        }
        self._client.table("messages").insert(row).execute()

    def recent_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 8,
    ) -> list[dict]:
        found = (
            self._client.table("messages")
            .select("direction, type, text, intent, language, created_at")
            .eq("seller_id", seller_id)
            .eq("buyer_id", buyer_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = found.data or []
        return list(reversed(rows))

    def get_seller(self, seller_id: str) -> dict | None:
        found = (
            self._client.table("sellers")
            .select("id, business_name, virtual_account, settings")
            .eq("id", seller_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        if not rows:
            return None
        row = dict(rows[0])
        settings = row.get("settings") or {}
        if isinstance(settings, dict):
            if settings.get("crypto_wallet"):
                row["crypto_wallet"] = settings["crypto_wallet"]
            if settings.get("crypto_network"):
                row["crypto_network"] = settings["crypto_network"]
        return row

    def set_crypto_wallet(self, seller_id: str, address: str, network: str) -> None:
        found = (
            self._client.table("sellers")
            .select("settings")
            .eq("id", seller_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        settings = {}
        if rows and isinstance(rows[0].get("settings"), dict):
            settings = dict(rows[0]["settings"])
        settings["crypto_wallet"] = address
        settings["crypto_network"] = network
        self._client.table("sellers").update({"settings": settings}).eq("id", seller_id).execute()

    def get_buyer_by_id(self, buyer_id: str) -> dict | None:
        found = (
            self._client.table("buyers")
            .select("id, channel, external_id")
            .eq("id", buyer_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        return rows[0] if rows else None


def build_store(settings: object) -> SupabaseEchoStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabaseEchoStore(create_client(url, key))

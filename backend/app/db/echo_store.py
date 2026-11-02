"""Seller, buyer, and inbound-message persistence for the echo bot.

The webhook dedupes on messages.external_msg_id. Tests use MemoryEchoStore.
SupabaseEchoStore is what the process uses when no store is injected.
"""

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


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
        media_path: str | None = None,
    ) -> bool: ...

    def save_outbound(
        self,
        *,
        seller_id: str,
        buyer_id: str,
        channel: str,
        external_msg_id: str,
        text: str,
        message_type: str = "text",
        media_path: str | None = None,
        meta: dict | None = None,
    ) -> None: ...

    def recent_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 8,
    ) -> list[dict]: ...

    def list_conversations(self, seller_id: str, limit: int = 50) -> list[dict]: ...

    def list_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 100,
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
        self.messages: dict[str, dict] = {}

    def ensure_seller(self, phone_number_id: str, *, channel: str = "whatsapp") -> str:
        if phone_number_id not in self.sellers:
            # Instagram Login / Messaging: keep seller_id == IG account id so
            # onboarding catalog rows match webhook recipient ids.
            seller_id = phone_number_id if channel == "instagram" else str(uuid4())
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
                "display_name": display_name or "",
            }
        elif display_name:
            self.buyer_by_id[self.buyers[key]]["display_name"] = display_name
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
        media_path: str | None = None,
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
            "id": external_msg_id,
            "external_msg_id": external_msg_id,
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
            "media_path": media_path,
            "meta": None,
            "created_at": _utc_now(),
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
        message_type: str = "text",
        media_path: str | None = None,
        meta: dict | None = None,
    ) -> None:
        self.messages[external_msg_id] = {
            "id": external_msg_id,
            "external_msg_id": external_msg_id,
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "direction": "out",
            "type": message_type,
            "text": text,
            "media_path": media_path,
            "meta": meta,
            "created_at": _utc_now(),
        }

    def recent_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 8,
    ) -> list[dict]:
        return self.list_messages(seller_id, buyer_id, limit=limit)

    def list_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 100,
    ) -> list[dict]:
        rows = [
            msg
            for msg in self.messages.values()
            if msg.get("seller_id") == seller_id and msg.get("buyer_id") == buyer_id
        ]
        rows.sort(key=lambda m: str(m.get("created_at") or m.get("external_msg_id") or ""))
        return rows[-limit:]

    def list_conversations(self, seller_id: str, limit: int = 50) -> list[dict]:
        latest: dict[str, dict] = {}
        for msg in self.messages.values():
            if msg.get("seller_id") != seller_id:
                continue
            buyer_id = str(msg.get("buyer_id") or "")
            if not buyer_id:
                continue
            prev = latest.get(buyer_id)
            created = str(msg.get("created_at") or "")
            if prev is None or created >= str(prev.get("created_at") or ""):
                latest[buyer_id] = msg
        conversations: list[dict] = []
        for buyer_id, msg in latest.items():
            buyer = self.get_buyer_by_id(buyer_id) or {}
            preview = str(msg.get("text") or "")
            if msg.get("type") == "image" and not preview:
                preview = "Sent an image"
            elif msg.get("type") == "audio" and not preview:
                preview = "Voice note"
            conversations.append(
                {
                    "id": buyer_id,
                    "buyer_id": buyer_id,
                    "channel": msg.get("channel") or buyer.get("channel") or "instagram",
                    "buyer_external_id": buyer.get("external_id") or "",
                    "buyer": buyer.get("display_name") or buyer.get("external_id") or buyer_id[:8],
                    "preview": preview,
                    "direction": msg.get("direction"),
                    "language": msg.get("language") or "",
                    "at": msg.get("created_at"),
                    "created_at": msg.get("created_at"),
                }
            )
        conversations.sort(key=lambda c: str(c.get("created_at") or ""), reverse=True)
        return conversations[:limit]

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
        media_path: str | None = None,
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
            "media_path": media_path,
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
        message_type: str = "text",
        media_path: str | None = None,
        meta: dict | None = None,
    ) -> None:
        row: dict[str, str | None] = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "channel": channel,
            "direction": "out",
            "external_msg_id": external_msg_id,
            "type": message_type,
            "text": text,
            "media_path": media_path,
        }
        # meta is memory-only for now; column may not exist on Supabase.
        _ = meta
        self._client.table("messages").insert(row).execute()

    def recent_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 8,
    ) -> list[dict]:
        return self.list_messages(seller_id, buyer_id, limit=limit)

    def list_messages(
        self,
        seller_id: str,
        buyer_id: str,
        limit: int = 100,
    ) -> list[dict]:
        found = (
            self._client.table("messages")
            .select(
                "external_msg_id, direction, type, text, intent, language, media_path, created_at"
            )
            .eq("seller_id", seller_id)
            .eq("buyer_id", buyer_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = found.data or []
        out = list(reversed(rows))
        for row in out:
            row["id"] = row.get("external_msg_id") or row.get("id")
        return out

    def list_conversations(self, seller_id: str, limit: int = 50) -> list[dict]:
        found = (
            self._client.table("messages")
            .select("buyer_id, channel, direction, type, text, language, created_at")
            .eq("seller_id", seller_id)
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        rows = found.data or []
        latest: dict[str, dict] = {}
        for msg in rows:
            buyer_id = str(msg.get("buyer_id") or "")
            if buyer_id and buyer_id not in latest:
                latest[buyer_id] = msg
        conversations: list[dict] = []
        for buyer_id, msg in latest.items():
            buyer = self.get_buyer_by_id(buyer_id) or {}
            preview = str(msg.get("text") or "")
            if msg.get("type") == "image" and not preview:
                preview = "Sent an image"
            conversations.append(
                {
                    "id": buyer_id,
                    "buyer_id": buyer_id,
                    "channel": msg.get("channel") or buyer.get("channel") or "instagram",
                    "buyer_external_id": buyer.get("external_id") or "",
                    "buyer": buyer.get("display_name") or buyer.get("external_id") or buyer_id[:8],
                    "preview": preview,
                    "direction": msg.get("direction"),
                    "language": msg.get("language") or "",
                    "at": msg.get("created_at"),
                    "created_at": msg.get("created_at"),
                }
            )
        conversations.sort(key=lambda c: str(c.get("created_at") or ""), reverse=True)
        return conversations[:limit]

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
            self._client.table("sellers").select("settings").eq("id", seller_id).limit(1).execute()
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
            .select("id, channel, external_id, display_name")
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

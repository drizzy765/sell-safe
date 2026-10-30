"""WhatsApp waitlist persistence.

The phone number is stored so we can message the seller when WhatsApp unblocks.
Tests use MemoryWaitlistStore. SupabaseWaitlistStore is used when Supabase is configured.
"""

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


class DuplicateWaitlistError(Exception):
    """The phone number is already on the waitlist."""

    def __init__(self, phone_number: str) -> None:
        self.phone_number = phone_number
        super().__init__("phone number already on the waitlist")


class WaitlistStore(Protocol):
    def add(self, phone_number: str) -> dict: ...


class MemoryWaitlistStore:
    """In-memory store for tests. A repeated phone number raises DuplicateWaitlistError."""

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, phone_number: str) -> dict:
        if any(row["phone_number"] == phone_number for row in self.rows):
            raise DuplicateWaitlistError(phone_number)
        row = {
            "id": str(uuid4()),
            "phone_number": phone_number,
            "created_at": datetime.now(UTC).isoformat(),
            "notified_at": None,
        }
        self.rows.append(row)
        return row


def _is_duplicate(exc: BaseException) -> bool:
    code = getattr(exc, "code", None)
    return str(code) == "23505" or "23505" in str(exc)


class SupabaseWaitlistStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def add(self, phone_number: str) -> dict:
        try:
            created = (
                self._client.table("whatsapp_waitlist")
                .insert({"phone_number": phone_number})
                .execute()
            )
        except Exception as exc:
            if _is_duplicate(exc):
                raise DuplicateWaitlistError(phone_number) from exc
            raise
        rows = created.data or []
        if not rows:
            raise RuntimeError("waitlist insert returned no row")
        return rows[0]


def build_waitlist_store(settings: object) -> SupabaseWaitlistStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabaseWaitlistStore(create_client(url, key))

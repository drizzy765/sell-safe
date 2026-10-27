"""Idempotency log for webhook events."""

from typing import Protocol


class WebhookEventStore(Protocol):
    def is_duplicate(self, provider: str, event_id: str) -> bool: ...

    def record(self, provider: str, event_id: str, payload: dict) -> None: ...


class MemoryWebhookEventStore:
    def __init__(self) -> None:
        self.events: set[tuple[str, str]] = set()
        self.payloads: list[dict] = []

    def is_duplicate(self, provider: str, event_id: str) -> bool:
        return (provider, event_id) in self.events

    def record(self, provider: str, event_id: str, payload: dict) -> None:
        self.events.add((provider, event_id))
        self.payloads.append(
            {
                "provider": provider,
                "event_id": event_id,
                "payload": payload,
            }
        )


class SupabaseWebhookEventStore:
    def __init__(self, client: object) -> None:
        self._client = client

    def is_duplicate(self, provider: str, event_id: str) -> bool:
        found = (
            self._client.table("webhook_events")
            .select("id")
            .eq("provider", provider)
            .eq("event_id", event_id)
            .limit(1)
            .execute()
        )
        rows = found.data or []
        return bool(rows)

    def record(self, provider: str, event_id: str, payload: dict) -> None:
        self._client.table("webhook_events").insert(
            {
                "provider": provider,
                "event_id": event_id,
                "payload": payload,
            }
        ).execute()


def build_webhook_event_store(settings: object) -> SupabaseWebhookEventStore:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    if not url or not key:
        raise RuntimeError("Supabase is not configured")
    from supabase import create_client

    return SupabaseWebhookEventStore(create_client(url, key))

"""Buyer payment reminders (max 2). Owned by POST /jobs/reminders."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.agent.templates import buyer_reminder
from app.channels.base import ChannelAdapter
from app.db.echo_store import EchoStore
from app.db.orders import OrderStore
from app.jobs.recheck import MAX_REMINDERS, RECHECK_WINDOW_MINUTES, REMINDER_INTERVAL_MINUTES


class ReminderService:
    """Send at most MAX_REMINDERS buyer reminders for unpaid orders."""

    def __init__(
        self,
        *,
        store: EchoStore,
        order_store: OrderStore,
        channel_adapter: ChannelAdapter,
    ) -> None:
        self._store = store
        self._order_store = order_store
        self._channel_adapter = channel_adapter

    async def run(self, now: datetime | None = None) -> list[dict[str, Any]]:
        if now is None:
            now = datetime.now(tz=UTC)
        actions: list[dict[str, Any]] = []
        for order in self._order_store.list_pending_payment_orders():
            if not self._is_due(order, now):
                continue
            ref = order["ref"]
            count = int(order.get("reminder_count") or 0)
            if count >= MAX_REMINDERS:
                continue
            self._order_store.increment_reminder_count(ref)
            text = buyer_reminder(ref, int(order.get("total_kobo") or 0))
            await self._notify_buyer(order, text)
            actions.append({"ref": ref, "action": "reminder", "count": count + 1})
        return actions

    def _is_due(self, order: dict[str, Any], now: datetime) -> bool:
        count = int(order.get("reminder_count") or 0)
        if count >= MAX_REMINDERS:
            return False
        created = self._created_at(order)
        # First reminder after the recheck window; later ones spaced by interval.
        due_at = created + timedelta(minutes=RECHECK_WINDOW_MINUTES)
        due_at = due_at + timedelta(minutes=REMINDER_INTERVAL_MINUTES * count)
        return now >= due_at

    def _created_at(self, order: dict[str, Any]) -> datetime:
        raw = order.get("created_at")
        if raw:
            try:
                return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.now(tz=UTC) - timedelta(minutes=RECHECK_WINDOW_MINUTES + 1)

    async def _notify_buyer(self, order: dict[str, Any], text: str) -> None:
        buyer = self._store.get_buyer_by_id(order["buyer_id"])
        if buyer is None:
            return
        external_id = buyer.get("external_id")
        if not external_id:
            return
        await self._channel_adapter.send_text(external_id, text)
        self._store.save_outbound(
            seller_id=order["seller_id"],
            buyer_id=order["buyer_id"],
            channel=buyer.get("channel", "whatsapp"),
            external_msg_id=f"out-reminder-{order['ref']}-{datetime.now(tz=UTC).isoformat()}",
            text=text,
        )

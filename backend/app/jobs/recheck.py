"""Recheck pending payments: re-evaluate evidence, send reminders, cancel."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.agent.graph.verify import reevaluate_order_after_webhook
from app.agent.templates import order_cancelled, order_released
from app.channels.base import ChannelAdapter
from app.db.echo_store import EchoStore
from app.db.fraud_store import FraudStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore
from app.decisions.base import JevClient

RECHECK_WINDOW_MINUTES = 30
REMINDER_INTERVAL_MINUTES = 5
MAX_REMINDERS = 2


class RecheckService:
    """Re-run verdicts for pending orders and manage the reminder/cancel window."""

    def __init__(
        self,
        *,
        store: EchoStore,
        order_store: OrderStore,
        payment_store: PaymentStore,
        channel_adapter: ChannelAdapter,
        jev: JevClient | None = None,
        pii_salt: str = "",
        fraud_store: FraudStore | None = None,
    ) -> None:
        self._store = store
        self._order_store = order_store
        self._payment_store = payment_store
        self._channel_adapter = channel_adapter
        self._jev = jev
        self._pii_salt = pii_salt
        self._fraud_store = fraud_store

    async def recheck(self, now: datetime | None = None) -> list[dict[str, Any]]:
        """Run one recheck pass and return a log of actions."""
        if now is None:
            now = datetime.now(tz=UTC)
        actions: list[dict[str, Any]] = []

        for order in self._order_store.list_pending_payment_orders():
            ref = order["ref"]
            payment = self._payment_store.get_payment_for_order(order["id"])
            if payment is None:
                continue

            verdict = self._payment_store.get_latest_verdict(payment["id"])
            if verdict is None:
                continue
            if verdict.get("release_allowed"):
                # Already confirmed; release if not already released.
                if order.get("status") != "released":
                    self._order_store.update_order_status(ref, "paid")
                    await self._notify_buyer(order, order_released(ref))
                    actions.append({"ref": ref, "action": "released"})
                continue

            window_start = self._window_start(order)
            elapsed = now - window_start
            if elapsed < timedelta(minutes=RECHECK_WINDOW_MINUTES):
                # Inside the recheck window: re-evaluate in case new evidence arrived.
                new_verdict = await reevaluate_order_after_webhook(
                    order,
                    store=self._store,
                    order_store=self._order_store,
                    payment_store=self._payment_store,
                    jev=self._jev,
                    pii_salt=self._pii_salt,
                    fraud_store=self._fraud_store,
                )
                if new_verdict and new_verdict.release_allowed:
                    self._order_store.update_order_status(ref, "paid")
                    await self._notify_buyer(order, order_released(ref))
                    actions.append({"ref": ref, "action": "confirmed_by_recheck"})
                continue

            # Outside the recheck window: reminders are owned by /jobs/reminders.
            # Cancel only after the buyer has already received the max reminders.
            reminder_count = int(order.get("reminder_count") or 0)
            if reminder_count < MAX_REMINDERS:
                actions.append(
                    {"ref": ref, "action": "awaiting_reminders", "count": reminder_count}
                )
                continue

            self._order_store.update_order_status(ref, "cancelled")
            await self._notify_buyer(order, order_cancelled(ref))
            actions.append({"ref": ref, "action": "cancelled"})

        return actions

    def _window_start(self, order: dict[str, Any]) -> datetime:
        created_at = order.get("created_at")
        if created_at:
            try:
                return datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
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
            external_msg_id=f"out-recheck-{order['ref']}-{datetime.now(tz=UTC).isoformat()}",
            text=text,
        )

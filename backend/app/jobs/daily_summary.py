"""Daily seller summary: orders, paid, fakes caught, naira saved."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from typing import Any

from app.agent.templates import daily_summary_message
from app.channels.base import ChannelAdapter
from app.db.echo_store import EchoStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore

# WAT is UTC+1 year-round (no DST). Avoid zoneinfo/tzdata so CI works on Windows.
WAT = timezone(timedelta(hours=1))
NAIRA_SAVED_CONFIRM_WINDOW = timedelta(hours=48)


def wat_today(now: datetime | None = None) -> date:
    current = now or datetime.now(tz=UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(WAT).date()


def compute_naira_saved_kobo(
    *,
    orders: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    verdicts_by_payment: dict[str, list[dict[str, Any]]],
    now: datetime | None = None,
) -> int:
    """Sum expected_kobo for SUSPICIOUS/NOT_FOUND with goods held and no CONFIRMED in 48h."""
    if now is None:
        now = datetime.now(tz=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    order_by_id = {o["id"]: o for o in orders}
    payment_by_id = {p["id"]: p for p in payments}
    saved = 0

    for payment_id, rows in verdicts_by_payment.items():
        payment = payment_by_id.get(payment_id)
        if payment is None:
            continue
        order = order_by_id.get(payment["order_id"])
        if order is None:
            continue
        if order.get("status") in ("released", "delivered", "paid"):
            continue

        # Chronological verdicts
        ordered = sorted(rows, key=lambda v: str(v.get("created_at") or v.get("id") or ""))
        fake_at: datetime | None = None
        confirmed_later = False
        for verdict in ordered:
            label = verdict.get("verdict")
            when = _parse_dt(verdict.get("created_at")) or now
            if label in ("SUSPICIOUS", "NOT_FOUND") and fake_at is None:
                fake_at = when
            if fake_at is not None and label == "CONFIRMED":
                if when <= fake_at + NAIRA_SAVED_CONFIRM_WINDOW:
                    confirmed_later = True
                    break
        if fake_at is None or confirmed_later:
            continue
        # Only count once the 48h window has elapsed (or still no confirm and window passed).
        if now < fake_at + NAIRA_SAVED_CONFIRM_WINDOW:
            continue
        saved += int(payment.get("expected_kobo") or 0)
    return saved


def _parse_dt(value: object) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


class DailySummaryService:
    def __init__(
        self,
        *,
        store: EchoStore,
        order_store: OrderStore,
        payment_store: PaymentStore,
        channel_adapter: ChannelAdapter,
        summaries: dict[tuple[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self._store = store
        self._order_store = order_store
        self._payment_store = payment_store
        self._channel_adapter = channel_adapter
        # In-memory upsert store for tests: (seller_id, date_iso) -> row
        self.summaries = summaries if summaries is not None else {}

    async def run(self, now: datetime | None = None) -> list[dict[str, Any]]:
        if now is None:
            now = datetime.now(tz=UTC)
        day = wat_today(now)
        actions: list[dict[str, Any]] = []

        seller_ids = self._seller_ids()
        for seller_id in seller_ids:
            row = self._build_row(seller_id, day, now)
            self.summaries[(seller_id, day.isoformat())] = row
            sent = await self._notify_seller(seller_id, row)
            actions.append({"seller_id": seller_id, "summary": row, "sent": sent})
        return actions

    def summary_for(self, seller_id: str, day: date | None = None) -> dict[str, Any] | None:
        target = day or wat_today()
        return self.summaries.get((seller_id, target.isoformat()))

    def _seller_ids(self) -> list[str]:
        details = getattr(self._store, "seller_details", None)
        if isinstance(details, dict) and details:
            return list(details.keys())
        # Fall back: distinct seller_ids on pending/all orders.
        seen: set[str] = set()
        for order in getattr(self._order_store, "orders", []):
            sid = order.get("seller_id")
            if sid:
                seen.add(str(sid))
        return sorted(seen)

    def _build_row(self, seller_id: str, day: date, now: datetime) -> dict[str, Any]:
        orders = [
            o for o in getattr(self._order_store, "orders", []) if o.get("seller_id") == seller_id
        ]
        payments = list(getattr(self._payment_store, "payments", []))
        seller_order_ids = {o["id"] for o in orders}
        seller_payments = [p for p in payments if p.get("order_id") in seller_order_ids]

        paid_kobo = 0
        fakes_caught = 0
        verdicts_by_payment: dict[str, list[dict[str, Any]]] = {}
        for payment in seller_payments:
            rows = [
                v
                for v in getattr(self._payment_store, "verdicts", [])
                if v.get("payment_id") == payment["id"]
            ]
            if not rows:
                embedded = payment.get("verdict")
                if isinstance(embedded, dict):
                    rows = [embedded]
            verdicts_by_payment[payment["id"]] = rows
            latest = rows[-1] if rows else None
            if latest and latest.get("verdict") == "CONFIRMED":
                paid_kobo += int(payment.get("expected_kobo") or 0)
            if latest and latest.get("verdict") in ("SUSPICIOUS", "NOT_FOUND"):
                fakes_caught += 1

        naira_saved = compute_naira_saved_kobo(
            orders=orders,
            payments=seller_payments,
            verdicts_by_payment=verdicts_by_payment,
            now=now,
        )
        return {
            "seller_id": seller_id,
            "date": day.isoformat(),
            "orders": len(orders),
            "paid_kobo": paid_kobo,
            "fakes_caught": fakes_caught,
            "naira_saved_kobo": naira_saved,
        }

    async def _notify_seller(self, seller_id: str, row: dict[str, Any]) -> bool:
        seller = self._store.get_seller(seller_id)
        if seller is None:
            return False
        # Prefer WhatsApp channel id from seller_channels if present.
        to = self._seller_external_id(seller_id)
        if not to:
            return False
        text = daily_summary_message(
            orders=int(row["orders"]),
            paid_kobo=int(row["paid_kobo"]),
            fakes_caught=int(row["fakes_caught"]),
            naira_saved_kobo=int(row["naira_saved_kobo"]),
        )
        await self._channel_adapter.send_text(to, text)
        return True

    def _seller_external_id(self, seller_id: str) -> str | None:
        channels = getattr(self._store, "seller_channels", None)
        if isinstance(channels, dict):
            for (channel, external_id), sid in channels.items():
                if sid == seller_id and channel == "whatsapp":
                    return str(external_id)
            for (_channel, external_id), sid in channels.items():
                if sid == seller_id:
                    return str(external_id)
        # MemoryEchoStore.sellers maps phone_number_id -> seller_id
        sellers = getattr(self._store, "sellers", None)
        if isinstance(sellers, dict):
            for external_id, sid in sellers.items():
                if sid == seller_id:
                    return str(external_id)
        return None

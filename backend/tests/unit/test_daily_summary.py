"""Naira-saved query and reminder/job auth coverage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.jobs.daily_summary import DailySummaryService, compute_naira_saved_kobo
from app.jobs.recheck import MAX_REMINDERS, RECHECK_WINDOW_MINUTES
from app.jobs.reminders import ReminderService
from app.main import create_app


def test_naira_saved_counts_suspicious_without_later_confirm() -> None:
    now = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
    fake_at = now - timedelta(hours=49)
    orders = [{"id": "o1", "seller_id": "s1", "status": "cancelled"}]
    payments = [{"id": "p1", "order_id": "o1", "expected_kobo": 1_500_000}]
    verdicts = {
        "p1": [
            {
                "verdict": "SUSPICIOUS",
                "created_at": fake_at.isoformat(),
            }
        ]
    }
    assert (
        compute_naira_saved_kobo(
            orders=orders,
            payments=payments,
            verdicts_by_payment=verdicts,
            now=now,
        )
        == 1_500_000
    )


def test_naira_saved_skips_when_confirmed_within_48h() -> None:
    now = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
    fake_at = now - timedelta(hours=49)
    confirm_at = fake_at + timedelta(hours=10)
    orders = [{"id": "o1", "seller_id": "s1", "status": "awaiting_payment"}]
    payments = [{"id": "p1", "order_id": "o1", "expected_kobo": 1_500_000}]
    verdicts = {
        "p1": [
            {"verdict": "SUSPICIOUS", "created_at": fake_at.isoformat()},
            {"verdict": "CONFIRMED", "created_at": confirm_at.isoformat()},
        ]
    }
    assert (
        compute_naira_saved_kobo(
            orders=orders,
            payments=payments,
            verdicts_by_payment=verdicts,
            now=now,
        )
        == 0
    )


def test_naira_saved_skips_released_orders() -> None:
    now = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)
    fake_at = now - timedelta(hours=49)
    orders = [{"id": "o1", "seller_id": "s1", "status": "released"}]
    payments = [{"id": "p1", "order_id": "o1", "expected_kobo": 900_000}]
    verdicts = {"p1": [{"verdict": "SUSPICIOUS", "created_at": fake_at.isoformat()}]}
    assert (
        compute_naira_saved_kobo(
            orders=orders,
            payments=payments,
            verdicts_by_payment=verdicts,
            now=now,
        )
        == 0
    )


@pytest.mark.asyncio
async def test_reminders_cap_at_two() -> None:
    store = MemoryEchoStore()
    orders = MemoryOrderStore()
    seller_id = store.ensure_seller("wa-1")
    buyer_id = store.ensure_buyer("whatsapp", "buyer-1")
    order = orders.create_order(
        seller_id=seller_id,
        buyer_id=buyer_id,
        items=[],
        total_kobo=100_000,
    )
    # Make the order old enough for reminders.
    order["created_at"] = (
        datetime.now(tz=UTC) - timedelta(minutes=RECHECK_WINDOW_MINUTES + 1)
    ).isoformat()

    adapter = AsyncMock()
    adapter.send_text = AsyncMock(return_value="out")
    service = ReminderService(store=store, order_store=orders, channel_adapter=adapter)

    for expected in range(1, MAX_REMINDERS + 1):
        actions = await service.run(now=datetime.now(tz=UTC))
        assert len(actions) == 1
        assert actions[0]["count"] == expected
        # Advance time so the next interval is due.
        order["created_at"] = (
            datetime.now(tz=UTC) - timedelta(minutes=RECHECK_WINDOW_MINUTES + 5 * expected + 1)
        ).isoformat()

    actions = await service.run(now=datetime.now(tz=UTC))
    assert actions == []
    assert order["reminder_count"] == MAX_REMINDERS


@pytest.mark.asyncio
async def test_daily_summary_sends_message() -> None:
    store = MemoryEchoStore()
    orders = MemoryOrderStore()
    payments = MemoryPaymentStore()
    seller_id = store.ensure_seller("wa-1")
    buyer_id = store.ensure_buyer("whatsapp", "buyer-1")
    order = orders.create_order(
        seller_id=seller_id,
        buyer_id=buyer_id,
        items=[],
        total_kobo=1_500_000,
    )
    payment = payments.get_or_create_payment(
        order_id=order["id"], method="bank_transfer", expected_kobo=1_500_000
    )
    payments.save_verdict(
        payment_id=payment["id"],
        verdict="SUSPICIOUS",
        confidence=0.2,
        release_allowed=False,
        reasons=["fake"],
        rule_hits=["R6_blocklist"],
    )
    # Stamp verdict created_at in the past for naira_saved.
    payments.verdicts[-1]["created_at"] = (datetime.now(tz=UTC) - timedelta(hours=50)).isoformat()
    orders.update_order_status(order["ref"], "cancelled")

    adapter = AsyncMock()
    adapter.send_text = AsyncMock(return_value="out")
    service = DailySummaryService(
        store=store,
        order_store=orders,
        payment_store=payments,
        channel_adapter=adapter,
    )
    actions = await service.run(now=datetime.now(tz=UTC))
    assert len(actions) == 1
    assert actions[0]["sent"] is True
    summary = actions[0]["summary"]
    assert summary["orders"] == 1
    assert summary["fakes_caught"] == 1
    assert summary["naira_saved_kobo"] == 1_500_000
    adapter.send_text.assert_awaited()


def test_jobs_require_internal_token() -> None:
    app = create_app(
        Settings(internal_api_token="secret"),
        store=MemoryEchoStore(),
        orders=MemoryOrderStore(),
        payments=MemoryPaymentStore(),
    )
    client = TestClient(app)
    for path in ("/jobs/reminders", "/jobs/daily-summary", "/jobs/recheck"):
        response = client.post(path)
        assert response.status_code == 401

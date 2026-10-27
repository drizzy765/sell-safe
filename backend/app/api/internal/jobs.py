"""Internal cron-style job endpoints."""

from datetime import UTC, date, datetime

from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.config import Settings
from app.db.echo_store import EchoStore, build_store
from app.db.fraud_store import FraudStore, MemoryFraudStore, build_fraud_store
from app.db.orders import OrderStore, build_order_store
from app.db.payments import PaymentStore, build_payment_store
from app.decisions.base import JevClient
from app.decisions.factory import build_jev
from app.jobs.daily_summary import DailySummaryService
from app.jobs.recheck import RecheckService
from app.jobs.reminders import ReminderService

router = APIRouter(prefix="/jobs")


def _require_token(settings: Settings, token: str | None) -> None:
    if not settings.internal_api_token:
        raise HTTPException(status_code=503, detail="internal token not configured")
    if not token:
        raise HTTPException(status_code=401, detail="missing internal token")
    if token != settings.internal_api_token:
        raise HTTPException(status_code=403, detail="invalid internal token")


def _store(request: Request) -> EchoStore:
    current = request.app.state.store
    if current is None:
        current = build_store(request.app.state.settings)
        request.app.state.store = current
    return current


def _orders(request: Request) -> OrderStore:
    current = request.app.state.orders
    if current is None:
        current = build_order_store(request.app.state.settings)
        request.app.state.orders = current
    return current


def _payments(request: Request) -> PaymentStore:
    current = getattr(request.app.state, "payments", None)
    if current is None:
        current = build_payment_store(request.app.state.settings)
        request.app.state.payments = current
    return current


def _jev(request: Request) -> JevClient:
    current = getattr(request.app.state, "jev", None)
    if current is None:
        current = build_jev(request.app.state.settings)
        request.app.state.jev = current
    return current


def _adapter(request: Request) -> WhatsAppAdapter:
    return WhatsAppAdapter(request.app.state.settings, transport=request.app.state.transport)


def _fraud(request: Request) -> FraudStore:
    current = getattr(request.app.state, "fraud", None)
    if current is None:
        settings = request.app.state.settings
        if settings.supabase_url and settings.supabase_service_role_key:
            current = build_fraud_store(settings)
        else:
            current = MemoryFraudStore()
        request.app.state.fraud = current
    return current


def _summary_service(request: Request) -> DailySummaryService:
    current = getattr(request.app.state, "daily_summary_service", None)
    if current is None:
        current = DailySummaryService(
            store=_store(request),
            order_store=_orders(request),
            payment_store=_payments(request),
            channel_adapter=_adapter(request),
        )
        request.app.state.daily_summary_service = current
    return current


@router.post("/recheck")
async def recheck(
    request: Request,
    x_internal_token: str | None = Header(default=None),
) -> dict:
    settings = request.app.state.settings
    _require_token(settings, x_internal_token)

    service = RecheckService(
        store=_store(request),
        order_store=_orders(request),
        payment_store=_payments(request),
        channel_adapter=_adapter(request),
        jev=_jev(request),
        pii_salt=settings.pii_salt,
        fraud_store=_fraud(request),
    )
    actions = await service.recheck(now=datetime.now(tz=UTC))
    return {"ok": True, "actions": actions}


@router.post("/reminders")
async def reminders(
    request: Request,
    x_internal_token: str | None = Header(default=None),
) -> dict:
    settings = request.app.state.settings
    _require_token(settings, x_internal_token)
    service = ReminderService(
        store=_store(request),
        order_store=_orders(request),
        channel_adapter=_adapter(request),
    )
    actions = await service.run(now=datetime.now(tz=UTC))
    return {"ok": True, "sent": len(actions), "actions": actions}


@router.post("/daily-summary")
async def daily_summary(
    request: Request,
    x_internal_token: str | None = Header(default=None),
) -> dict:
    settings = request.app.state.settings
    _require_token(settings, x_internal_token)
    service = _summary_service(request)
    actions = await service.run(now=datetime.now(tz=UTC))
    return {"ok": True, "sent": sum(1 for a in actions if a.get("sent")), "actions": actions}


sellers_router = APIRouter()


@sellers_router.get("/sellers/{seller_id}/summary")
def seller_summary(
    seller_id: str,
    request: Request,
    summary_date: str | None = Query(default=None, alias="date"),
    x_internal_token: str | None = Header(default=None),
) -> dict:
    from app.jobs.daily_summary import wat_today

    settings = request.app.state.settings
    _require_token(settings, x_internal_token)
    service = _summary_service(request)
    target_day = date.fromisoformat(summary_date) if summary_date else wat_today()
    row = service.summary_for(seller_id, target_day)
    if row is None:
        row = service._build_row(seller_id, target_day, datetime.now(tz=UTC))
        service.summaries[(seller_id, target_day.isoformat())] = row
    return row

"""Internal cron-style job endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException, Request

from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.config import Settings
from app.db.echo_store import EchoStore, build_store
from app.db.orders import OrderStore, build_order_store
from app.db.payments import PaymentStore, build_payment_store
from app.decisions.base import JevClient
from app.decisions.factory import build_jev
from app.jobs.recheck import RecheckService

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
    )
    actions = await service.recheck(now=datetime.now(tz=UTC))
    return {"ok": True, "actions": actions}

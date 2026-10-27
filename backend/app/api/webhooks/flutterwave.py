"""Flutterwave webhook route."""

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.agent.graph.verify import reevaluate_order_after_webhook
from app.config import Settings
from app.db.echo_store import EchoStore, build_store
from app.db.orders import OrderStore, build_order_store
from app.db.payments import PaymentStore, build_payment_store
from app.db.webhook_events import WebhookEventStore, build_webhook_event_store
from app.payments.flutterwave.webhook import FlutterwaveWebhookHandler, verify_flutterwave_hash

router = APIRouter()


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _store(request: Request) -> EchoStore:
    current = request.app.state.store
    if current is None:
        current = build_store(request.app.state.settings)
        request.app.state.store = current
    return current


def _order_store(request: Request) -> OrderStore:
    current = request.app.state.orders
    if current is None:
        current = build_order_store(request.app.state.settings)
        request.app.state.orders = current
    return current


def _payment_store(request: Request) -> PaymentStore:
    current = getattr(request.app.state, "payments", None)
    if current is None:
        current = build_payment_store(request.app.state.settings)
        request.app.state.payments = current
    return current


def _event_store(request: Request) -> WebhookEventStore:
    current = getattr(request.app.state, "webhook_events", None)
    if current is None:
        current = build_webhook_event_store(request.app.state.settings)
        request.app.state.webhook_events = current
    return current


@router.post("/webhooks/flutterwave")
async def flutterwave_webhook(request: Request) -> Response:
    settings = _settings(request)
    raw = await request.body()
    header = request.headers.get("verif-hash")
    if not verify_flutterwave_hash(header, settings.flutterwave_secret_key):
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "invalid_hash", "message": "bad verif-hash"}},
        )

    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "invalid_json", "message": "body is not JSON"}},
        )

    if not isinstance(payload, dict):
        return Response(status_code=200)

    data = payload.get("data") or {}
    event_id = str(data.get("id") or "")
    reference = str(data.get("tx_ref") or data.get("reference") or "")
    if not event_id or not reference:
        return Response(status_code=200)

    order_store = _order_store(request)
    order = order_store.get_order_by_ref(reference)
    if order is None:
        return Response(status_code=200)

    handler = FlutterwaveWebhookHandler(
        payment_store=_payment_store(request),
        event_store=_event_store(request),
    )
    try:
        await handler.handle(
            event_id=event_id,
            payload=payload,
            order_id=order["id"],
            expected_kobo=int(order.get("total_kobo") or 0),
        )
        await reevaluate_order_after_webhook(
            order,
            store=_store(request),
            order_store=order_store,
            payment_store=_payment_store(request),
            pii_salt=settings.pii_salt,
        )
    except Exception:
        pass

    return Response(status_code=200)

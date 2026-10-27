"""Paystack webhook route."""

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.agent.graph.verify import reevaluate_order_after_webhook
from app.config import Settings
from app.db.echo_store import EchoStore, build_store
from app.db.orders import OrderStore, build_order_store
from app.db.payments import PaymentStore, build_payment_store
from app.db.webhook_events import WebhookEventStore, build_webhook_event_store
from app.decisions.base import JevClient
from app.decisions.factory import build_jev
from app.payments.paystack.dva import PaystackClient
from app.payments.paystack.webhook import PaystackWebhookHandler, verify_paystack_signature

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


def _paystack_client(request: Request) -> PaystackClient:
    current = getattr(request.app.state, "paystack_client", None)
    if current is None:
        current = PaystackClient(request.app.state.settings, request.app.state.transport)
        request.app.state.paystack_client = current
    return current


def _jev(request: Request) -> JevClient:
    current = getattr(request.app.state, "jev", None)
    if current is None:
        current = build_jev(request.app.state.settings)
        request.app.state.jev = current
    return current


@router.post("/webhooks/paystack")
async def paystack_webhook(request: Request) -> Response:
    settings = _settings(request)
    raw = await request.body()
    signature = request.headers.get("x-paystack-signature")
    if not verify_paystack_signature(settings.paystack_secret_key, raw, signature):
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "invalid_signature", "message": "bad signature"}},
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
    reference = str(data.get("reference") or "")
    if not event_id or not reference:
        return Response(status_code=200)

    order_store = _order_store(request)
    order = order_store.get_order_by_ref(reference)
    if order is None:
        return Response(status_code=200)

    handler = PaystackWebhookHandler(
        client=_paystack_client(request),
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
            jev=_jev(request),
            pii_salt=settings.pii_salt,
        )
    except Exception:
        # Do not leak provider errors to the webhook sender.
        pass

    return Response(status_code=200)

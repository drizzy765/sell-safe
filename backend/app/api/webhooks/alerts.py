"""Bank alert forwarding webhooks (SMS and email)."""

from __future__ import annotations

import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.agent.graph.verify import reevaluate_order_after_webhook
from app.config import Settings
from app.db.echo_store import EchoStore, build_store
from app.db.orders import OrderStore, build_order_store
from app.db.payments import PaymentStore, build_payment_store
from app.decisions.base import JevClient
from app.decisions.factory import build_jev
from app.payments.alerts.parse import BankAlert, alert_to_extraction_dict, parse_alert
from app.verification.extract import ReceiptExtraction

router = APIRouter(prefix="/alerts")


def _require_token(settings: Settings, token: str | None) -> None:
    secret = settings.alert_inbound_secret
    if not secret:
        raise HTTPException(status_code=503, detail="alert secret not configured")
    if not token:
        raise HTTPException(status_code=401, detail="missing alert secret")
    if not hmac.compare_digest(token.encode(), secret.encode()):
        raise HTTPException(status_code=403, detail="invalid alert secret")


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


def _find_open_orders_for_alert(
    order_store: OrderStore,
    seller_id: str,
    alert: BankAlert,
) -> list[dict[str, Any]]:
    """Return the seller's open orders whose total matches the alert amount.

    Alerts do not carry a buyer identity, so we match by seller + amount + recency.
    """
    all_orders = getattr(order_store, "orders", [])
    cutoff = datetime.now(tz=UTC) - timedelta(hours=48)
    matches: list[dict[str, Any]] = []
    for order in all_orders:
        if order.get("seller_id") != seller_id:
            continue
        if order.get("status") not in ("awaiting_payment", "payment_review"):
            continue
        created_at = order.get("created_at")
        if created_at and datetime.fromisoformat(str(created_at).replace("Z", "+00:00")) < cutoff:
            continue
        if int(order.get("total_kobo") or 0) == alert.amount_kobo:
            matches.append(order)
    # Return the most recent if there are several; ambiguous matches are handled by tests.
    matches.sort(key=lambda o: str(o.get("created_at") or ""), reverse=True)
    return matches[:1]


def _build_extraction(alert: BankAlert) -> ReceiptExtraction:
    return ReceiptExtraction.model_validate(alert_to_extraction_dict(alert))


def _source_id(alert: BankAlert, order_id: str) -> str:
    ref = alert.reference or alert.txn_time_iso or ""
    return f"sms-{ref}-{order_id}"


async def _process_alert_for_order(
    order: dict[str, Any],
    alert: BankAlert,
    store: EchoStore,
    order_store: OrderStore,
    payment_store: PaymentStore,
    settings: Settings,
    jev: JevClient,
) -> None:
    payment = payment_store.get_or_create_payment(
        order_id=order["id"],
        method="bank_transfer",
        expected_kobo=int(order.get("total_kobo") or 0),
    )
    extraction = _build_extraction(alert)
    payment_store.insert_evidence(
        payment_id=payment["id"],
        evidence_type="bank_alert",
        source_id=_source_id(alert, order["id"]),
        extracted=extraction.model_dump(exclude={"image_sha256", "image_phash", "metadata_editor"}),
        trust_level=2,
    )
    await reevaluate_order_after_webhook(
        order,
        store=store,
        order_store=order_store,
        payment_store=payment_store,
        jev=jev,
        pii_salt=settings.pii_salt,
    )


@router.post("/sms")
async def sms_alert(
    request: Request,
    x_alert_secret: str | None = Header(default=None),
) -> dict:
    settings = request.app.state.settings
    _require_token(settings, x_alert_secret)

    body = await request.json()
    text = body.get("text")
    from_number = body.get("from")
    if not text or not from_number:
        raise HTTPException(status_code=400, detail="missing text or from")

    store = _store(request)
    seller = store.get_seller_by_channel("sms", str(from_number))
    if seller is None:
        raise HTTPException(status_code=403, detail="sender not a registered seller channel")

    alert = parse_alert(text)
    if alert is None:
        return {"ok": False, "reason": "unparseable"}
    if alert.type != "credit":
        return {"ok": False, "reason": "not_credit"}

    order_store = _orders(request)
    payment_store = _payments(request)
    jev = _jev(request)
    matching_orders = _find_open_orders_for_alert(order_store, seller["id"], alert)

    for order in matching_orders:
        await _process_alert_for_order(
            order,
            alert,
            store,
            order_store,
            payment_store,
            settings,
            jev,
        )

    return {"ok": True, "matched_orders": len(matching_orders)}


@router.post("/email")
async def email_alert(
    request: Request,
    x_alert_secret: str | None = Header(default=None),
) -> dict:
    """Email alerts use the same shared secret as SMS in this phase."""
    settings = request.app.state.settings
    _require_token(settings, x_alert_secret)

    body = await request.json()
    text = body.get("text")
    from_email = body.get("from")
    if not text or not from_email:
        raise HTTPException(status_code=400, detail="missing text or from")

    store = _store(request)
    seller = store.get_seller_by_channel("email", str(from_email))
    if seller is None:
        raise HTTPException(status_code=403, detail="sender not a registered seller channel")

    alert = parse_alert(text)
    if alert is None:
        return {"ok": False, "reason": "unparseable"}
    if alert.type != "credit":
        return {"ok": False, "reason": "not_credit"}

    order_store = _orders(request)
    payment_store = _payments(request)
    jev = _jev(request)
    matching_orders = _find_open_orders_for_alert(order_store, seller["id"], alert)

    for order in matching_orders:
        await _process_alert_for_order(
            order,
            alert,
            store,
            order_store,
            payment_store,
            settings,
            jev,
        )

    return {"ok": True, "matched_orders": len(matching_orders)}

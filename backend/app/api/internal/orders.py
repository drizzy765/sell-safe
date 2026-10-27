"""Internal order endpoints."""

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import Settings
from app.db.orders import OrderStore, build_order_store
from app.db.payments import PaymentStore, build_payment_store

router = APIRouter(prefix="/orders")


def _require_token(settings: Settings, token: str | None) -> None:
    if not settings.internal_api_token:
        raise HTTPException(status_code=503, detail="internal token not configured")
    if not token:
        raise HTTPException(status_code=401, detail="missing internal token")
    if token != settings.internal_api_token:
        raise HTTPException(status_code=403, detail="invalid internal token")


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


@router.post("/{ref}/release")
async def release_order(
    ref: str,
    request: Request,
    x_internal_token: str | None = Header(default=None),
) -> dict:
    settings = request.app.state.settings
    _require_token(settings, x_internal_token)

    order_store = _order_store(request)
    payment_store = _payment_store(request)

    order = order_store.get_order_by_ref(ref)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")

    payment = payment_store.get_payment_for_order(order["id"])
    verdict = (payment or {}).get("verdict") if payment else None
    if not verdict:
        latest = payment_store.get_latest_verdict(payment["id"]) if payment else None
        verdict = latest
    if not verdict or verdict.get("verdict") != "CONFIRMED":
        raise HTTPException(status_code=409, detail="release not allowed")

    # Seller confirmation of a mid-band verdict sets release_allowed=true.
    if not verdict.get("release_allowed"):
        payment_store.save_verdict(
            payment_id=payment["id"],
            verdict="CONFIRMED",
            confidence=verdict.get("confidence", 0.0),
            release_allowed=True,
            reasons=verdict.get("reasons", []),
            rule_hits=verdict.get("rule_hits", []),
            jev_scores=verdict.get("jev_scores"),
            decided_by="seller",
        )

    updated = order_store.update_order_status(ref, "released")
    return {"ok": True, "order": updated}

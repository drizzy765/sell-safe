"""Seller login <-> Instagram link/restore (internal, token-gated).

The web app verifies the Supabase Auth user server-side, then calls these
with INTERNAL_API_TOKEN. Link stores auth user -> IG account. Restore
returns the saved IG session id so the web app can re-set the opaque
session cookie without a fresh Instagram OAuth round-trip.
"""

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.db.seller_account_store import MemorySellerAccountStore, build_seller_account_store

router = APIRouter(prefix="/api/auth")

SESSION_HEADER = "X-IG-Session"


class LinkBody(BaseModel):
    user_id: str
    email: str = ""


class RestoreBody(BaseModel):
    user_id: str


def _require_token(request: Request, token: str | None) -> None:
    settings = request.app.state.settings
    expected = getattr(settings, "internal_api_token", "")
    if not expected:
        raise HTTPException(status_code=503, detail="internal token not configured")
    if not token:
        raise HTTPException(status_code=401, detail="missing internal token")
    if token != expected:
        raise HTTPException(status_code=403, detail="invalid internal token")


def _accounts(request: Request):
    current = getattr(request.app.state, "seller_accounts", None)
    if current is None:
        current = build_seller_account_store(request.app.state.settings)
        if current is None:
            current = MemorySellerAccountStore()
        request.app.state.seller_accounts = current
    return current


@router.post("/link")
async def link_account(
    body: LinkBody,
    request: Request,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _require_token(request, x_internal_token)
    sessions = request.app.state.instagram_sessions
    session_id = (x_ig_session or "").strip() or request.cookies.get("sellsafe_ig_session", "")
    session = sessions.get(session_id) if session_id else None
    if session is None:
        raise HTTPException(status_code=401, detail="Connect Instagram first.")
    row = _accounts(request).link(
        user_id=body.user_id,
        email=body.email,
        ig_account_id=session.account_id,
        username=session.username,
    )
    return {"linked": True, "username": row.get("username") or session.username}


@router.post("/restore")
async def restore_account(
    body: RestoreBody,
    request: Request,
    x_internal_token: str | None = Header(default=None, alias="X-Internal-Token"),
) -> dict:
    _require_token(request, x_internal_token)
    account = _accounts(request).get(body.user_id)
    if account is None:
        return {"linked": False, "connected": False}
    sessions = request.app.state.instagram_sessions
    session_id = sessions.find_session_id_by_account_id(str(account.get("ig_account_id") or ""))
    if session_id is None:
        return {
            "linked": True,
            "connected": False,
            "username": account.get("username") or None,
            "detail": "Instagram token expired. Reconnect Instagram once.",
        }
    return {
        "linked": True,
        "connected": True,
        "username": account.get("username") or None,
        "session_id": session_id,
    }

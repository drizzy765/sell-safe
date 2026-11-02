"""Public Instagram Login OAuth endpoints for seller connect / disconnect."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.channels.instagram.oauth import (
    InstagramOAuthClient,
    InstagramOAuthError,
    build_authorize_url,
    oauth_configured,
)
from app.db.instagram_session_store import InstagramSessionStore

router = APIRouter(prefix="/api/instagram", tags=["instagram-oauth"])

SESSION_HEADER = "X-IG-Session"
DEFAULT_RETURN_TO = "/?platform=instagram"


class InstagramStatusResponse(BaseModel):
    """Seller Instagram connection status. Never includes tokens."""

    connected: bool = False
    oauth_configured: bool = False
    username: str | None = None
    account_id: str | None = None
    ready: bool = False
    detail: str | None = None
    graph_username: str | None = None


async def _graph_username(access_token: str, transport=None) -> str | None:
    """Resolve the live Graph username for a session token (no token returned)."""
    token = (access_token or "").strip()
    if not token:
        return None
    import httpx

    # Always use a real network client for Graph — app.state.transport may be an
    # ASGI test transport that cannot reach graph.instagram.com.
    del transport
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://graph.instagram.com/v23.0/me",
                params={"fields": "user_id,username,account_type", "access_token": token},
            )
        if response.status_code >= 400:
            return None
        payload = response.json()
        name = str(payload.get("username") or "").strip()
        if name.isdigit():
            return None
        return name or None
    except Exception:
        return None


class OAuthStartResponse(BaseModel):
    authorize_url: str
    state: str


class OAuthExchangeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)


class OAuthExchangeResponse(BaseModel):
    session_id: str
    username: str
    account_id: str
    return_to: str
    connected: bool = True


class DisconnectResponse(BaseModel):
    connected: bool = False
    detail: str = "Instagram disconnected."


def _sessions(request: Request) -> InstagramSessionStore:
    current = getattr(request.app.state, "instagram_sessions", None)
    if current is None:
        current = InstagramSessionStore()
        request.app.state.instagram_sessions = current
    return current


def _oauth_client(request: Request) -> InstagramOAuthClient:
    settings = request.app.state.settings
    transport = getattr(request.app.state, "transport", None)
    return InstagramOAuthClient(settings, transport=transport)


def _session_id(
    request: Request,
    x_ig_session: str | None,
) -> str:
    header = (x_ig_session or "").strip()
    if header:
        return header
    cookie = request.cookies.get("sellsafe_ig_session", "").strip()
    return cookie


@router.get("/status", response_model=InstagramStatusResponse)
async def instagram_status(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> InstagramStatusResponse:
    settings = request.app.state.settings
    configured = oauth_configured(settings)
    session_id = _session_id(request, x_ig_session)
    session = _sessions(request).get(session_id) if session_id else None
    if session is not None:
        # Prefer the live OAuth session token for outbound replies so we do not
        # accidentally send as a different IG account from .env.
        settings.instagram_access_token = session.access_token
        graph_username: str | None = None
        if not (session.username or "").strip():
            transport = getattr(request.app.state, "transport", None)
            graph_username = await _graph_username(session.access_token, transport=transport)
            if graph_username:
                session.username = graph_username
        return InstagramStatusResponse(
            connected=True,
            oauth_configured=configured,
            username=session.username or graph_username,
            account_id=session.account_id,
            ready=True,
            graph_username=graph_username or session.username or None,
        )
    detail = None
    if not configured:
        detail = (
            "Instagram OAuth is not configured. Set INSTAGRAM_APP_ID "
            "(Instagram product id, not META_APP_ID), INSTAGRAM_APP_SECRET, "
            "and INSTAGRAM_OAUTH_REDIRECT_URI."
        )
    return InstagramStatusResponse(
        connected=False,
        oauth_configured=configured,
        ready=False,
        detail=detail,
    )


@router.get("/oauth/start", response_model=OAuthStartResponse)
def oauth_start(
    request: Request,
    return_to: str = Query(default=DEFAULT_RETURN_TO),
    force_reauth: bool = Query(default=True),
    redirect: bool = Query(default=False),
) -> OAuthStartResponse | RedirectResponse:
    """Create CSRF state and return (or redirect to) the Instagram authorize URL."""
    settings = request.app.state.settings
    if not oauth_configured(settings):
        raise HTTPException(
            status_code=503,
            detail=(
                "Instagram OAuth is not configured. Set INSTAGRAM_APP_ID "
                "(Instagram product id, not META_APP_ID), INSTAGRAM_APP_SECRET, "
                "and INSTAGRAM_OAUTH_REDIRECT_URI."
            ),
        )
    safe_return = return_to if return_to.startswith("/") else DEFAULT_RETURN_TO
    state = _sessions(request).create_state(return_to=safe_return)
    try:
        authorize_url = build_authorize_url(settings, state=state, force_reauth=force_reauth)
    except InstagramOAuthError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    if redirect:
        return RedirectResponse(url=authorize_url, status_code=302)
    return OAuthStartResponse(authorize_url=authorize_url, state=state)


@router.post("/oauth/exchange", response_model=OAuthExchangeResponse)
async def oauth_exchange(
    body: OAuthExchangeRequest,
    request: Request,
) -> OAuthExchangeResponse:
    """Exchange the OAuth code for a long-lived token; return opaque session id."""
    settings = request.app.state.settings
    if not oauth_configured(settings):
        raise HTTPException(status_code=503, detail="Instagram OAuth is not configured.")
    consumed = _sessions(request).consume_state(body.state)
    if consumed is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Start Connect Instagram again.",
        )
    try:
        access_token, account_id, username, expires_in = await _oauth_client(request).exchange_code(
            body.code
        )
    except InstagramOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    session_id = _sessions(request).create_session(
        access_token=access_token,
        account_id=account_id,
        username=username,
        expires_in=expires_in,
    )
    settings.instagram_access_token = access_token
    if account_id:
        settings.instagram_account_id = account_id
    return OAuthExchangeResponse(
        session_id=session_id,
        username=username,
        account_id=account_id,
        return_to=consumed.return_to,
        connected=True,
    )


@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    """Optional backend callback when redirect_uri points at FastAPI."""
    settings = request.app.state.settings
    web_base = (settings.web_base_url or "").rstrip("/")
    if not web_base:
        raise HTTPException(
            status_code=503,
            detail="WEB_BASE_URL is required when using the backend OAuth callback.",
        )

    def _to_web(**params: str) -> RedirectResponse:
        return RedirectResponse(
            url=f"{web_base}/api/instagram/session?{urlencode(params)}",
            status_code=302,
        )

    if error:
        return _to_web(ig_error=error_description or error or "access_denied")
    if not code or not state:
        return _to_web(ig_error="missing_code")

    consumed = _sessions(request).consume_state(state)
    if consumed is None:
        return _to_web(ig_error="invalid_state")

    try:
        access_token, account_id, username, expires_in = await _oauth_client(request).exchange_code(
            code
        )
    except InstagramOAuthError as exc:
        return _to_web(ig_error=str(exc)[:180])

    session_id = _sessions(request).create_session(
        access_token=access_token,
        account_id=account_id,
        username=username,
        expires_in=expires_in,
    )
    settings.instagram_access_token = access_token
    if account_id:
        settings.instagram_account_id = account_id
    dest = consumed.return_to if consumed.return_to.startswith("/") else DEFAULT_RETURN_TO
    return _to_web(session_id=session_id, ig_user=username, return_to=dest)


@router.post("/disconnect", response_model=DisconnectResponse)
def disconnect(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> DisconnectResponse:
    session_id = _session_id(request, x_ig_session)
    if session_id:
        _sessions(request).delete(session_id)
    return DisconnectResponse()

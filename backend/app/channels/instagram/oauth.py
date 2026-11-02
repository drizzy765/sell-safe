"""Instagram Login (Business Login) OAuth helpers.

Authorize → short-lived code exchange → long-lived token → /me profile.
Uses INSTAGRAM_APP_SECRET (Instagram Login screen), not META_APP_SECRET.
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.config import Settings

_AUTHORIZE_URL = "https://www.instagram.com/oauth/authorize"
_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
_GRAPH_HOST = "https://graph.instagram.com"

DEFAULT_SCOPES = (
    "instagram_business_basic",
    "instagram_business_manage_messages",
)


class InstagramOAuthError(Exception):
    """Raised when Meta rejects an OAuth step. Message is safe for clients."""


def instagram_client_id(settings: Settings) -> str:
    """Instagram App ID for Login OAuth. Never use META_APP_ID here."""
    return settings.instagram_app_id.strip()


def oauth_configured(settings: Settings) -> bool:
    return bool(
        instagram_client_id(settings)
        and settings.instagram_app_secret.strip()
        and settings.instagram_oauth_redirect_uri.strip()
    )


def build_authorize_url(
    settings: Settings,
    *,
    state: str,
    force_reauth: bool = True,
) -> str:
    if not oauth_configured(settings):
        raise InstagramOAuthError(
            "Instagram OAuth is not configured. Set INSTAGRAM_APP_ID "
            "(from Instagram → API setup with Instagram login — not META_APP_ID), "
            "INSTAGRAM_APP_SECRET, and INSTAGRAM_OAUTH_REDIRECT_URI."
        )
    scopes = settings.instagram_oauth_scopes.strip() or ",".join(DEFAULT_SCOPES)
    params: dict[str, str] = {
        "client_id": instagram_client_id(settings),
        "redirect_uri": settings.instagram_oauth_redirect_uri.strip(),
        "response_type": "code",
        "scope": scopes,
        "state": state,
    }
    if force_reauth:
        params["force_reauth"] = "true"
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


def _normalize_code(code: str) -> str:
    # Meta may append #_ to the redirected code.
    return code.strip().removesuffix("#_").strip()


def _parse_short_lived(payload: object) -> tuple[str, str]:
    """Return (access_token, user_id) from the code-exchange response."""
    if not isinstance(payload, dict):
        raise InstagramOAuthError("Unexpected token response from Instagram.")

    data = payload.get("data")
    if isinstance(data, list) and data:
        row = data[0]
        if isinstance(row, dict):
            token = str(row.get("access_token") or "").strip()
            user_id = str(row.get("user_id") or "").strip()
            if token and user_id:
                return token, user_id

    token = str(payload.get("access_token") or "").strip()
    user_id = str(payload.get("user_id") or "").strip()
    if token and user_id:
        return token, user_id
    raise InstagramOAuthError("Instagram token response missing access_token or user_id.")


class InstagramOAuthClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def exchange_code(
        self, code: str
    ) -> tuple[str, str, str, int | None, tuple[str, ...]]:
        """Exchange auth code → long-lived token + account id + username.

        Returns
        (access_token, account_id, username, expires_in_seconds|None, alias_ids).
        ``alias_ids`` includes the IG-scoped ``/me`` id used as webhook recipient.id.
        """
        short_token, fallback_user_id = await self._exchange_short_lived(_normalize_code(code))
        long_token, expires_in = await self._exchange_long_lived(short_token)
        account_id, username, alias_ids = await self._fetch_profile(long_token, fallback_user_id)
        return long_token, account_id, username, expires_in, alias_ids

    async def subscribe_webhooks(self, access_token: str) -> bool:
        """Subscribe this IG account to app message webhooks (required for auto-replies)."""
        version = (self._settings.graph_api_version or "v21.0").strip() or "v21.0"
        fields = (
            "messages,messaging_postbacks,messaging_seen,messaging_referral,"
            "message_edit,message_reactions"
        )
        url = f"{_GRAPH_HOST}/{version}/me/subscribed_apps"
        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            response = await client.post(
                url,
                params={"subscribed_fields": fields, "access_token": access_token},
            )
        if response.status_code >= 400:
            return False
        payload = response.json() if response.content else {}
        return bool(isinstance(payload, dict) and payload.get("success") is True)

    async def _exchange_short_lived(self, code: str) -> tuple[str, str]:
        form = {
            "client_id": instagram_client_id(self._settings),
            "client_secret": self._settings.instagram_app_secret.strip(),
            "grant_type": "authorization_code",
            "redirect_uri": self._settings.instagram_oauth_redirect_uri.strip(),
            "code": code,
        }
        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            response = await client.post(_TOKEN_URL, data=form)
        if response.status_code >= 400:
            raise InstagramOAuthError(
                _safe_meta_error(response, "Could not exchange Instagram code.")
            )
        return _parse_short_lived(response.json())

    async def _exchange_long_lived(self, short_token: str) -> tuple[str, int | None]:
        # Meta now requires POST for ig_exchange_token. GET returns:
        # "Unsupported request - method type: get"
        form = {
            "grant_type": "ig_exchange_token",
            "client_secret": self._settings.instagram_app_secret.strip(),
            "access_token": short_token,
        }
        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            response = await client.post(f"{_GRAPH_HOST}/access_token", data=form)
        if response.status_code >= 400:
            # Keep the short-lived token if long-lived exchange fails (still usable ~1h).
            return short_token, 3600
        payload = response.json()
        if not isinstance(payload, dict):
            return short_token, 3600
        # Ignore IGApiException bodies that sometimes arrive with odd status handling.
        if isinstance(payload.get("error"), dict):
            return short_token, 3600
        token = str(payload.get("access_token") or "").strip() or short_token
        expires_in = _as_int(payload.get("expires_in"))
        return token, expires_in

    async def _fetch_profile(
        self, access_token: str, fallback_user_id: str
    ) -> tuple[str, str, tuple[str, ...]]:
        version = (self._settings.graph_api_version or "v21.0").strip() or "v21.0"
        fields = "id,user_id,username,account_type"
        urls = [f"{_GRAPH_HOST}/{version}/me"]
        if fallback_user_id:
            urls.append(f"{_GRAPH_HOST}/{version}/{fallback_user_id}")

        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            for url in urls:
                response = await client.get(
                    url,
                    params={"fields": fields, "access_token": access_token},
                )
                if response.status_code >= 400:
                    continue
                payload = response.json()
                if not isinstance(payload, dict) or isinstance(payload.get("error"), dict):
                    continue
                igsid = str(payload.get("id") or "").strip()
                # Professional account id is user_id; keep IG-scoped id as alias.
                account_id = (
                    str(payload.get("user_id") or "").strip()
                    or fallback_user_id
                    or igsid
                )
                username = str(payload.get("username") or "").strip()
                if username.isdigit():
                    username = ""
                aliases = tuple(
                    dict.fromkeys(
                        a for a in (igsid, fallback_user_id) if a and a != account_id
                    )
                )
                if account_id:
                    return account_id, username, aliases
        return fallback_user_id, "", ()


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _safe_meta_error(response: httpx.Response, fallback: str) -> str:
    try:
        payload = response.json()
    except Exception:
        return fallback
    if not isinstance(payload, dict):
        return fallback
    err = payload.get("error")
    if isinstance(err, dict):
        message = str(err.get("message") or "").strip()
        if message and "token" not in message.lower() and "secret" not in message.lower():
            return message
    error_message = str(payload.get("error_message") or "").strip()
    if error_message and "token" not in error_message.lower():
        return error_message
    return fallback

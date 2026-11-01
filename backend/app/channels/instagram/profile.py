"""Fetch Instagram professional profile + recent media with a user access token."""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from app.config import Settings

_GRAPH_HOST = "https://graph.instagram.com"

# Core fields that Instagram Login /me accepts reliably.
_CORE_FIELDS = "user_id,username,account_type"
# Optional enrichment — requested one-by-one so one bad field cannot break Confirm Shop.
_OPTIONAL_FIELDS = (
    "name",
    "biography",
    "profile_picture_url",
    "followers_count",
    "website",
)
_MEDIA_FIELDS = "id,caption,media_url,media_type,timestamp,permalink,thumbnail_url"


class InstagramProfileError(Exception):
    """Safe-to-show profile fetch failure."""

    def __init__(self, message: str, *, auth_failed: bool = False) -> None:
        super().__init__(message)
        self.auth_failed = auth_failed


@dataclass
class IgMediaItem:
    id: str
    caption: str = ""
    media_url: str = ""
    media_type: str = ""
    timestamp: str = ""
    permalink: str = ""
    thumbnail_url: str = ""


@dataclass
class IgProfile:
    account_id: str
    username: str
    name: str = ""
    biography: str = ""
    profile_picture_url: str = ""
    website: str = ""
    followers_count: int | None = None
    account_type: str = ""
    category: str = ""
    media: list[IgMediaItem] = field(default_factory=list)


class InstagramProfileClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def _version(self) -> str:
        return (self._settings.graph_api_version or "v21.0").strip() or "v21.0"

    async def fetch_shop_profile(
        self,
        access_token: str,
        *,
        media_limit: int = 12,
        fallback_account_id: str = "",
        fallback_username: str = "",
    ) -> IgProfile:
        version = self._version()
        me_url = f"{_GRAPH_HOST}/{version}/me"

        try:
            profile_payload = await self._get(
                me_url,
                {"fields": _CORE_FIELDS, "access_token": access_token},
            )
        except InstagramProfileError:
            profile_payload = {}
            # Some IGAA tokens reject /me but allow /{ig-user-id}.
            if fallback_account_id:
                try:
                    profile_payload = await self._get(
                        f"{_GRAPH_HOST}/{version}/{fallback_account_id}",
                        {"fields": _CORE_FIELDS, "access_token": access_token},
                    )
                except InstagramProfileError:
                    profile_payload = {}
            if not profile_payload:
                if fallback_account_id:
                    profile_payload = {
                        "user_id": fallback_account_id,
                        "username": fallback_username,
                        "account_type": "",
                    }
                else:
                    raise

        account_id = str(
            profile_payload.get("user_id") or profile_payload.get("id") or fallback_account_id
        ).strip()
        username = str(profile_payload.get("username") or fallback_username).strip()
        if not account_id:
            raise InstagramProfileError(
                "Instagram profile is missing user id. Reconnect Instagram.",
                auth_failed=True,
            )
        # Numeric "username" means Graph never returned a handle.
        if username.isdigit():
            if fallback_username and not fallback_username.isdigit():
                username = fallback_username
            else:
                username = ""

        # Enrich with optional fields; ignore per-field failures (Meta field matrix varies).
        for field_name in _OPTIONAL_FIELDS:
            try:
                extra = await self._get(
                    me_url,
                    {"fields": field_name, "access_token": access_token},
                )
                if field_name in extra and extra[field_name] is not None:
                    profile_payload[field_name] = extra[field_name]
            except InstagramProfileError:
                continue

        media_items: list[IgMediaItem] = []
        try:
            media_payload = await self._get(
                f"{_GRAPH_HOST}/{version}/me/media",
                {
                    "fields": _MEDIA_FIELDS,
                    "limit": str(max(1, min(media_limit, 25))),
                    "access_token": access_token,
                },
            )
            rows = media_payload.get("data")
            if isinstance(rows, list):
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    media_id = str(row.get("id") or "").strip()
                    if not media_id:
                        continue
                    media_items.append(
                        IgMediaItem(
                            id=media_id,
                            caption=str(row.get("caption") or ""),
                            media_url=str(row.get("media_url") or ""),
                            media_type=str(row.get("media_type") or ""),
                            timestamp=str(row.get("timestamp") or ""),
                            permalink=str(row.get("permalink") or ""),
                            thumbnail_url=str(row.get("thumbnail_url") or ""),
                        )
                    )
        except InstagramProfileError:
            media_items = []

        # Some apps only allow media via /{ig-user-id}/media
        if not media_items and account_id:
            try:
                media_payload = await self._get(
                    f"{_GRAPH_HOST}/{version}/{account_id}/media",
                    {
                        "fields": _MEDIA_FIELDS,
                        "limit": str(max(1, min(media_limit, 25))),
                        "access_token": access_token,
                    },
                )
                rows = media_payload.get("data")
                if isinstance(rows, list):
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        media_id = str(row.get("id") or "").strip()
                        if not media_id:
                            continue
                        media_items.append(
                            IgMediaItem(
                                id=media_id,
                                caption=str(row.get("caption") or ""),
                                media_url=str(row.get("media_url") or ""),
                                media_type=str(row.get("media_type") or ""),
                                timestamp=str(row.get("timestamp") or ""),
                                permalink=str(row.get("permalink") or ""),
                                thumbnail_url=str(row.get("thumbnail_url") or ""),
                            )
                        )
            except InstagramProfileError:
                media_items = []

        followers = profile_payload.get("followers_count")
        followers_count = followers if isinstance(followers, int) else None

        return IgProfile(
            account_id=account_id,
            username=username,
            name=str(profile_payload.get("name") or "").strip(),
            biography=str(profile_payload.get("biography") or "").strip(),
            profile_picture_url=str(profile_payload.get("profile_picture_url") or "").strip(),
            website=str(profile_payload.get("website") or "").strip(),
            followers_count=followers_count,
            account_type=str(profile_payload.get("account_type") or "").strip(),
            category=str(profile_payload.get("category") or "").strip(),
            media=media_items,
        )

    async def _get(self, url: str, params: dict[str, str]) -> dict:
        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            response = await client.get(url, params=params)
        if response.status_code in {401, 403}:
            raise InstagramProfileError(
                "Instagram session expired. Disconnect and connect again.",
                auth_failed=True,
            )
        if response.status_code >= 400:
            raise InstagramProfileError(_safe_error(response), auth_failed=_is_auth_error(response))
        payload = response.json()
        if not isinstance(payload, dict):
            raise InstagramProfileError("Unexpected Instagram profile response.")
        if isinstance(payload.get("error"), dict):
            raise InstagramProfileError(
                _safe_error(response),
                auth_failed=_is_auth_error(response),
            )
        return payload


def _is_auth_error(response: httpx.Response) -> bool:
    try:
        payload = response.json()
    except Exception:
        return response.status_code in {401, 403}
    if not isinstance(payload, dict):
        return False
    err = payload.get("error")
    if not isinstance(err, dict):
        return False
    code = err.get("code")
    message = str(err.get("message") or "").lower()
    return code in {190, 102} or "session has expired" in message or "invalid oauth" in message


def _safe_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return "Could not load Instagram profile."
    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            message = str(err.get("message") or "").strip()
            if message and "token" not in message.lower() and "secret" not in message.lower():
                return message
    return "Could not load Instagram profile."

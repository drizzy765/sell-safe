"""Sync Instagram Messaging conversations into the local message store.

Dashboard inbox mirrors Graph Conversations API (past DMs) plus webhooks
(live DMs). Meta only exposes details for the ~20 newest messages per thread.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings

_GRAPH_HOST = "https://graph.instagram.com"
_LOG = logging.getLogger(__name__)
_SYNC_DEBUG_PATH = Path(".tmp/inbox_sync_last.json")
# Skip writing debug from unit tests (fake tokens like "tok").
_MIN_LIVE_TOKEN_LEN = 20


def _conversation_fields(messages_limit: int) -> str:
    limit = max(1, min(int(messages_limit), 20))
    return (
        "id,updated_time,"
        "participants{id,username},"
        f"messages.limit({limit}){{id,created_time,from,to,message}}"
    )


def _normalize_created_at(raw: object) -> str:
    text = str(raw or "").strip()
    if not text:
        return datetime.now(tz=UTC).isoformat()
    if text.isdigit():
        try:
            ts = int(text)
            if ts > 10_000_000_000:
                ts //= 1000
            return datetime.fromtimestamp(ts, tz=UTC).isoformat()
        except (OSError, OverflowError, ValueError):
            return datetime.now(tz=UTC).isoformat()
    if text.endswith("+0000"):
        text = text[:-5] + "+00:00"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(tz=UTC).isoformat()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def _participant_rows(payload: dict) -> list[dict]:
    participants = payload.get("participants") or {}
    if isinstance(participants, dict):
        rows = participants.get("data") or []
    elif isinstance(participants, list):
        rows = participants
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def _message_rows(payload: dict) -> list[dict]:
    messages = payload.get("messages") or {}
    if isinstance(messages, dict):
        rows = messages.get("data") or []
    elif isinstance(messages, list):
        rows = messages
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def _buyer_from_participants(
    participants: list[dict],
    *,
    seller_ig_id: str,
) -> tuple[str, str]:
    seller = (seller_ig_id or "").strip()
    for row in participants:
        pid = str(row.get("id") or "").strip()
        if not pid or pid == seller:
            continue
        username = str(row.get("username") or "").strip()
        return pid, username
    return "", ""


def _safe_graph_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return f"HTTP {response.status_code}"
    err = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(err, dict):
        msg = str(err.get("message") or "").strip()
        code = err.get("code")
        sub = err.get("error_subcode")
        # Meta returns this when the IG account is not a role/tester on the app,
        # or Access Verification is incomplete — OAuth succeeds but Graph is dead.
        if code == 100 and "unsupported request" in msg.lower():
            return (
                "Meta blocked Graph reads for this Instagram token (code 100). "
                "Add sellsafe.testshop.ng as an Instagram Tester, accept the invite "
                "in Instagram → Settings → Apps and websites, revoke the app, then "
                "Reconnect. Or paste a dashboard-generated token into "
                "INSTAGRAM_ACCESS_TOKEN."
            )
        bits = [msg or f"HTTP {response.status_code}"]
        if code is not None:
            bits.append(f"code={code}")
        if sub is not None:
            bits.append(f"subcode={sub}")
        joined = " ".join(bits)
        lower = joined.lower()
        if "token" in lower or "secret" in lower:
            return f"Instagram auth error (code={code})"
        return joined[:240]
    return f"HTTP {response.status_code}"


def _write_debug(report: dict, *, access_token: str = "") -> None:
    if len((access_token or "").strip()) < _MIN_LIVE_TOKEN_LEN:
        return
    try:
        _SYNC_DEBUG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SYNC_DEBUG_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass


@dataclass
class InboxSyncReport:
    attempted: bool = False
    ok: bool = False
    conversations: int = 0
    inserted: int = 0
    error: str | None = None
    endpoint: str | None = None
    details: list[str] = field(default_factory=list)

    def public_dict(self) -> dict:
        return asdict(self)


class InstagramConversationClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def _version(self) -> str:
        return (self._settings.graph_api_version or "v23.0").strip() or "v23.0"

    async def list_conversations(
        self,
        access_token: str,
        *,
        seller_ig_id: str = "",
        messages_limit: int = 20,
        page_limit: int = 25,
    ) -> tuple[list[dict], str | None, str | None]:
        """Return (conversations, endpoint_used, error)."""
        token = (access_token or "").strip()
        if not token:
            return [], None, "No Instagram access token on the session."
        version = self._version()
        fields = _conversation_fields(messages_limit)
        limit = str(max(1, min(int(page_limit), 50)))
        paths = [f"/{version}/me/conversations"]
        ig_id = (seller_ig_id or "").strip()
        if ig_id:
            paths.append(f"/{version}/{ig_id}/conversations")

        last_error: str | None = None
        async with httpx.AsyncClient(transport=self._transport, timeout=45.0) as client:
            for path in paths:
                url = f"{_GRAPH_HOST}{path}"
                rich = await client.get(
                    url,
                    params={
                        "platform": "instagram",
                        "fields": fields,
                        "limit": limit,
                        "access_token": token,
                    },
                )
                if rich.status_code < 400:
                    rows = list((rich.json() or {}).get("data") or [])
                    hydrated = await self._hydrate_rows(
                        client,
                        rows[:page_limit],
                        access_token=token,
                        messages_limit=messages_limit,
                    )
                    return hydrated, path, None

                last_error = _safe_graph_error(rich)
                thin = await client.get(
                    url,
                    params={
                        "platform": "instagram",
                        "limit": limit,
                        "access_token": token,
                    },
                )
                if thin.status_code >= 400:
                    last_error = _safe_graph_error(thin)
                    _LOG.warning(
                        "instagram conversations list failed path=%s status=%s body=%s",
                        path,
                        thin.status_code,
                        thin.text[:300],
                    )
                    continue

                base_rows = list((thin.json() or {}).get("data") or [])
                enriched: list[dict] = []
                for row in base_rows[:page_limit]:
                    conv_id = str(row.get("id") or "")
                    if not conv_id:
                        continue
                    detail = await self.get_conversation(
                        conv_id,
                        access_token=token,
                        messages_limit=messages_limit,
                        client=client,
                    )
                    if detail:
                        enriched.append(detail)
                return enriched, path, None

        return [], paths[0] if paths else None, last_error or "Conversations API failed."

    async def get_conversation(
        self,
        conversation_id: str,
        *,
        access_token: str,
        messages_limit: int = 20,
        client: httpx.AsyncClient | None = None,
    ) -> dict | None:
        token = (access_token or "").strip()
        conv_id = (conversation_id or "").strip()
        if not token or not conv_id:
            return None
        version = self._version()
        fields = _conversation_fields(messages_limit)
        url = f"{_GRAPH_HOST}/{version}/{conv_id}"
        owns_client = client is None
        http = client or httpx.AsyncClient(transport=self._transport, timeout=45.0)
        try:
            response = await http.get(
                url,
                params={"fields": fields, "access_token": token},
            )
            if response.status_code >= 400:
                _LOG.warning(
                    "instagram conversation fetch failed id=%s status=%s body=%s",
                    conv_id[:12],
                    response.status_code,
                    response.text[:200],
                )
                return None
            data = response.json() or {}
            if not isinstance(data, dict):
                return None
            messages = _message_rows(data)
            if messages and not any(m.get("message") or m.get("from") for m in messages):
                data["messages"] = {
                    "data": await self._fetch_message_details(http, messages, access_token=token)
                }
            return data
        finally:
            if owns_client:
                await http.aclose()

    async def _hydrate_rows(
        self,
        client: httpx.AsyncClient,
        rows: list[dict],
        *,
        access_token: str,
        messages_limit: int,
    ) -> list[dict]:
        out: list[dict] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            messages = _message_rows(row)
            participants = _participant_rows(row)
            needs_detail = not participants or (
                messages and not any(m.get("message") or m.get("from") for m in messages)
            )
            if needs_detail and row.get("id"):
                detail = await self.get_conversation(
                    str(row["id"]),
                    access_token=access_token,
                    messages_limit=messages_limit,
                    client=client,
                )
                if detail:
                    out.append(detail)
                    continue
            if messages and not any(m.get("message") or m.get("from") for m in messages):
                row = dict(row)
                row["messages"] = {
                    "data": await self._fetch_message_details(
                        client, messages, access_token=access_token
                    )
                }
            out.append(row)
        return out

    async def _fetch_message_details(
        self,
        client: httpx.AsyncClient,
        messages: list[dict],
        *,
        access_token: str,
    ) -> list[dict]:
        version = self._version()
        detailed: list[dict] = []
        for msg in messages[:20]:
            mid = str(msg.get("id") or "").strip()
            if not mid:
                continue
            response = await client.get(
                f"{_GRAPH_HOST}/{version}/{mid}",
                params={
                    "fields": "id,created_time,from,to,message",
                    "access_token": access_token,
                },
            )
            if response.status_code >= 400:
                # Keep the stub so the thread still appears.
                detailed.append(msg)
                continue
            payload = response.json() or {}
            detailed.append(payload if isinstance(payload, dict) else msg)
        return detailed


async def sync_instagram_inbox(
    *,
    store: Any,
    access_token: str,
    seller_ig_id: str,
    seller_id: str,
    settings: Settings,
    transport: httpx.AsyncBaseTransport | None = None,
    inbox_control: Any | None = None,
    conversation_limit: int = 25,
    messages_per_conversation: int = 20,
) -> InboxSyncReport:
    """Pull Graph conversations into ``store``."""
    report = InboxSyncReport(attempted=True)
    token = (access_token or "").strip()
    if store is None or not token:
        report.error = "No Instagram access token on the session."
        _write_debug(report.public_dict(), access_token=token)
        return report

    client = InstagramConversationClient(settings, transport=transport)
    conversations, endpoint, error = await client.list_conversations(
        token,
        seller_ig_id=seller_ig_id,
        messages_limit=messages_per_conversation,
        page_limit=conversation_limit,
    )
    report.endpoint = endpoint
    report.conversations = len(conversations)
    if error and not conversations:
        if "404" in error:
            report.error = (
                f"{error} — Conversations edge missing for this token/version. "
                "Reconnect Instagram Login and confirm instagram_business_manage_messages."
            )
        else:
            report.error = error
        _write_debug(report.public_dict(), access_token=token)
        return report

    inserted = 0
    seller_ids = {
        (seller_ig_id or "").strip(),
        (seller_id or "").strip(),
    }
    seller_ids.discard("")

    for conv in conversations:
        if not isinstance(conv, dict):
            continue
        participants = _participant_rows(conv)
        buyer_external_id, buyer_username = _buyer_from_participants(
            participants, seller_ig_id=seller_ig_id
        )
        messages = _message_rows(conv)
        if not buyer_external_id and messages:
            for msg in messages:
                from_row = msg.get("from") or {}
                from_id = str(from_row.get("id") or "").strip()
                if from_id and from_id not in seller_ids:
                    buyer_external_id = from_id
                    buyer_username = str(from_row.get("username") or "").strip()
                    break
                to_data = (
                    ((msg.get("to") or {}).get("data") or [])
                    if isinstance(msg.get("to"), dict)
                    else []
                )
                for to_row in to_data:
                    to_id = str(to_row.get("id") or "").strip()
                    if to_id and to_id not in seller_ids:
                        buyer_external_id = to_id
                        buyer_username = str(to_row.get("username") or "").strip()
                        break
                if buyer_external_id:
                    break
        if not buyer_external_id:
            cid = str(conv.get("id") or "")[:16]
            report.details.append(f"skipped conversation {cid}: no buyer")
            continue

        buyer_id = store.ensure_buyer(
            "instagram",
            buyer_external_id,
            display_name=buyer_username or None,
        )
        latest_inbound_at: str | None = None

        if not messages:
            # Still surface the thread with a placeholder so the inbox isn't empty.
            stub_id = f"conv-stub-{buyer_external_id}"
            known = getattr(store, "messages", None)
            if not (isinstance(known, dict) and stub_id in known):
                store.save_inbound(
                    seller_id=seller_id,
                    buyer_id=buyer_id,
                    channel="instagram",
                    external_msg_id=stub_id,
                    message_type="text",
                    text="(Open thread to load messages)",
                    created_at=_normalize_created_at(conv.get("updated_time")),
                )
                inserted += 1
            continue

        for msg in messages:
            mid = str(msg.get("id") or "").strip()
            if not mid:
                continue
            from_row = msg.get("from") or {}
            from_id = str(from_row.get("id") or "").strip()
            from_username = str(from_row.get("username") or "").strip()
            text = str(msg.get("message") or "")
            created_at = _normalize_created_at(msg.get("created_time"))
            is_outbound = bool(from_id) and from_id in seller_ids
            # If `from` is missing, treat as inbound so the chat still shows.
            if not from_id:
                is_outbound = False
            if not is_outbound and from_username:
                store.ensure_buyer(
                    "instagram",
                    buyer_external_id,
                    display_name=from_username,
                )
            if is_outbound:
                known = getattr(store, "messages", None)
                already = isinstance(known, dict) and mid in known
                store.save_outbound(
                    seller_id=seller_id,
                    buyer_id=buyer_id,
                    channel="instagram",
                    external_msg_id=mid,
                    text=text,
                    created_at=created_at,
                )
                if not already:
                    inserted += 1
            else:
                saved = store.save_inbound(
                    seller_id=seller_id,
                    buyer_id=buyer_id,
                    channel="instagram",
                    external_msg_id=mid,
                    message_type="text",
                    text=text or None,
                    created_at=created_at,
                    # Mark Graph mirrors so a later webhook can still run the agent.
                    meta={"source": "graph_sync"},
                )
                if saved:
                    inserted += 1
                    if latest_inbound_at is None or created_at > latest_inbound_at:
                        latest_inbound_at = created_at
        if (
            inbox_control is not None
            and latest_inbound_at
            and hasattr(inbox_control, "mark_inbound")
        ):
            ctrl = inbox_control.get_control(seller_id, buyer_id)
            if not ctrl.last_inbound_at or latest_inbound_at > (ctrl.last_inbound_at or ""):
                inbox_control.mark_inbound(
                    seller_id, buyer_id, at=latest_inbound_at, count_unread=False
                )

    report.inserted = inserted
    report.ok = True
    if error:
        report.details.append(error)
    _write_debug(report.public_dict(), access_token=token)
    return report

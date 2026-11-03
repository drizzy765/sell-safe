"""Instagram OAuth state + seller session store.

Tokens stay server-side. The browser only keeps an opaque session id.
Sessions are also mirrored to ``.tmp/ig_sessions.json`` so StatReload does
not wipe the connected shop mid-demo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from secrets import token_urlsafe
from threading import Lock

DEFAULT_PERSIST_PATH = Path(".tmp/ig_sessions.json")


@dataclass
class OAuthState:
    return_to: str
    created_at: datetime


@dataclass
class InstagramSession:
    access_token: str
    account_id: str
    username: str
    created_at: datetime
    expires_at: datetime | None = None
    # Webhook recipient.id is often the IG-scoped id (/me id), while OAuth
    # stores professional user_id. Match either so outbound tokens resolve.
    alias_ids: tuple[str, ...] = ()


class InstagramSessionStore:
    """Process-local store with optional disk mirror for local demos.

    Persistence is off by default so unit tests never write fake tokens to disk.
    The live app opts in via ``persist_path=DEFAULT_PERSIST_PATH``.
    """

    def __init__(
        self,
        *,
        state_ttl_seconds: int = 600,
        persist_path: Path | None = None,
        supabase_client: object | None = None,
    ) -> None:
        self._lock = Lock()
        self._states: dict[str, OAuthState] = {}
        self._sessions: dict[str, InstagramSession] = {}
        self._state_ttl = timedelta(seconds=state_ttl_seconds)
        self._persist_path = persist_path
        self._supabase = supabase_client
        if self._persist_path is not None:
            self._load_from_disk()
        if self._supabase is not None:
            self._load_from_supabase()

    def create_state(self, *, return_to: str) -> str:
        state = token_urlsafe(24)
        with self._lock:
            self._purge_locked()
            self._states[state] = OAuthState(return_to=return_to, created_at=datetime.now(UTC))
        return state

    def consume_state(self, state: str) -> OAuthState | None:
        with self._lock:
            self._purge_locked()
            return self._states.pop(state, None)

    def create_session(
        self,
        *,
        access_token: str,
        account_id: str,
        username: str,
        expires_in: int | None = None,
        alias_ids: tuple[str, ...] | list[str] | None = None,
    ) -> str:
        session_id = token_urlsafe(32)
        now = datetime.now(UTC)
        expires_at = None
        if expires_in is not None and expires_in > 0:
            expires_at = now + timedelta(seconds=expires_in)
        aliases = tuple(
            dict.fromkeys(
                a.strip()
                for a in (alias_ids or ())
                if isinstance(a, str) and a.strip() and a.strip() != account_id
            )
        )
        with self._lock:
            self._sessions[session_id] = InstagramSession(
                access_token=access_token,
                account_id=account_id,
                username=username,
                created_at=now,
                expires_at=expires_at,
                alias_ids=aliases,
            )
            self._save_locked()
            _created = self._sessions[session_id]
        self._remote_upsert(session_id, _created)
        if self._persist_path is not None:
            try:
                Path(".tmp/ig_session_id.txt").write_text(session_id, encoding="utf-8")
            except OSError:
                pass
        return session_id

    def get(self, session_id: str) -> InstagramSession | None:
        with self._lock:
            self._purge_locked()
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.expires_at is not None and session.expires_at <= datetime.now(UTC):
                self._sessions.pop(session_id, None)
                self._save_locked()
                return None
            return session

    def find_by_account_id(self, account_id: str) -> InstagramSession | None:
        """Return any live session for this Instagram account id (webhook outbound)."""
        wanted = (account_id or "").strip()
        if not wanted:
            return None
        with self._lock:
            self._purge_locked()
            now = datetime.now(UTC)
            for session in self._sessions.values():
                ids = {session.account_id, *session.alias_ids}
                if wanted not in ids:
                    continue
                if session.expires_at is not None and session.expires_at <= now:
                    continue
                return session
            return None

    def upsert_aliases(self, session_id: str, *alias_ids: str) -> InstagramSession | None:
        """Attach extra IG ids (e.g. /me id) so webhook recipient lookup works."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            merged = list(session.alias_ids)
            for raw in alias_ids:
                alias = (raw or "").strip()
                if not alias or alias == session.account_id or alias in merged:
                    continue
                merged.append(alias)
            session.alias_ids = tuple(merged)
            self._save_locked()
            self._remote_upsert(session_id, session)
            return session

    def latest(self) -> InstagramSession | None:
        """Most recently created live session (single-shop hackathon helper)."""
        with self._lock:
            self._purge_locked()
            now = datetime.now(UTC)
            live = [
                s for s in self._sessions.values() if s.expires_at is None or s.expires_at > now
            ]
            if not live:
                return None
            return max(live, key=lambda s: s.created_at)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            removed = self._sessions.pop(session_id, None) is not None
            if removed:
                self._save_locked()
                self._remote_delete(session_id)
            return removed

    def _remote_upsert(self, session_id: str, session: InstagramSession) -> None:
        if self._supabase is None:
            return
        try:
            self._supabase.table("instagram_sessions").upsert(
                {
                    "session_id": session_id,
                    "access_token": session.access_token,
                    "account_id": session.account_id,
                    "username": session.username,
                    "alias_ids": list(session.alias_ids),
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                }
            ).execute()
        except Exception:
            pass  # Table may not exist yet (migration 0007); memory store still works.

    def _remote_delete(self, session_id: str) -> None:
        if self._supabase is None:
            return
        try:
            self._supabase.table("instagram_sessions").delete().eq(
                "session_id", session_id
            ).execute()
        except Exception:
            pass

    def _load_from_supabase(self) -> None:
        try:
            result = self._supabase.table("instagram_sessions").select("*").execute()
        except Exception:
            return
        rows = getattr(result, "data", None) or []
        now = datetime.now(UTC)
        for row in rows:
            if not isinstance(row, dict):
                continue
            session_id = str(row.get("session_id") or "").strip()
            token = str(row.get("access_token") or "").strip()
            account_id = str(row.get("account_id") or "").strip()
            if not session_id or not token or not account_id:
                continue
            expires_at = None
            raw_exp = row.get("expires_at")
            if raw_exp:
                try:
                    expires_at = datetime.fromisoformat(str(raw_exp))
                except ValueError:
                    expires_at = None
            if expires_at is not None and expires_at <= now:
                continue
            try:
                created_at = datetime.fromisoformat(str(row.get("created_at") or now.isoformat()))
            except ValueError:
                created_at = now
            raw_aliases = row.get("alias_ids") or []
            aliases = (
                [str(a).strip() for a in raw_aliases if str(a).strip()]
                if isinstance(raw_aliases, list)
                else []
            )
            self._sessions[session_id] = InstagramSession(
                access_token=token,
                account_id=account_id,
                username=str(row.get("username") or ""),
                created_at=created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC),
                expires_at=expires_at,
                alias_ids=tuple(dict.fromkeys(aliases)),
            )

    def _purge_locked(self) -> None:
        now = datetime.now(UTC)
        expired_states = [
            key for key, value in self._states.items() if now - value.created_at > self._state_ttl
        ]
        for key in expired_states:
            self._states.pop(key, None)
        expired_sessions = [
            key
            for key, value in self._sessions.items()
            if value.expires_at is not None and value.expires_at <= now
        ]
        if expired_sessions:
            for key in expired_sessions:
                self._sessions.pop(key, None)
            self._save_locked()

    def _save_locked(self) -> None:
        if self._persist_path is None:
            return
        payload = {
            "sessions": {
                sid: {
                    "access_token": session.access_token,
                    "account_id": session.account_id,
                    "username": session.username,
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                    "alias_ids": list(session.alias_ids),
                }
                for sid, session in self._sessions.items()
            }
        }
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._persist_path.write_text(json.dumps(payload), encoding="utf-8")
        except OSError:
            pass

    def _load_from_disk(self) -> None:
        path = self._persist_path
        if path is None or not path.is_file():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        rows = payload.get("sessions") if isinstance(payload, dict) else None
        if not isinstance(rows, dict):
            return
        now = datetime.now(UTC)
        for sid, row in rows.items():
            if not isinstance(row, dict):
                continue
            token = str(row.get("access_token") or "").strip()
            account_id = str(row.get("account_id") or "").strip()
            if not token or not account_id:
                continue
            try:
                created_at = datetime.fromisoformat(str(row.get("created_at") or now.isoformat()))
            except ValueError:
                created_at = now
            expires_at = None
            raw_exp = row.get("expires_at")
            if raw_exp:
                try:
                    expires_at = datetime.fromisoformat(str(raw_exp))
                except ValueError:
                    expires_at = None
            if expires_at is not None and expires_at <= now:
                continue
            raw_aliases = row.get("alias_ids") or []
            aliases: list[str] = []
            if isinstance(raw_aliases, list):
                aliases = [str(a).strip() for a in raw_aliases if str(a).strip()]
            # Older demos may have rewritten account_id to /me id and kept user_id.
            legacy_user = str(row.get("user_id") or "").strip()
            if legacy_user and legacy_user != account_id:
                aliases.append(legacy_user)
            self._sessions[str(sid)] = InstagramSession(
                access_token=token,
                account_id=account_id,
                username=str(row.get("username") or ""),
                created_at=created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC),
                expires_at=expires_at,
                alias_ids=tuple(dict.fromkeys(aliases)),
            )

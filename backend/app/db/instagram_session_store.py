"""In-memory Instagram OAuth state + seller session store.

Tokens stay server-side. The browser only keeps an opaque session id.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from threading import Lock


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


class InstagramSessionStore:
    """Process-local store for hackathon / local OAuth testing."""

    def __init__(self, *, state_ttl_seconds: int = 600) -> None:
        self._lock = Lock()
        self._states: dict[str, OAuthState] = {}
        self._sessions: dict[str, InstagramSession] = {}
        self._state_ttl = timedelta(seconds=state_ttl_seconds)

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
    ) -> str:
        session_id = token_urlsafe(32)
        now = datetime.now(UTC)
        expires_at = None
        if expires_in is not None and expires_in > 0:
            expires_at = now + timedelta(seconds=expires_in)
        with self._lock:
            self._sessions[session_id] = InstagramSession(
                access_token=access_token,
                account_id=account_id,
                username=username,
                created_at=now,
                expires_at=expires_at,
            )
        return session_id

    def get(self, session_id: str) -> InstagramSession | None:
        with self._lock:
            self._purge_locked()
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.expires_at is not None and session.expires_at <= datetime.now(UTC):
                self._sessions.pop(session_id, None)
                return None
            return session

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

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
        for key in expired_sessions:
            self._sessions.pop(key, None)

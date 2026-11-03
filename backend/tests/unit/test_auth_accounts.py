from fastapi.testclient import TestClient

from app.config import Settings
from app.db.instagram_session_store import InstagramSessionStore
from app.db.seller_account_store import MemorySellerAccountStore
from app.main import create_app

TOKEN = "test-internal-token"


def _client():
    sessions = InstagramSessionStore()
    session_id = sessions.create_session(
        access_token="tok-1", account_id="acc-1", username="sellsafe.testshop.ng"
    )
    accounts = MemorySellerAccountStore()
    app = create_app(
        settings=Settings(internal_api_token=TOKEN),
        instagram_sessions=sessions,
        seller_accounts=accounts,
    )
    return TestClient(app), session_id, accounts


def test_link_then_restore_returns_session_id() -> None:
    client, session_id, _accounts = _client()
    linked = client.post(
        "/api/auth/link",
        headers={"X-Internal-Token": TOKEN, "X-IG-Session": session_id},
        json={"user_id": "00000000-0000-0000-0000-000000000001", "email": "a@b.c"},
    )
    assert linked.status_code == 200
    assert linked.json()["linked"] is True

    restored = client.post(
        "/api/auth/restore",
        headers={"X-Internal-Token": TOKEN},
        json={"user_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert restored.status_code == 200
    body = restored.json()
    assert body["connected"] is True
    assert body["session_id"] == session_id


def test_restore_unknown_user_is_not_linked() -> None:
    client, _sid, _a = _client()
    restored = client.post(
        "/api/auth/restore",
        headers={"X-Internal-Token": TOKEN},
        json={"user_id": "00000000-0000-0000-0000-000000000099"},
    )
    assert restored.json() == {"linked": False, "connected": False}


def test_link_requires_internal_token_and_live_session() -> None:
    client, session_id, _a = _client()
    no_token = client.post(
        "/api/auth/link",
        headers={"X-IG-Session": session_id},
        json={"user_id": "u1"},
    )
    assert no_token.status_code == 401
    no_session = client.post(
        "/api/auth/link",
        headers={"X-Internal-Token": TOKEN},
        json={"user_id": "u1"},
    )
    assert no_session.status_code == 401

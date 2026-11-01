"""Instagram connect status. Never returns tokens."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.instagram_session_store import InstagramSessionStore
from app.main import create_app


def test_status_without_session_is_not_connected() -> None:
    settings = Settings(
        llm_provider="groq",
        instagram_app_id="ig-app",
        instagram_app_secret="secret",
        instagram_oauth_redirect_uri="http://localhost:3000/api/instagram/oauth/callback",
        # Legacy bot env must not fake a seller connection.
        instagram_access_token="login-token",
        instagram_account_id="17840000000000000",
    )
    response = TestClient(create_app(settings)).get("/api/instagram/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["ready"] is False
    assert body["oauth_configured"] is True
    assert "login-token" not in response.text
    assert "17840000000000000" not in response.text


def test_status_with_session_is_connected() -> None:
    sessions = InstagramSessionStore()
    session_id = sessions.create_session(
        access_token="secret-token",
        account_id="17840000000000000",
        username="adasbags",
        expires_in=3600,
    )
    settings = Settings(
        llm_provider="groq",
        instagram_app_id="ig-app",
        instagram_app_secret="secret",
        instagram_oauth_redirect_uri="http://localhost:3000/api/instagram/oauth/callback",
    )
    response = TestClient(create_app(settings, instagram_sessions=sessions)).get(
        "/api/instagram/status",
        headers={"X-IG-Session": session_id},
    )
    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert response.json()["username"] == "adasbags"
    assert "secret-token" not in response.text

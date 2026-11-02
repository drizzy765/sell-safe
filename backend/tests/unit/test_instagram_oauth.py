"""Instagram Login OAuth: start, exchange, status, disconnect."""

from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.instagram_session_store import InstagramSessionStore
from app.main import create_app


def _settings(**overrides: str) -> Settings:
    base = {
        "llm_provider": "groq",
        "instagram_app_id": "ig-app-123",
        "instagram_app_secret": "ig-secret",
        "instagram_oauth_redirect_uri": "http://localhost:3000/api/instagram/oauth/callback",
        "graph_api_version": "v21.0",
        "web_base_url": "http://localhost:3000",
    }
    base.update(overrides)
    return Settings(**base)


def _client(
    *,
    settings: Settings | None = None,
    transport: httpx.MockTransport | None = None,
    sessions: InstagramSessionStore | None = None,
) -> TestClient:
    return TestClient(
        create_app(
            settings=settings or _settings(),
            transport=transport,
            instagram_sessions=sessions or InstagramSessionStore(),
        )
    )


def test_status_not_connected_when_oauth_missing() -> None:
    client = _client(
        settings=Settings(llm_provider="groq", instagram_app_id="", instagram_app_secret="")
    )
    response = client.get("/api/instagram/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["oauth_configured"] is False
    assert body["ready"] is False
    assert "oauth" in (body.get("detail") or "").lower()


def test_status_oauth_configured_but_not_connected() -> None:
    response = _client().get("/api/instagram/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False
    assert body["oauth_configured"] is True
    assert body["ready"] is False


def test_oauth_start_returns_authorize_url_with_force_reauth() -> None:
    response = _client().get(
        "/api/instagram/oauth/start",
        params={"return_to": "/?platform=instagram", "force_reauth": "true"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "state" in body
    assert "www.instagram.com/oauth/authorize" in body["authorize_url"]
    assert "force_reauth=true" in body["authorize_url"]
    assert "client_id=ig-app-123" in body["authorize_url"]
    assert "client_id=1623" not in body["authorize_url"]  # never Facebook app id
    assert "instagram_business_basic" in body["authorize_url"]
    assert "instagram_business_manage_messages" in body["authorize_url"]


def test_oauth_start_redirect_mode() -> None:
    response = _client().get(
        "/api/instagram/oauth/start",
        params={"redirect": "true"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "www.instagram.com/oauth/authorize" in response.headers["location"]


def test_oauth_exchange_and_disconnect() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        path = request.url.path
        if path.endswith("/oauth/access_token"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "access_token": "short-lived-token",
                            "user_id": "17840000000000001",
                            "permissions": "instagram_business_basic",
                        }
                    ]
                },
            )
        if path.endswith("/access_token") and request.method == "POST":
            return httpx.Response(
                200,
                json={"access_token": "long-lived-token", "expires_in": 5184000},
            )
        if path.endswith("/me"):
            return httpx.Response(
                200,
                json={
                    "user_id": "17840000000000001",
                    "username": "adasbags",
                    "account_type": "BUSINESS",
                },
            )
        return httpx.Response(404, json={"error": {"message": "not found"}})

    sessions = InstagramSessionStore()
    client = _client(transport=httpx.MockTransport(handler), sessions=sessions)

    start = client.get("/api/instagram/oauth/start").json()
    state = start["state"]

    exchange = client.post(
        "/api/instagram/oauth/exchange",
        json={"code": "auth-code-xyz", "state": state},
    )
    assert exchange.status_code == 200
    payload = exchange.json()
    assert payload["connected"] is True
    assert payload["username"] == "adasbags"
    assert payload["account_id"] == "17840000000000001"
    assert "short-lived-token" not in exchange.text
    assert "long-lived-token" not in exchange.text
    session_id = payload["session_id"]

    status = client.get(
        "/api/instagram/status",
        headers={"X-IG-Session": session_id},
    )
    assert status.json() == {
        "connected": True,
        "oauth_configured": True,
        "username": "adasbags",
        "account_id": "17840000000000001",
        "ready": True,
        "detail": None,
        "graph_username": "adasbags",
    }

    disconnected = client.post(
        "/api/instagram/disconnect",
        headers={"X-IG-Session": session_id},
    )
    assert disconnected.status_code == 200
    assert disconnected.json()["connected"] is False

    after = client.get(
        "/api/instagram/status",
        headers={"X-IG-Session": session_id},
    )
    assert after.json()["connected"] is False
    assert after.json()["ready"] is False

    # Code exchange hit Meta; long-lived exchange must be POST (GET is rejected by Meta).
    assert any(str(req.url).endswith("/oauth/access_token") for req in seen)
    assert any(req.method == "POST" and str(req.url).endswith("/access_token") for req in seen)


def test_oauth_exchange_rejects_invalid_state() -> None:
    response = _client().post(
        "/api/instagram/oauth/exchange",
        json={"code": "x", "state": "never-issued"},
    )
    assert response.status_code == 400
    assert "state" in response.json()["detail"].lower()


def test_oauth_exchange_rejects_reused_state() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth/access_token"):
            return httpx.Response(
                200,
                json={"access_token": "t", "user_id": "1"},
            )
        if request.url.path.endswith("/access_token"):
            return httpx.Response(200, json={"access_token": "long", "expires_in": 100})
        if request.url.path.endswith("/me"):
            return httpx.Response(200, json={"user_id": "1", "username": "u"})
        return httpx.Response(404)

    client = _client(transport=httpx.MockTransport(handler))
    state = client.get("/api/instagram/oauth/start").json()["state"]
    first = client.post(
        "/api/instagram/oauth/exchange",
        json={"code": "c1", "state": state},
    )
    assert first.status_code == 200
    second = client.post(
        "/api/instagram/oauth/exchange",
        json={"code": "c2", "state": state},
    )
    assert second.status_code == 400

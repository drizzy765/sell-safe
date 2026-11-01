"""Feature 1: Confirm shop from Instagram session."""

from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.instagram_session_store import InstagramSessionStore
from app.db.shop_store import MemoryShopStore
from app.main import create_app


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        instagram_app_id="ig-app",
        instagram_app_secret="secret",
        instagram_oauth_redirect_uri="https://example.com/callback",
        graph_api_version="v21.0",
    )


def _client(transport: httpx.MockTransport, sessions: InstagramSessionStore) -> TestClient:
    return TestClient(
        create_app(
            settings=_settings(),
            transport=transport,
            instagram_sessions=sessions,
            shops=MemoryShopStore(),
        )
    )


def test_get_shop_requires_session() -> None:
    client = TestClient(create_app(settings=_settings()))
    response = client.get("/api/onboarding/shop")
    assert response.status_code == 401


def test_get_shop_fetches_instagram_profile_and_masks_nothing_yet() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/me") and "media" not in path:
            return httpx.Response(
                200,
                json={
                    "user_id": "17840000000000001",
                    "username": "sellsafe.testshop.ng",
                    "name": "Mama Timi Provisions 🛒",
                    "biography": "Fresh food for Lagos families",
                    "profile_picture_url": "https://example.com/logo.jpg",
                    "website": "https://example.com",
                    "followers_count": 1200,
                    "account_type": "BUSINESS",
                },
            )
        if path.endswith("/me/media"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "media-1",
                            "caption": "Garri ₦9,500",
                            "media_url": "https://example.com/1.jpg",
                            "media_type": "IMAGE",
                            "timestamp": "2026-11-01T10:00:00+0000",
                            "permalink": "https://instagram.com/p/1",
                        }
                    ]
                },
            )
        return httpx.Response(404)

    sessions = InstagramSessionStore()
    session_id = sessions.create_session(
        access_token="user-token",
        account_id="17840000000000001",
        username="sellsafe.testshop.ng",
        expires_in=3600,
    )
    client = _client(httpx.MockTransport(handler), sessions)
    response = client.get(
        "/api/onboarding/shop",
        headers={"X-IG-Session": session_id},
    )
    assert response.status_code == 200
    shop = response.json()["shop"]
    assert shop["handle"] == "sellsafe.testshop.ng"
    assert shop["name"] == "Mama Timi Provisions 🛒"
    assert shop["bio"].startswith("Fresh food")
    assert shop["logo_url"].endswith("logo.jpg")
    assert shop["followers_count"] == 1200
    assert shop["recent_media"][0]["id"] == "media-1"
    assert "user-token" not in response.text


def test_patch_shop_confirms_and_masks_account_number() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/me") and "media" not in request.url.path:
            return httpx.Response(
                200,
                json={
                    "user_id": "1784",
                    "username": "shop",
                    "name": "Shop",
                    "biography": "",
                    "profile_picture_url": "",
                    "followers_count": 1,
                    "account_type": "BUSINESS",
                },
            )
        if request.url.path.endswith("/me/media"):
            return httpx.Response(200, json={"data": []})
        return httpx.Response(404)

    sessions = InstagramSessionStore()
    session_id = sessions.create_session(
        access_token="tok",
        account_id="1784",
        username="shop",
        expires_in=3600,
    )
    client = _client(httpx.MockTransport(handler), sessions)
    headers = {"X-IG-Session": session_id}
    assert client.get("/api/onboarding/shop", headers=headers).status_code == 200

    patched = client.patch(
        "/api/onboarding/shop",
        headers=headers,
        json={
            "name": "Mama Timi Provisions 🛒",
            "phone": "+2348012345678",
            "location": "Lagos",
            "bank_name": "Opay",
            "account_name": "Mama Timi",
            "account_number": "1234567890",
            "languages": ["en", "yo"],
            "confirm": True,
        },
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["next"] == "/onboarding/catalog"
    shop = body["shop"]
    assert shop["confirmed"] is True
    assert shop["account_number_set"] is True
    assert shop["account_number_masked"] == "******7890"
    assert "1234567890" not in patched.text
    assert shop["languages"] == ["en", "yo"]

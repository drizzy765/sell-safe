"""Graph Conversations API → dashboard inbox sync."""

from __future__ import annotations

import json

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.echo_store import MemoryEchoStore
from app.db.instagram_session_store import InstagramSessionStore
from app.db.shop_store import MemoryShopStore, ShopProfile
from app.main import create_app


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        instagram_app_id="ig",
        instagram_app_secret="secret",
        instagram_oauth_redirect_uri="https://example.com/cb",
        graph_api_version="v21.0",
        google_drive_api_key="drive-key",
    )


def _graph_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/me/conversations"):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "conv-1",
                        "updated_time": "2026-11-02T12:00:00+0000",
                        "participants": {
                            "data": [
                                {"id": "ig-1", "username": "sellsafe.testshop.ng"},
                                {"id": "buyer-igs-22", "username": "testicles22"},
                            ]
                        },
                        "messages": {
                            "data": [
                                {
                                    "id": "mid-out-1",
                                    "created_time": "2026-11-02T12:00:00+0000",
                                    "from": {"id": "ig-1", "username": "sellsafe.testshop.ng"},
                                    "to": {
                                        "data": [{"id": "buyer-igs-22", "username": "testicles22"}]
                                    },
                                    "message": "Honey beans — ₦6,000",
                                },
                                {
                                    "id": "mid-in-1",
                                    "created_time": "2026-11-02T11:59:00+0000",
                                    "from": {"id": "buyer-igs-22", "username": "testicles22"},
                                    "to": {
                                        "data": [
                                            {
                                                "id": "ig-1",
                                                "username": "sellsafe.testshop.ng",
                                            }
                                        ]
                                    },
                                    "message": "how much be honey beans?",
                                },
                            ]
                        },
                    }
                ]
            },
        )
    return httpx.Response(404, json={"error": {"message": f"unexpected {path}"}})


def test_summary_syncs_past_instagram_dms() -> None:
    sessions = InstagramSessionStore()
    session_id = sessions.create_session(
        access_token="tok",
        account_id="ig-1",
        username="sellsafe.testshop.ng",
        expires_in=3600,
    )
    shops = MemoryShopStore()
    shops.upsert(
        ShopProfile(
            id="shop-1",
            ig_account_id="ig-1",
            handle="sellsafe.testshop.ng",
            name="Mama Timi Provisions",
            confirmed=True,
            reply_mode="auto",
        )
    )
    store = MemoryEchoStore()
    client = TestClient(
        create_app(
            settings=_settings(),
            store=store,
            transport=httpx.MockTransport(_graph_handler),
            instagram_sessions=sessions,
            shops=shops,
        )
    )

    response = client.get("/api/dashboard/summary", headers={"X-IG-Session": session_id})
    assert response.status_code == 200, response.text
    body = response.json()
    inbox = body["inbox"]
    assert len(inbox) == 1
    assert inbox[0]["buyer"] == "testicles22"
    assert "honey beans" in inbox[0]["preview"].lower() or "6,000" in inbox[0]["preview"]

    buyer_id = inbox[0]["buyer_id"]
    thread = client.get(f"/api/dashboard/inbox/{buyer_id}", headers={"X-IG-Session": session_id})
    assert thread.status_code == 200
    texts = [m["text"] for m in thread.json()["messages"]]
    assert "how much be honey beans?" in texts
    assert "Honey beans — ₦6,000" in texts


def test_sync_is_idempotent() -> None:
    sessions = InstagramSessionStore()
    session_id = sessions.create_session(
        access_token="tok",
        account_id="ig-1",
        username="sellsafe.testshop.ng",
        expires_in=3600,
    )
    shops = MemoryShopStore()
    shops.upsert(
        ShopProfile(
            id="shop-1",
            ig_account_id="ig-1",
            handle="sellsafe.testshop.ng",
            name="Mama Timi",
            confirmed=True,
        )
    )
    store = MemoryEchoStore()
    client = TestClient(
        create_app(
            settings=_settings(),
            store=store,
            transport=httpx.MockTransport(_graph_handler),
            instagram_sessions=sessions,
            shops=shops,
        )
    )
    headers = {"X-IG-Session": session_id}
    first = client.get("/api/dashboard/summary", headers=headers)
    second = client.get("/api/dashboard/summary", headers=headers)
    assert first.status_code == 200 and second.status_code == 200
    assert len(store.messages) == 2
    assert json.dumps(first.json()["inbox"], sort_keys=True) == json.dumps(
        second.json()["inbox"], sort_keys=True
    )

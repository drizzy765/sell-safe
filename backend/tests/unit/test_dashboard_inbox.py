"""Dashboard v2: real inbox only — no fake DMs by default."""

from __future__ import annotations

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


def _client() -> tuple[TestClient, str, MemoryEchoStore]:
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
            transport=httpx.MockTransport(lambda r: httpx.Response(404)),
            instagram_sessions=sessions,
            shops=shops,
        )
    )
    return client, session_id, store


def test_empty_inbox_has_no_demo_chats() -> None:
    client, session_id, _store = _client()
    response = client.get("/api/dashboard/summary", headers={"X-IG-Session": session_id})
    assert response.status_code == 200
    body = response.json()
    assert body["inbox"] == []
    assert body["demo_mode"] is False
    assert body["settings"]["reply_mode"] == "auto"


def test_real_dm_appears_in_inbox() -> None:
    client, session_id, store = _client()
    seller_id = store.ensure_seller("ig-1", channel="instagram")
    buyer_id = store.ensure_buyer("instagram", "buyer-99", display_name="adaeze_styles")
    store.save_inbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="instagram",
        external_msg_id="mid-1",
        message_type="text",
        text="Abeg how much be the honey beans?",
    )
    response = client.get("/api/dashboard/inbox", headers={"X-IG-Session": session_id})
    assert response.status_code == 200
    rows = response.json()["conversations"]
    assert len(rows) == 1
    assert rows[0]["buyer"] == "adaeze_styles"
    assert "honey beans" in rows[0]["preview"]
    assert rows[0].get("demo") is False

    thread = client.get(f"/api/dashboard/inbox/{buyer_id}", headers={"X-IG-Session": session_id})
    assert thread.status_code == 200
    messages = thread.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["text"] == "Abeg how much be the honey beans?"


def test_demo_mode_opt_in_only() -> None:
    client, session_id, _store = _client()
    patched = client.patch(
        "/api/dashboard/settings",
        headers={"X-IG-Session": session_id},
        json={"demo_mode": True},
    )
    assert patched.status_code == 200
    summary = client.get("/api/dashboard/summary", headers={"X-IG-Session": session_id})
    body = summary.json()
    assert body["demo_mode"] is True
    assert any(c.get("demo") for c in body["inbox"])

"""Feature 2: Instagram/upload import + approve drafts."""

from __future__ import annotations

import base64

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.echo_store import MemoryEchoStore
from app.db.instagram_session_store import InstagramSessionStore
from app.db.shop_store import MemoryShopStore, ShopMedia, ShopProfile
from app.main import create_app


class _FakeProvider:
    async def chat(self, messages, tools=None, json_schema=None):  # noqa: ANN001
        raise NotImplementedError

    async def vision(self, image: bytes, prompt: str, json_schema: dict) -> dict:
        return {
            "name": "Garri 2kg",
            "description": "Premium white garri",
            "suggested_price_kobo": None,
            "category": "Provisions",
            "colors": [],
            "confidence": 0.91,
        }

    async def transcribe(self, audio: bytes) -> str:
        return ""


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        instagram_app_id="ig",
        instagram_app_secret="secret",
        instagram_oauth_redirect_uri="https://example.com/cb",
        graph_api_version="v21.0",
    )


def _ready_client() -> tuple[TestClient, str]:
    sessions = InstagramSessionStore()
    session_id = sessions.create_session(
        access_token="tok",
        account_id="ig-1",
        username="mama",
        expires_in=3600,
    )
    shops = MemoryShopStore()
    shops.upsert(
        ShopProfile(
            id="shop-1",
            ig_account_id="ig-1",
            handle="mama",
            name="Mama Timi Provisions",
            confirmed=True,
            recent_media=[
                ShopMedia(
                    id="media-1",
                    caption="Garri ₦9,500 fresh",
                    media_url="https://cdn.example/garri.jpg",
                    thumbnail_url="https://cdn.example/garri.jpg",
                ),
                ShopMedia(
                    id="media-2",
                    caption="Beans DM for price",
                    media_url="https://cdn.example/beans.jpg",
                    thumbnail_url="https://cdn.example/beans.jpg",
                ),
            ],
        )
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "cdn.example":
            return httpx.Response(200, content=b"jpeg-bytes")
        return httpx.Response(404)

    client = TestClient(
        create_app(
            settings=_settings(),
            store=MemoryEchoStore(),
            transport=httpx.MockTransport(handler),
            provider=_FakeProvider(),
            instagram_sessions=sessions,
            shops=shops,
        )
    )
    return client, session_id


def test_import_instagram_and_approve() -> None:
    client, session_id = _ready_client()
    headers = {"X-IG-Session": session_id}

    imported = client.post(
        "/api/onboarding/catalog/import/instagram",
        headers=headers,
        json={"media_ids": ["media-1", "media-2"]},
    )
    assert imported.status_code == 200
    drafts = imported.json()["drafts"]
    assert len(drafts) == 2
    priced = next(d for d in drafts if d["source_ref"] == "media-1")
    assert priced["price_ngn"] == 9500
    assert priced["name"] == "Garri 2kg"
    flagged = next(d for d in drafts if d["source_ref"] == "media-2")
    assert flagged["price_ngn"] is None
    assert "dm_for_price" in flagged["flags"]

    approve = client.post(
        "/api/onboarding/catalog/drafts/approve",
        headers=headers,
        json={"ids": [priced["id"], flagged["id"]]},
    )
    assert approve.status_code == 200
    body = approve.json()
    assert len(body["approved"]) == 1
    assert len(body["skipped"]) == 1
    assert body["skipped"][0]["detail"] == "missing price"

    products = client.get("/api/onboarding/catalog/products", headers=headers)
    assert products.status_code == 200
    assert len(products.json()["products"]) == 1


def test_upload_import() -> None:
    client, session_id = _ready_client()
    headers = {"X-IG-Session": session_id}
    payload = base64.b64encode(b"png-bytes").decode("ascii")
    response = client.post(
        "/api/onboarding/catalog/import/upload",
        headers=headers,
        json={
            "items": [
                {
                    "filename": "oil.png",
                    "content_base64": payload,
                    "caption": "Groundnut oil ₦4,500",
                }
            ]
        },
    )
    assert response.status_code == 200
    drafts = response.json()["drafts"]
    assert len(drafts) == 1
    assert drafts[0]["price_ngn"] == 4500
    assert drafts[0]["source"] == "upload"

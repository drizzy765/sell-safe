import hashlib
import hmac
import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider
from app.main import create_app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"
SECRET = "test-app-secret"


def _settings() -> Settings:
    return Settings(
        llm_provider="groq",
        meta_app_secret=SECRET,
        meta_verify_token="verify-me",
        whatsapp_access_token="test-token",
        whatsapp_phone_number_id="1234567890",
        graph_api_version="v21.0",
    )


def _sign(raw: bytes) -> str:
    digest = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post(client: TestClient, name: str, text: str) -> None:
    payload = json.loads((FIXTURES / "text.json").read_text(encoding="utf-8"))
    payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = text
    payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = f"wamid.{name}"
    raw = json.dumps(payload).encode()
    headers = {"X-Hub-Signature-256": _sign(raw), "content-type": "application/json"}
    response = client.post("/webhooks/whatsapp", content=raw, headers=headers)
    assert response.status_code == 200


def test_buyer_asks_price_and_places_order_in_pidgin() -> None:
    store = MemoryEchoStore()
    catalog = MemoryCatalogStore()
    orders = MemoryOrderStore()
    catalog.products.append(
        {
            "id": "p1",
            "seller_id": "s1",
            "name": "Black tote",
            "description": "Leather bag",
            "price_kobo": 1_500_000,
        }
    )

    sent: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request.content)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})

    provider = FakeProvider(
        chat=[
            {
                "text": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "name": "search_catalog",
                        "arguments": '{"query":"black tote"}',
                    }
                ],
            },
            {"text": "The black tote is ₦15,000."},
            {
                "text": "",
                "tool_calls": [
                    {
                        "id": "call-2",
                        "name": "search_catalog",
                        "arguments": '{"query":"black tote"}',
                    },
                    {
                        "id": "call-3",
                        "name": "create_order",
                        "arguments": (
                            '{"items":[{"product_id":"p1","qty":1,"unit_price_kobo":1500000}]}'
                        ),
                    },
                ],
            },
            {"text": "Order SS-1001 created. Total ₦15,000."},
        ]
    )

    app = create_app(
        _settings(),
        store=store,
        transport=httpx.MockTransport(handler),
        provider=provider,
        jev=FakeJev(intent="price_question", language="pcm"),
        catalog=catalog,
        orders=orders,
    )
    client = TestClient(app)

    _post(client, "price", "Abeg how much for the black tote?")
    assert "15,000" in json.loads(sent[0])["text"]["body"]

    _post(client, "order", "I go take 1")
    assert orders.orders
    assert orders.orders[0]["status"] == "awaiting_payment"
    assert orders.orders[0]["total_kobo"] == 1_500_000
    assert orders.orders[0]["ref"].startswith("SS-")
    assert orders.orders[0]["ref"] in json.loads(sent[1])["text"]["body"]

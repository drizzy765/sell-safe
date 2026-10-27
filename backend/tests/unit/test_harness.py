from datetime import UTC, datetime

import pytest

from app.agent.graph.harness import run_turn
from app.agent.graph.state import State
from app.channels.base import InboundMessage
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider


def _message(text: str) -> InboundMessage:
    return InboundMessage(
        channel="whatsapp",
        external_id="wamid.test",
        sender_id="15550000001",
        type="text",
        text=text,
        ts=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_price_question_searches_catalog_and_replies_with_price() -> None:
    catalog = MemoryCatalogStore()
    catalog.products.append(
        {
            "id": "p1",
            "seller_id": "s1",
            "name": "Black tote",
            "price_kobo": 15000,
        }
    )
    orders = MemoryOrderStore()
    store = MemoryEchoStore()
    store.seller_languages["s1"] = "en"
    jev = FakeJev(intent="price_question", language="en")

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
            {"text": "The black tote is ₦150."},
        ]
    )

    state = await run_turn(
        _message("How much is the black tote?"),
        seller_id="s1",
        buyer_id="b1",
        channel_adapter=_FakeAdapter(),
        store=store,
        jev=jev,
        provider=provider,
        catalog_store=catalog,
        order_store=orders,
        payment_store=MemoryPaymentStore(),
    )

    assert isinstance(state, State)
    assert "150" in state.reply
    assert provider.chat_calls == 2  # tool call + final


class _FakeAdapter:
    name = "whatsapp"

    async def send_text(self, to: str, text: str) -> str:
        return "wamid.out"

    async def send_image(self, to: str, url: str, caption: str) -> str:
        return "wamid.out"

    async def fetch_media(self, media_id: str) -> bytes:
        return b""

    def verify_signature(self, raw: bytes, headers: object) -> bool:
        return True

    def parse(self, payload: dict) -> list:
        return []

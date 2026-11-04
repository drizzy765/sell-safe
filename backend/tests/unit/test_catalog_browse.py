from datetime import UTC, datetime

import pytest

from app.agent.graph.harness import is_catalog_browse_request, run_turn
from app.channels.base import InboundMessage
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider


def test_catalog_browse_phrases_en_and_pidgin() -> None:
    assert is_catalog_browse_request("wetin dey your catalog? send picture if you fit")
    assert is_catalog_browse_request("i wan buy something wetin you get")
    assert is_catalog_browse_request("What do you have?")
    assert not is_catalog_browse_request("How much is the black tote?")


class _FakeAdapter:
    name = "whatsapp"

    async def send_text(self, to: str, text: str) -> str:
        return "msg-1"


@pytest.mark.asyncio
async def test_pidgin_browse_lists_catalog_without_llm() -> None:
    catalog = MemoryCatalogStore()
    catalog.products.append(
        {"id": "p1", "seller_id": "s1", "name": "Tomato Paste Carton", "price_kobo": 1_600_000}
    )
    store = MemoryEchoStore()
    store.seller_languages["s1"] = "pcm"
    provider = FakeProvider()
    state = await run_turn(
        InboundMessage(
            channel="instagram",
            external_id="m1",
            sender_id="buyer1",
            type="text",
            text="wetin dey your catalog? send picture if you fit",
            ts=datetime.now(UTC),
        ),
        seller_id="s1",
        buyer_id="b1",
        channel_adapter=_FakeAdapter(),
        store=store,
        jev=FakeJev(intent="unknown", language="pcm"),
        provider=provider,
        catalog_store=catalog,
        order_store=MemoryOrderStore(),
        payment_store=MemoryPaymentStore(),
    )
    assert state.intent == "catalog_browse"
    assert "Tomato Paste Carton" in state.reply
    assert "₦16,000" in state.reply
    assert provider.chat_calls == 0

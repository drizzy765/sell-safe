"""Official Sell-Safe IG page: connect reply only, never catalog."""

from datetime import UTC, datetime

import pytest

from app.agent.graph.harness import run_turn
from app.agent.official_page import (
    is_official_ig_account,
    parse_official_ig_account_ids,
)
from app.agent.templates import official_connect_reply
from app.channels.base import InboundMessage
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider


def test_parse_official_ids() -> None:
    assert parse_official_ig_account_ids("111, 222") == frozenset({"111", "222"})
    assert is_official_ig_account("111", official_ids=frozenset({"111", "222"}))
    assert not is_official_ig_account("999", official_ids=frozenset({"111"}))


def test_official_connect_reply_includes_site_and_connect_steps() -> None:
    text = official_connect_reply("https://sellsafe.ng")
    assert "https://sellsafe.ng" in text
    assert "Connect your Instagram" in text
    assert "catalog" in text.lower()
    assert "does not sell products" in text.lower()


class _Settings:
    sellsafe_official_ig_account_ids = "29855683307365684,17841412608367416"
    sellsafe_site_url = "https://sellsafe.ng"
    web_base_url = ""
    app_base_url = ""


class _FakeAdapter:
    name = "instagram"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_text(self, to: str, text: str) -> str:
        self.sent.append((to, text))
        return "mid-official"


@pytest.mark.asyncio
async def test_official_page_skips_catalog_and_llm() -> None:
    catalog = MemoryCatalogStore()
    catalog.products.append(
        {
            "id": "p1",
            "seller_id": "29855683307365684",
            "name": "Honey beans",
            "price_kobo": 600_000,
        }
    )
    store = MemoryEchoStore()
    adapter = _FakeAdapter()
    provider = FakeProvider(chat=[{"text": "Honey beans are ₦6,000"}])
    jev = FakeJev(intent="price_question", language="en")

    state = await run_turn(
        InboundMessage(
            channel="instagram",
            external_id="ig.official.1",
            sender_id="buyer-1",
            type="text",
            text="How much is honey beans?",
            ts=datetime.now(UTC),
        ),
        seller_id="29855683307365684",
        buyer_id="b1",
        channel_adapter=adapter,
        store=store,
        jev=jev,
        provider=provider,
        catalog_store=catalog,
        order_store=MemoryOrderStore(),
        payment_store=MemoryPaymentStore(),
        settings=_Settings(),
    )

    assert state.intent == "official_connect"
    assert "sellsafe.ng" in (state.reply or "").lower()
    assert "₦6,000" not in (state.reply or "")
    assert "Honey beans are" not in (state.reply or "")
    assert provider.chat_calls == 0
    assert len(adapter.sent) == 1
    assert "Connect your Instagram" in adapter.sent[0][1]

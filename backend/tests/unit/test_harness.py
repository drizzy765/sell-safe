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


class _RaisingProvider:
    """Simulates an LLM provider HTTP failure (e.g. Groq 400 on Render)."""

    async def chat(self, messages, tools=None, json_schema=None):
        raise RuntimeError("Groq request failed (400): simulated")

    async def vision(self, image, prompt, json_schema):
        raise RuntimeError("Groq request failed (400): simulated")

    async def transcribe(self, audio):
        raise RuntimeError("Groq request failed (400): simulated")


@pytest.mark.asyncio
async def test_provider_failure_still_replies_with_fallback() -> None:
    """Regression: a provider 400 must not leave the buyer with silence."""
    catalog = MemoryCatalogStore()
    store = MemoryEchoStore()
    store.seller_languages["s1"] = "en"
    jev = FakeJev(intent="chit_chat", language="en")

    state = await run_turn(
        _message("Hi"),
        seller_id="s1",
        buyer_id="b1",
        channel_adapter=_FakeAdapter(),
        store=store,
        jev=jev,
        provider=_RaisingProvider(),
        catalog_store=catalog,
        order_store=MemoryOrderStore(),
        payment_store=MemoryPaymentStore(),
    )

    assert state.reply  # fallback text, not an exception / empty reply
    assert state.errors  # failure is recorded for logs


@pytest.mark.asyncio
async def test_account_number_request_replies_with_saved_payout_even_if_misrouted() -> None:
    """Buyers asking for account number must get the saved details directly.

    Regression: 'What's the business account number' depended on Jev routing
    plus LLM tool choice, and buyers got 'I'm not sure I understood'.
    """
    from app.db.shop_store import MemoryShopStore, ShopProfile

    shops = MemoryShopStore()
    shops.upsert(
        ShopProfile(
            id="shop1",
            ig_account_id="s1",
            handle="sellsafe.testshop.ng",
            name="Mama Timi Provisions",
            bank_name="OPay",
            account_name="Mama Timi",
            account_number="8012345678",
        )
    )
    store = MemoryEchoStore()
    store.seller_languages["s1"] = "en"
    jev = FakeJev(intent="unknown", language="en")  # worst case: Jev misses it

    state = await run_turn(
        _message("What's the business account number"),
        seller_id="s1",
        buyer_id="b1",
        channel_adapter=_FakeAdapter(),
        store=store,
        jev=jev,
        provider=_RaisingProvider(),  # must not need the LLM at all
        catalog_store=MemoryCatalogStore(),
        order_store=MemoryOrderStore(),
        payment_store=MemoryPaymentStore(),
        shop_store=shops,
    )

    assert state.intent == "payment_details"
    assert "8012345678" in state.reply
    assert "Mama Timi" in state.reply


@pytest.mark.asyncio
async def test_account_number_request_without_payout_says_not_configured() -> None:
    store = MemoryEchoStore()
    store.seller_languages["s1"] = "en"
    jev = FakeJev(intent="chit_chat", language="en")

    state = await run_turn(
        _message("account number want to make a purchase"),
        seller_id="s1",
        buyer_id="b1",
        channel_adapter=_FakeAdapter(),
        store=store,
        jev=jev,
        provider=_RaisingProvider(),
        catalog_store=MemoryCatalogStore(),
        order_store=MemoryOrderStore(),
        payment_store=MemoryPaymentStore(),
    )

    assert state.intent == "payment_details"
    assert state.reply
    assert "8012" not in state.reply  # never invent a number

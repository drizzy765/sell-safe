from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.agent.templates import fallback_ask_type
from app.agent.voice import handle_voice_note
from app.channels.base import InboundMessage
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider
from app.speech.fake import FakeSpeechClient


def _audio_message(*, channel: str = "whatsapp") -> InboundMessage:
    return InboundMessage(
        channel=channel,  # type: ignore[arg-type]
        external_id="msg-audio-1",
        sender_id="buyer-1",
        type="audio",
        media_id="https://cdn.example/voice.ogg",
        ts=datetime.now(tz=UTC),
    )


@pytest.mark.asyncio
async def test_voice_note_persists_asr_and_creates_order() -> None:
    store = MemoryEchoStore()
    catalog = MemoryCatalogStore()
    orders = MemoryOrderStore()
    seller_id = store.ensure_seller("wa-1")
    buyer_id = store.ensure_buyer("whatsapp", "buyer-1")
    catalog.products.append(
        {
            "id": "p1",
            "seller_id": seller_id,
            "name": "Black tote",
            "price_kobo": 1_500_000,
        }
    )
    store.save_inbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id="msg-audio-1",
        message_type="audio",
        text=None,
    )

    adapter = AsyncMock()
    adapter.fetch_media = AsyncMock(return_value=b"ogg-bytes")
    adapter.send_text = AsyncMock(return_value="out-1")

    provider = FakeProvider(
        chat=[
            {
                "text": "",
                "tool_calls": [
                    {
                        "id": "call-1",
                        "name": "search_catalog",
                        "arguments": '{"query":"black tote"}',
                    },
                    {
                        "id": "call-2",
                        "name": "create_order",
                        "arguments": (
                            '{"items":[{"product_id":"p1","qty":1,"unit_price_kobo":1500000}]}'
                        ),
                    },
                ],
            },
            {"text": "Order created."},
        ]
    )
    speech = FakeSpeechClient(
        text="I want the black tote",
        language="pcm",
        confidence=0.88,
    )

    await handle_voice_note(
        adapter=adapter,
        speech=speech,
        store=store,
        jev=FakeJev(intent="order", language="pcm"),
        provider=provider,
        catalog_store=catalog,
        order_store=orders,
        seller_id=seller_id,
        buyer_id=buyer_id,
        message=_audio_message(),
    )

    saved = store.messages["msg-audio-1"]
    assert saved["transcript"] == "I want the black tote"
    assert saved["language"] == "pcm"
    assert saved["asr_confidence"] == 0.88
    assert orders.orders
    assert orders.orders[0]["status"] == "awaiting_payment"
    adapter.fetch_media.assert_awaited_once()
    # Audio bytes must never appear in store text fields beyond the transcript.
    assert b"ogg-bytes" not in repr(store.messages).encode()


@pytest.mark.asyncio
async def test_voice_note_stt_failure_asks_to_type() -> None:
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("wa-1")
    buyer_id = store.ensure_buyer("whatsapp", "buyer-1")
    store.seller_languages[seller_id] = "en"

    adapter = AsyncMock()
    adapter.fetch_media = AsyncMock(return_value=b"ogg-bytes")
    adapter.send_text = AsyncMock(return_value="out-1")

    await handle_voice_note(
        adapter=adapter,
        speech=FakeSpeechClient(fail=True),
        store=store,
        jev=FakeJev(),
        provider=_FailingProvider(chat_text="should not run"),
        catalog_store=MemoryCatalogStore(),
        order_store=MemoryOrderStore(),
        seller_id=seller_id,
        buyer_id=buyer_id,
        message=_audio_message(),
    )

    adapter.send_text.assert_awaited_once_with("buyer-1", fallback_ask_type("en"))


@pytest.mark.asyncio
async def test_voice_note_empty_transcript_asks_to_type() -> None:
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("wa-1")
    buyer_id = store.ensure_buyer("whatsapp", "buyer-1")
    store.seller_languages[seller_id] = "pcm"

    adapter = AsyncMock()
    adapter.fetch_media = AsyncMock(return_value=b"ogg-bytes")
    adapter.send_text = AsyncMock(return_value="out-1")

    await handle_voice_note(
        adapter=adapter,
        speech=FakeSpeechClient(text="   "),
        store=store,
        jev=FakeJev(),
        provider=_FailingProvider(chat_text="should not run"),
        catalog_store=MemoryCatalogStore(),
        order_store=MemoryOrderStore(),
        seller_id=seller_id,
        buyer_id=buyer_id,
        message=_audio_message(),
    )

    adapter.send_text.assert_awaited_once_with("buyer-1", fallback_ask_type("pcm"))


class _FailingProvider(FakeProvider):
    async def transcribe(self, audio: bytes) -> str:
        raise RuntimeError("fallback stt failed")


@pytest.mark.asyncio
async def test_voice_note_falls_back_to_provider_transcribe_when_intron_fails() -> None:
    """Intron outage must not silence voice notes: the LLM provider's
    transcription (Meta delegates to Groq Whisper) is the backup."""
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("wa-1")
    buyer_id = store.ensure_buyer("instagram", "buyer-1")
    store.seller_languages[seller_id] = "en"

    adapter = AsyncMock()
    adapter.fetch_media = AsyncMock(return_value=b"ogg-bytes")
    adapter.send_text = AsyncMock(return_value="out-1")

    await handle_voice_note(
        adapter=adapter,
        speech=FakeSpeechClient(fail=True),
        store=store,
        jev=FakeJev(intent="chit_chat", language="en"),
        provider=FakeProvider(chat_text="Hello! How can I help you today?"),
        catalog_store=MemoryCatalogStore(),
        order_store=MemoryOrderStore(),
        seller_id=seller_id,
        buyer_id=buyer_id,
        message=_audio_message(channel="instagram"),
    )

    sent = [call.args[1] for call in adapter.send_text.await_args_list if len(call.args) > 1]
    assert fallback_ask_type("en") not in sent
    saved = store.messages["msg-audio-1"]
    assert saved["media_path"] == "https://cdn.example/voice.ogg"


@pytest.mark.asyncio
async def test_voice_note_both_transcribers_fail_asks_to_type() -> None:
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("wa-1")
    buyer_id = store.ensure_buyer("whatsapp", "buyer-1")
    store.seller_languages[seller_id] = "en"

    adapter = AsyncMock()
    adapter.fetch_media = AsyncMock(return_value=b"ogg-bytes")
    adapter.send_text = AsyncMock(return_value="out-1")

    await handle_voice_note(
        adapter=adapter,
        speech=FakeSpeechClient(fail=True),
        store=store,
        jev=FakeJev(),
        provider=_FailingProvider(chat_text="unused"),
        catalog_store=MemoryCatalogStore(),
        order_store=MemoryOrderStore(),
        seller_id=seller_id,
        buyer_id=buyer_id,
        message=_audio_message(),
    )

    adapter.send_text.assert_awaited_once_with("buyer-1", fallback_ask_type("en"))

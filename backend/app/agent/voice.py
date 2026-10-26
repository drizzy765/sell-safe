"""Voice note handling: transcribe with Intron, then treat as text."""

from app.agent.graph.harness import run_turn
from app.agent.templates import fallback_ask_type
from app.channels.base import ChannelAdapter, InboundMessage
from app.db.catalog_store import CatalogStore
from app.db.echo_store import EchoStore
from app.db.orders import OrderStore
from app.decisions.base import JevClient
from app.llm.base import LLMProvider
from app.speech.base import SpeechClient


async def handle_voice_note(
    *,
    adapter: ChannelAdapter,
    speech: SpeechClient,
    store: EchoStore,
    jev: JevClient,
    provider: LLMProvider,
    catalog_store: CatalogStore,
    order_store: OrderStore,
    seller_id: str,
    buyer_id: str,
    message: InboundMessage,
    business_name: str | None = None,
) -> None:
    if not message.media_id:
        return
    try:
        audio = await adapter.fetch_media(message.media_id)
        result = await speech.transcribe(audio, language_hint=None)
    except Exception:
        language = store.get_seller_language(seller_id)
        await adapter.send_text(message.sender_id, fallback_ask_type(language))
        return

    if not result.text:
        language = store.get_seller_language(seller_id)
        await adapter.send_text(message.sender_id, fallback_ask_type(language))
        return

    text_message = InboundMessage(
        channel=message.channel,
        external_id=f"{message.external_id}-transcript",
        sender_id=message.sender_id,
        seller_id=message.seller_id,
        type="text",
        text=result.text,
        ts=message.ts,
    )
    await run_turn(
        text_message,
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel_adapter=adapter,
        store=store,
        jev=jev,
        provider=provider,
        catalog_store=catalog_store,
        order_store=order_store,
        business_name=business_name,
    )

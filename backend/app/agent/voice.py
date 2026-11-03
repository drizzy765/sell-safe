"""Voice note handling: transcribe with Intron, then treat as text."""

import logging

from app.agent.graph.harness import run_turn
from app.agent.templates import fallback_ask_type
from app.channels.base import ChannelAdapter, InboundMessage
from app.db.catalog_store import CatalogStore
from app.db.echo_store import EchoStore
from app.db.orders import OrderStore
from app.decisions.base import JevClient
from app.llm.base import LLMProvider
from app.speech.base import SpeechClient, TranscriptResult

logger = logging.getLogger(__name__)


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

    language = store.get_seller_language(seller_id)
    try:
        # Never log audio bytes.
        audio = await adapter.fetch_media(message.media_id)
    except Exception:
        await adapter.send_text(message.sender_id, fallback_ask_type(language))
        return

    result: TranscriptResult | None = None
    try:
        result = await speech.transcribe(audio, language_hint=None)
    except Exception:
        logger.exception("Primary STT (Intron) failed; trying provider fallback")
    if result is None or not (result.text or "").strip():
        # Fallback: the LLM provider's transcription. Meta Muse has no STT,
        # so MetaProvider delegates to Groq Whisper when configured.
        try:
            fallback_text = await provider.transcribe(audio)
            if (fallback_text or "").strip():
                result = TranscriptResult(text=fallback_text, language=language, confidence=None)
        except Exception:
            logger.exception("Fallback STT (provider) failed")

    if result is None:
        await adapter.send_text(message.sender_id, fallback_ask_type(language))
        return

    transcript = (result.text or "").strip()
    if not transcript:
        await adapter.send_text(message.sender_id, fallback_ask_type(language))
        return

    store.save_inbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel=message.channel,
        external_msg_id=message.external_id,
        message_type=message.type,
        text=transcript,
        language=result.language,
        transcript=transcript,
        asr_confidence=result.confidence,
        media_path=message.media_id,
    )

    text_message = InboundMessage(
        channel=message.channel,
        external_id=f"{message.external_id}-transcript",
        sender_id=message.sender_id,
        seller_id=message.seller_id,
        type="text",
        text=transcript,
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

"""Save a product photo only after the seller replies with a naira price."""

from app.agent.catalog import AskSeller, extract_catalog
from app.agent.templates import (
    ask_price,
    ask_price_again,
    ask_seller_reread,
    parse_naira,
    saved_product,
)
from app.channels.base import InboundMessage
from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.db.catalog_store import CatalogStore
from app.db.storage import ObjectStorage
from app.llm.base import LLMProvider


async def handle_product_photo(
    *,
    adapter: WhatsAppAdapter,
    provider: LLMProvider,
    storage: ObjectStorage,
    catalog: CatalogStore,
    seller_id: str,
    buyer_id: str,
    message: InboundMessage,
) -> None:
    if not message.media_id:
        return
    image = await adapter.fetch_media(message.media_id)
    extracted = await extract_catalog(provider, image)
    if isinstance(extracted, AskSeller):
        await adapter.send_text(message.sender_id, ask_seller_reread())
        return
    path = f"{seller_id}/{message.external_id}.jpg"
    storage.upload(path, image, "image/jpeg")
    catalog.save_draft(
        seller_id=seller_id,
        buyer_id=buyer_id,
        image_path=path,
        extraction=extracted.model_dump(),
    )
    await adapter.send_text(message.sender_id, ask_price(extracted.name))


async def handle_price_reply(
    *,
    adapter: WhatsAppAdapter,
    catalog: CatalogStore,
    seller_id: str,
    buyer_id: str,
    sender_id: str,
    text: str,
) -> bool:
    """Confirm a pending draft. Returns False when there is nothing pending."""
    draft = catalog.pending_draft(seller_id, buyer_id)
    if draft is None:
        return False
    naira = parse_naira(text)
    if naira is None:
        await adapter.send_text(sender_id, ask_price_again())
        return True
    product = catalog.save_product(seller_id, buyer_id, naira * 100)
    if product is None:
        return True
    await adapter.send_text(sender_id, saved_product(product["name"], product["price_kobo"]))
    return True

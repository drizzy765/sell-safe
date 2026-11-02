"""Meta verify handshake, WhatsApp, and Instagram messaging webhooks."""

import hmac
import json

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.agent.graph.harness import run_turn
from app.agent.graph.verify import verify_payment_turn
from app.agent.listing import handle_price_reply, handle_product_photo
from app.agent.official_page import (
    connect_reply_for_settings,
    is_official_ig_account,
    official_ids_from_settings,
)
from app.agent.voice import handle_voice_note
from app.api.webhooks.alerts import router as alerts_router
from app.api.webhooks.flutterwave import router as flutterwave_router
from app.api.webhooks.paystack import router as paystack_router
from app.channels.base import ChannelAdapter, InboundMessage
from app.channels.instagram.adapter import InstagramAdapter
from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.db.catalog_store import CatalogStore, MemoryCatalogStore, build_catalog_store
from app.db.echo_store import EchoStore, MemoryEchoStore, build_store
from app.db.fraud_store import FraudStore, MemoryFraudStore, build_fraud_store
from app.db.orders import MemoryOrderStore, OrderStore, build_order_store
from app.db.payments import MemoryPaymentStore, PaymentStore, build_payment_store
from app.db.storage import MemoryStorage, ObjectStorage, build_storage
from app.decisions.base import JevClient
from app.decisions.factory import build_jev
from app.llm.base import LLMProvider
from app.llm.factory import build_provider
from app.payments.crypto.handle import extract_tx_hash, handle_crypto_hash
from app.payments.crypto.store import MemoryCryptoStore
from app.speech.base import SpeechClient
from app.speech.factory import build_speech

router = APIRouter()


def _supabase_ready(settings: object) -> bool:
    return bool(
        getattr(settings, "supabase_url", "") and getattr(settings, "supabase_service_role_key", "")
    )


def _store(request: Request) -> EchoStore:
    current = request.app.state.store
    if current is None:
        settings = request.app.state.settings
        if _supabase_ready(settings):
            current = build_store(settings)
        else:
            current = MemoryEchoStore()
        request.app.state.store = current
    return current


def _whatsapp_adapter(request: Request) -> WhatsAppAdapter:
    return WhatsAppAdapter(request.app.state.settings, transport=request.app.state.transport)


def _instagram_adapter(request: Request) -> InstagramAdapter:
    return InstagramAdapter(request.app.state.settings, transport=request.app.state.transport)


def _provider(request: Request) -> LLMProvider:
    current = request.app.state.provider
    if current is None:
        current = build_provider(request.app.state.settings)
        request.app.state.provider = current
    return current


def _catalog(request: Request) -> CatalogStore:
    current = request.app.state.catalog
    if current is None:
        settings = request.app.state.settings
        if _supabase_ready(settings):
            current = build_catalog_store(settings)
        else:
            current = MemoryCatalogStore()
        request.app.state.catalog = current
    return current


def _storage(request: Request) -> ObjectStorage:
    current = request.app.state.storage
    if current is None:
        settings = request.app.state.settings
        bucket = getattr(settings, "supabase_storage_bucket", "")
        if _supabase_ready(settings) and bucket:
            current = build_storage(settings)
        else:
            current = MemoryStorage()
        request.app.state.storage = current
    return current


def _jev(request: Request) -> JevClient:
    current = request.app.state.jev
    if current is None:
        current = build_jev(request.app.state.settings)
        request.app.state.jev = current
    return current


def _orders(request: Request) -> OrderStore:
    current = request.app.state.orders
    if current is None:
        settings = request.app.state.settings
        if _supabase_ready(settings):
            current = build_order_store(settings)
        else:
            current = MemoryOrderStore()
        request.app.state.orders = current
    return current


def _payments(request: Request) -> PaymentStore:
    current = getattr(request.app.state, "payments", None)
    if current is None:
        settings = request.app.state.settings
        if _supabase_ready(settings):
            current = build_payment_store(settings)
        else:
            current = MemoryPaymentStore()
        request.app.state.payments = current
    return current


def _speech(request: Request) -> SpeechClient:
    current = request.app.state.speech
    if current is None:
        current = build_speech(request.app.state.settings)
        request.app.state.speech = current
    return current


def _fraud(request: Request) -> FraudStore:
    current = getattr(request.app.state, "fraud", None)
    if current is None:
        settings = request.app.state.settings
        if settings.supabase_url and settings.supabase_service_role_key:
            current = build_fraud_store(settings)
        else:
            current = MemoryFraudStore()
        request.app.state.fraud = current
    return current


def _tokens_match(token: str | None, expected: str) -> bool:
    if not token or not expected:
        return False
    token_b = token.encode()
    expected_b = expected.encode()
    if len(token_b) != len(expected_b):
        return False
    return hmac.compare_digest(token_b, expected_b)


def _handshake(request: Request) -> Response:
    settings = request.app.state.settings
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if (
        mode == "subscribe"
        and challenge is not None
        and _tokens_match(token, settings.meta_verify_token)
    ):
        return PlainTextResponse(challenge)
    return Response(status_code=403)


@router.get("/webhooks/meta")
def meta_verify(request: Request) -> Response:
    return _handshake(request)


@router.get("/webhooks/instagram")
def instagram_verify(request: Request) -> Response:
    return _handshake(request)


def _dispatch_inbound(
    *,
    request: Request,
    background: BackgroundTasks,
    adapter: ChannelAdapter,
    store: EchoStore,
    message: InboundMessage,
    seller_id: str,
    buyer_id: str,
    channel: str,
) -> None:
    settings = request.app.state.settings
    saved = store.save_inbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel=channel,
        external_msg_id=message.external_id,
        message_type=message.type,
        text=message.text,
        media_path=message.media_id,
    )
    if not saved:
        return
    inbox_control = getattr(request.app.state, "inbox_control", None)
    if inbox_control is not None:
        inbox_control.mark_inbound(
            seller_id,
            buyer_id,
            at=message.ts.isoformat() if getattr(message, "ts", None) else None,
        )

    # Official Sell-Safe IG page: connect CTA only (no catalog / payments / listing).
    if channel == "instagram" and is_official_ig_account(
        seller_id, official_ids=official_ids_from_settings(settings)
    ):
        background.add_task(
            _reply_official_connect,
            adapter=adapter,
            store=store,
            seller_id=seller_id,
            buyer_id=buyer_id,
            sender_id=message.sender_id,
            reply=connect_reply_for_settings(settings),
        )
        return

    if message.type == "image":
        catalog = _catalog(request)
        if _orders(request).get_open_order(seller_id, buyer_id):
            background.add_task(
                verify_payment_turn,
                message=message,
                seller_id=seller_id,
                buyer_id=buyer_id,
                channel_adapter=adapter,
                store=store,
                order_store=_orders(request),
                payment_store=_payments(request),
                provider=_provider(request),
                jev=_jev(request),
                pii_salt=settings.pii_salt,
                fraud_store=_fraud(request),
            )
        else:
            background.add_task(
                handle_product_photo,
                adapter=adapter,
                provider=_provider(request),
                storage=_storage(request),
                catalog=catalog,
                seller_id=seller_id,
                buyer_id=buyer_id,
                message=message,
            )
        return
    if message.type == "audio":
        background.add_task(
            handle_voice_note,
            adapter=adapter,
            speech=_speech(request),
            store=store,
            jev=_jev(request),
            provider=_provider(request),
            catalog_store=_catalog(request),
            order_store=_orders(request),
            seller_id=seller_id,
            buyer_id=buyer_id,
            message=message,
        )
        return
    if message.type == "text" and message.text and extract_tx_hash(message.text):
        crypto_store = getattr(request.app.state, "crypto_payments", None)
        if crypto_store is None:
            crypto_store = MemoryCryptoStore()
            request.app.state.crypto_payments = crypto_store
        background.add_task(
            handle_crypto_hash,
            text=message.text,
            seller_id=seller_id,
            buyer_id=buyer_id,
            sender_id=message.sender_id,
            adapter=adapter,
            store=store,
            orders=_orders(request),
            payments=crypto_store,
            rpc_url=settings.crypto_rpc_url,
            token_contract=settings.crypto_token_contract,
            chain_id=settings.crypto_chain_id,
            network=settings.crypto_network,
            min_confirmations=settings.crypto_min_confirmations,
            transport=request.app.state.transport,
        )
        return
    if message.type == "text" and message.text:
        catalog = request.app.state.catalog
        if catalog is None and settings.supabase_url and settings.supabase_service_role_key:
            catalog = _catalog(request)
        if catalog is not None and catalog.pending_draft(seller_id, buyer_id):
            background.add_task(
                handle_price_reply,
                adapter=adapter,
                catalog=catalog,
                seller_id=seller_id,
                buyer_id=buyer_id,
                sender_id=message.sender_id,
                text=message.text,
            )
        else:
            reply_mode = "auto"
            smart_threshold = 50_000
            business_name = None
            seller = store.get_seller(seller_id) or {}
            business_name = seller.get("business_name") or seller.get("name")
            shops = getattr(request.app.state, "shops", None)
            if shops is not None and seller.get("shop_id"):
                shop = shops.get(str(seller["shop_id"]))
                if shop is not None:
                    reply_mode = getattr(shop, "reply_mode", None) or "auto"
                    smart_threshold = int(getattr(shop, "smart_threshold_ngn", 50_000) or 50_000)
                    business_name = shop.name or business_name
            background.add_task(
                run_turn,
                message=message,
                seller_id=seller_id,
                buyer_id=buyer_id,
                channel_adapter=adapter,
                store=store,
                jev=_jev(request),
                provider=_provider(request),
                catalog_store=_catalog(request),
                order_store=_orders(request),
                payment_store=_payments(request),
                fraud_store=_fraud(request),
                pii_salt=settings.pii_salt,
                business_name=business_name,
                inbox_control=getattr(request.app.state, "inbox_control", None),
                reply_mode=reply_mode,
                smart_threshold_ngn=smart_threshold,
                settings=settings,
            )


async def _reply_official_connect(
    *,
    adapter: ChannelAdapter,
    store: EchoStore,
    seller_id: str,
    buyer_id: str,
    sender_id: str,
    reply: str,
) -> None:
    """Send the fixed official-page connect reply (no LLM / catalog)."""
    message_id = await adapter.send_text(sender_id, reply)
    out_id = message_id or f"out-official-{sender_id}"
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="instagram",
        external_msg_id=out_id,
        text=reply,
        meta={"mode": "official_connect"},
    )


@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background: BackgroundTasks) -> Response:
    raw = await request.body()
    adapter = _whatsapp_adapter(request)
    if not adapter.verify_signature(raw, request.headers):
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "invalid_signature", "message": "bad signature"}},
        )
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "invalid_json", "message": "body is not JSON"}},
        )
    if not isinstance(payload, dict):
        return Response(status_code=200)

    settings = request.app.state.settings
    store = _store(request)
    for message in adapter.parse(payload):
        seller_id = store.ensure_seller(settings.whatsapp_phone_number_id)
        buyer_id = store.ensure_buyer("whatsapp", message.sender_id, message.display_name)
        _dispatch_inbound(
            request=request,
            background=background,
            adapter=adapter,
            store=store,
            message=message,
            seller_id=seller_id,
            buyer_id=buyer_id,
            channel="whatsapp",
        )
    return Response(status_code=200)


@router.post("/webhooks/instagram")
async def instagram_webhook(request: Request, background: BackgroundTasks) -> Response:
    raw = await request.body()
    adapter = _instagram_adapter(request)
    if not adapter.verify_signature(raw, request.headers):
        return JSONResponse(
            status_code=401,
            content={"error": {"code": "invalid_signature", "message": "bad signature"}},
        )
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "invalid_json", "message": "body is not JSON"}},
        )
    if not isinstance(payload, dict):
        return Response(status_code=200)

    settings = request.app.state.settings
    store = _store(request)
    # Prefer recipient IG user id from the webhook so seller_id matches Instagram Login.
    account_id = settings.instagram_account_id or settings.fb_page_id
    for entry in payload.get("entry") or []:
        for event in entry.get("messaging") or []:
            rid = str((event.get("recipient") or {}).get("id") or "")
            if rid:
                account_id = rid
                break
        if account_id and account_id != (settings.instagram_account_id or settings.fb_page_id):
            break
    # Prefer the OAuth session that matches this recipient only.
    # Never fall back to sessions.latest() — that can send as the wrong IG account
    # (e.g. a connected test shop while DMing the official Sell-Safe page).
    sessions = getattr(request.app.state, "instagram_sessions", None)
    if sessions is not None:
        live = sessions.find_by_account_id(str(account_id or ""))
        if live is not None and live.access_token:
            settings.instagram_access_token = live.access_token
            if live.account_id:
                settings.instagram_account_id = live.account_id
    for message in adapter.parse(payload):
        seller_id = store.ensure_seller(account_id, channel="instagram")
        buyer_id = store.ensure_buyer("instagram", message.sender_id, message.display_name)
        _dispatch_inbound(
            request=request,
            background=background,
            adapter=adapter,
            store=store,
            message=message,
            seller_id=seller_id,
            buyer_id=buyer_id,
            channel="instagram",
        )
    return Response(status_code=200)


router.include_router(paystack_router)
router.include_router(flutterwave_router)
router.include_router(alerts_router)

"""Meta verify handshake and WhatsApp echo."""

import hmac
import json

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.agent.listing import handle_price_reply, handle_product_photo
from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.db.catalog_store import CatalogStore, build_catalog_store
from app.db.echo_store import EchoStore, build_store
from app.db.storage import ObjectStorage, build_storage
from app.llm.base import LLMProvider
from app.llm.factory import build_provider

router = APIRouter()


def _store(request: Request) -> EchoStore:
    current = request.app.state.store
    if current is None:
        current = build_store(request.app.state.settings)
        request.app.state.store = current
    return current


def _adapter(request: Request) -> WhatsAppAdapter:
    return WhatsAppAdapter(request.app.state.settings, transport=request.app.state.transport)


def _provider(request: Request) -> LLMProvider:
    current = request.app.state.provider
    if current is None:
        current = build_provider(request.app.state.settings)
        request.app.state.provider = current
    return current


def _catalog(request: Request) -> CatalogStore:
    current = request.app.state.catalog
    if current is None:
        current = build_catalog_store(request.app.state.settings)
        request.app.state.catalog = current
    return current


def _storage(request: Request) -> ObjectStorage:
    current = request.app.state.storage
    if current is None:
        current = build_storage(request.app.state.settings)
        request.app.state.storage = current
    return current


def _tokens_match(token: str | None, expected: str) -> bool:
    if not token or not expected:
        return False
    token_b = token.encode()
    expected_b = expected.encode()
    if len(token_b) != len(expected_b):
        return False
    return hmac.compare_digest(token_b, expected_b)


@router.get("/webhooks/meta")
def meta_verify(request: Request) -> Response:
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


@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background: BackgroundTasks) -> Response:
    raw = await request.body()
    adapter = _adapter(request)
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
        saved = store.save_inbound(
            seller_id=seller_id,
            buyer_id=buyer_id,
            channel="whatsapp",
            external_msg_id=message.external_id,
            message_type=message.type,
            text=message.text,
        )
        if not saved:
            continue
        if message.type == "image":
            background.add_task(
                handle_product_photo,
                adapter=adapter,
                provider=_provider(request),
                storage=_storage(request),
                catalog=_catalog(request),
                seller_id=seller_id,
                buyer_id=buyer_id,
                message=message,
            )
            continue
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
                background.add_task(adapter.send_text, message.sender_id, message.text)
    return Response(status_code=200)

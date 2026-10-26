"""Meta verify handshake and WhatsApp echo."""

import hmac
import json

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.channels.whatsapp.adapter import WhatsAppAdapter
from app.db.echo_store import EchoStore, build_store

router = APIRouter()


def _store(request: Request) -> EchoStore:
    current = request.app.state.store
    if current is None:
        current = build_store(request.app.state.settings)
        request.app.state.store = current
    return current


def _adapter(request: Request) -> WhatsAppAdapter:
    return WhatsAppAdapter(request.app.state.settings, transport=request.app.state.transport)


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
        if saved and message.type == "text" and message.text:
            background.add_task(adapter.send_text, message.sender_id, message.text)
    return Response(status_code=200)

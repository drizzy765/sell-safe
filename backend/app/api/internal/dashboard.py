"""Feature 3 / Dashboard v2 — real Instagram inbox + catalog + reply modes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.api.internal.catalog_onboarding import _drafts, _shop_media
from app.api.internal.onboarding import SESSION_HEADER, _link_seller, _require_session, _shops
from app.channels.instagram.adapter import InstagramAdapter
from app.channels.instagram.conversations import InboxSyncReport, sync_instagram_inbox
from app.db.echo_store import DEFAULT_ECHO_PERSIST_PATH, MemoryEchoStore, build_store
from app.db.inbox_control import InboxControlStore

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_DEMO_CHATS = [
    {
        "id": "demo-1",
        "buyer_id": "demo-1",
        "channel": "instagram",
        "buyer": "adaeze_styles",
        "buyer_external_id": "demo-adaeze",
        "language": "pcm",
        "preview": "Abeg how much be the honey beans? 🛍️",
        "reply": "Na ₦6,000 per paint bucket 😊",
        "at": "today 10:14",
        "created_at": None,
        "demo": True,
        "unread": 1,
        "paused": False,
        "folder": "primary",
    },
]

_DEMO_RECEIPTS = [
    {
        "id": "demo-r1",
        "verdict": "SUSPICIOUS",
        "amount_ngn": 20000,
        "reasons": ["amount mismatch", "no matching bank webhook"],
        "demo": True,
    },
]

_VALID_MODES = {"auto", "approve", "smart"}


class SettingsPatch(BaseModel):
    reply_mode: str | None = None
    smart_threshold_ngn: int | None = None
    demo_mode: bool | None = None
    seller_email: str | None = None
    catalog_skipped: bool | None = None


class TakeoverBody(BaseModel):
    paused: bool = True


class ReplyModeBody(BaseModel):
    reply_mode: str | None = None  # null clears override


class DraftActionBody(BaseModel):
    text: str | None = None


class SendMessageBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


def _inbox_control(request: Request) -> InboxControlStore:
    current = getattr(request.app.state, "inbox_control", None)
    if current is None:
        current = InboxControlStore()
        request.app.state.inbox_control = current
    return current


def _supabase_ready(settings: object) -> bool:
    return bool(
        getattr(settings, "supabase_url", "") and getattr(settings, "supabase_service_role_key", "")
    )


def _echo_store(request: Request):
    current = getattr(request.app.state, "store", None)
    if current is None:
        settings = request.app.state.settings
        if _supabase_ready(settings):
            current = build_store(settings)
        else:
            current = MemoryEchoStore(persist_path=DEFAULT_ECHO_PERSIST_PATH)
        request.app.state.store = current
    return current


def _seller_id(request: Request, ig_account_id: str) -> str:
    store = _echo_store(request)
    if hasattr(store, "ensure_seller"):
        return str(store.ensure_seller(ig_account_id, channel="instagram"))
    return ig_account_id


def _preferred_handle(request: Request, session) -> str:
    """Resolve a human @handle — never fall back to a bare numeric IG id."""
    settings = request.app.state.settings
    candidates = [
        (getattr(session, "username", None) or "").strip().lstrip("@"),
        (getattr(settings, "instagram_username", None) or "").strip().lstrip("@"),
    ]
    account = (getattr(session, "account_id", None) or "").strip()
    env_account = (getattr(settings, "instagram_account_id", None) or "").strip()
    if account and env_account and account == env_account:
        candidates.append(
            (getattr(settings, "instagram_username", None) or "").strip().lstrip("@")
        )
    for handle in candidates:
        if handle and not handle.isdigit():
            return handle
    return "shop"


def _require_shop(request: Request, x_ig_session: str | None):
    from app.db.shop_store import MemoryShopStore, ShopProfile

    _session_id, session = _require_session(request, x_ig_session)
    shops = _shops(request)
    shop = shops.get_by_ig_account(session.account_id)
    handle = _preferred_handle(request, session)
    if shop is None:
        # Survive StatReload: recreate a confirmed shop from the live IG session.
        shop = shops.upsert(
            ShopProfile(
                id=MemoryShopStore.new_id(),
                ig_account_id=session.account_id,
                handle=handle,
                name=handle,
                confirmed=True,
                reply_mode="auto",
            )
        )
    elif (shop.handle or "").strip().isdigit() or not (shop.handle or "").strip():
        shop.handle = handle
        shop.name = shop.name if shop.name and not str(shop.name).isdigit() else handle
        shop = shops.upsert(shop)
    if (getattr(session, "username", None) or "").strip() in ("",) and handle != "shop":
        session.username = handle
    _link_seller(request, shop)
    return session, shop


def _purge_test_stub_threads(store) -> int:
    """Drop synthetic TEST_BUYER_* rows left from local probes."""
    if store is None or not hasattr(store, "messages"):
        return 0
    buyers = getattr(store, "buyer_by_id", {}) or {}
    stub_buyer_ids = {
        bid
        for bid, row in buyers.items()
        if str((row or {}).get("external_id") or "").upper().startswith("TEST_BUYER")
    }
    if not stub_buyer_ids:
        return 0
    removed = 0
    for mid, msg in list((store.messages or {}).items()):
        if msg.get("buyer_id") in stub_buyer_ids:
            store.messages.pop(mid, None)
            removed += 1
    for bid in stub_buyer_ids:
        buyers.pop(bid, None)
    buyer_keys = getattr(store, "buyers", None)
    if isinstance(buyer_keys, dict):
        for key, bid in list(buyer_keys.items()):
            if bid in stub_buyer_ids:
                buyer_keys.pop(key, None)
    if hasattr(store, "_save"):
        store._save()
    return removed


async def _sync_inbox(request: Request, session, shop, seller_id: str) -> InboxSyncReport:
    """Best-effort Graph Conversations sync so past DMs appear in the dashboard."""
    settings = request.app.state.settings
    tokens: list[str] = []
    for raw in (
        getattr(session, "access_token", None),
        getattr(settings, "instagram_access_token", None),
    ):
        token = (raw or "").strip()
        if token and token not in tokens:
            tokens.append(token)
    if not tokens:
        return InboxSyncReport(attempted=True, error="No Instagram access token on the session.")
    store = _echo_store(request)
    control = _inbox_control(request)
    transport = getattr(request.app.state, "transport", None)
    last = InboxSyncReport(attempted=True, error="Conversations sync failed.")
    for token in tokens:
        try:
            report = await sync_instagram_inbox(
                store=store,
                access_token=token,
                seller_ig_id=shop.ig_account_id,
                seller_id=seller_id,
                settings=settings,
                transport=transport,
                inbox_control=control,
            )
        except Exception as exc:  # noqa: BLE001 — never fail the dashboard on Graph sync
            last = InboxSyncReport(
                attempted=True, error=f"Sync failed: {exc.__class__.__name__}"
            )
            continue
        last = report
        if report.ok or (report.conversations or 0) > 0:
            return report
        # code 100 / dead OAuth token → try dashboard-generated env token next
        if report.error and "code 100" not in (report.error or "").lower():
            return report
    return last


def _window_status(last_inbound_at: str | None) -> dict:
    if not last_inbound_at:
        return {"open": False, "hours_left": 0, "warn": "No inbound message yet."}
    try:
        ts = datetime.fromisoformat(last_inbound_at.replace("Z", "+00:00"))
    except ValueError:
        return {"open": False, "hours_left": 0, "warn": "Unknown last message time."}
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    deadline = ts + timedelta(hours=24)
    now = datetime.now(tz=UTC)
    open_window = now <= deadline
    hours_left = max((deadline - now).total_seconds() / 3600.0, 0.0)
    warn = None if open_window else "Outside Meta's 24-hour messaging window — do not send."
    if open_window and hours_left < 4:
        warn = f"Messaging window closes in ~{hours_left:.1f}h."
    return {"open": open_window, "hours_left": round(hours_left, 1), "warn": warn}


@router.post("/inbox/pull")
async def pull_instagram_inbox(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    """Force a Graph Conversations sync for the connected shop (or latest live session)."""
    from app.db.instagram_session_store import InstagramSessionStore
    from app.db.shop_store import MemoryShopStore, ShopProfile

    sessions: InstagramSessionStore = (
        request.app.state.instagram_sessions or InstagramSessionStore()
    )
    session = None
    try:
        _sid, session = _require_session(request, x_ig_session)
    except HTTPException:
        session = sessions.latest()
    if session is None:
        raise HTTPException(status_code=401, detail="Connect Instagram first.")
    shops = _shops(request)
    shop = shops.get_by_ig_account(session.account_id)
    if shop is None:
        handle = (session.username or "").strip().lstrip("@") or session.account_id
        shop = shops.upsert(
            ShopProfile(
                id=MemoryShopStore.new_id(),
                ig_account_id=session.account_id,
                handle=handle,
                name=handle,
                confirmed=True,
                reply_mode="auto",
            )
        )
    seller_id = _seller_id(request, shop.ig_account_id)
    report = await _sync_inbox(request, session, shop, seller_id)
    store = _echo_store(request)
    conversations = (
        store.list_conversations(seller_id) if hasattr(store, "list_conversations") else []
    )
    return {
        "inbox_sync": report.public_dict(),
        "conversations": [
            {
                "buyer": c.get("buyer"),
                "preview": c.get("preview"),
                "buyer_external_id": c.get("buyer_external_id"),
            }
            for c in conversations
        ],
        "shop_handle": shop.handle,
        "account_id_suffix": (shop.ig_account_id or "")[-6:],
    }


@router.get("/summary")
async def dashboard_summary(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    store = _echo_store(request)
    _purge_test_stub_threads(store)
    sync_report = await _sync_inbox(request, session, shop, seller_id)
    control = _inbox_control(request)
    demo_mode = bool(shop.demo_mode or control.get_demo_mode(seller_id))

    products = _drafts(request).list_products(shop.id)
    drafts = _drafts(request).list_drafts(shop.id)
    media = _shop_media(request).list_for_shop(shop.id)

    conversations: list[dict] = []
    if hasattr(store, "list_conversations"):
        conversations = store.list_conversations(seller_id)
        for row in conversations:
            ctrl = control.get_control(seller_id, row["buyer_id"])
            row["unread"] = ctrl.unread
            row["paused"] = ctrl.paused
            row["folder"] = ctrl.folder
            row["reply_mode"] = ctrl.reply_mode or shop.reply_mode
            row["demo"] = False

    inbox = conversations
    receipts: list[dict] = []
    if demo_mode:
        # Demo is Settings-only — never the default for a quiet real inbox.
        inbox = list(conversations) + _DEMO_CHATS
        receipts = list(_DEMO_RECEIPTS)

    pending_drafts = control.list_drafts(seller_id, status="pending")
    unread_total = sum(int(c.get("unread") or 0) for c in conversations)

    today_prefix = datetime.now(tz=UTC).date().isoformat()
    chats_today = sum(
        1 for c in conversations if str(c.get("created_at") or "").startswith(today_prefix)
    )

    return {
        "shop": shop.public_dict(),
        "seller_id": seller_id,
        "stats": {
            "chats_today": chats_today,
            "orders": 0,
            "naira_verified": 0,
            "fakes_caught": 0,
            "avg_reply_seconds": 0,
            "unread_inbox": unread_total,
            "pending_drafts": len(pending_drafts),
            "demo": False,
        },
        "products": [p.public_dict() for p in products],
        "drafts": [d.public_dict() for d in drafts],
        "media": [m.public_dict() for m in media],
        "inbox": inbox,
        "receipts": receipts,
        "reply_drafts": [d.public_dict() for d in pending_drafts],
        "settings": {
            "reply_mode": shop.reply_mode or "auto",
            "smart_threshold_ngn": shop.smart_threshold_ngn,
            "demo_mode": demo_mode,
            "seller_email": shop.seller_email or "",
            "catalog_skipped": shop.catalog_skipped,
        },
        "demo_mode": demo_mode,
        "session_username": session.username,
        "inbox_sync": sync_report.public_dict(),
    }


@router.get("/inbox")
async def list_inbox(
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
    folder: str = "primary",
) -> dict:
    session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    store = _echo_store(request)
    _purge_test_stub_threads(store)
    sync_report = await _sync_inbox(request, session, shop, seller_id)
    control = _inbox_control(request)
    if not hasattr(store, "list_conversations"):
        return {
            "conversations": [],
            "folder": folder,
            "inbox_sync": sync_report.public_dict(),
        }
    rows = store.list_conversations(seller_id)
    out = []
    for row in rows:
        ctrl = control.get_control(seller_id, row["buyer_id"])
        if folder and folder != "all" and ctrl.folder != folder:
            # Until Meta folders exist, everything is primary.
            if folder != "primary":
                continue
        row = dict(row)
        row["unread"] = ctrl.unread
        row["paused"] = ctrl.paused
        row["folder"] = ctrl.folder
        row["reply_mode"] = ctrl.reply_mode or shop.reply_mode
        row["demo"] = False
        out.append(row)
    return {
        "conversations": out,
        "folder": folder,
        "empty": len(out) == 0,
        "inbox_sync": sync_report.public_dict(),
    }


@router.get("/inbox/{buyer_id}")
async def get_thread(
    buyer_id: str,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    store = _echo_store(request)
    _purge_test_stub_threads(store)
    await _sync_inbox(request, session, shop, seller_id)
    control = _inbox_control(request)
    control.clear_unread(seller_id, buyer_id)
    messages = (
        store.list_messages(seller_id, buyer_id, limit=200)
        if hasattr(store, "list_messages")
        else store.recent_messages(seller_id, buyer_id, limit=200)
    )
    # Backfill 24h window from stored inbound rows (sync/webhooks may predate control).
    inbound_times = [
        str(m.get("created_at") or "")
        for m in messages
        if m.get("direction") == "in" and m.get("created_at")
    ]
    if inbound_times:
        latest_in = max(inbound_times)
        control.mark_inbound(seller_id, buyer_id, at=latest_in, count_unread=False)
    buyer = store.get_buyer_by_id(buyer_id) or {}
    ctrl = control.get_control(seller_id, buyer_id)
    drafts = control.list_drafts(seller_id, buyer_id=buyer_id, status="pending")
    window = _window_status(ctrl.last_inbound_at)
    return {
        "buyer_id": buyer_id,
        "buyer": buyer.get("display_name") or buyer.get("external_id") or buyer_id[:8],
        "buyer_external_id": buyer.get("external_id") or "",
        "channel": buyer.get("channel") or "instagram",
        "paused": ctrl.paused,
        "reply_mode": ctrl.reply_mode or shop.reply_mode or "auto",
        "global_reply_mode": shop.reply_mode or "auto",
        "folder": ctrl.folder,
        "window": window,
        "messages": [
            {
                "id": m.get("id") or m.get("external_msg_id"),
                "direction": m.get("direction"),
                "type": m.get("type") or "text",
                "text": m.get("text") or "",
                "media_url": m.get("media_path") or "",
                "meta": m.get("meta"),
                "created_at": m.get("created_at"),
                "language": m.get("language") or "",
            }
            for m in messages
        ],
        "drafts": [d.public_dict() for d in drafts],
    }


@router.post("/inbox/{buyer_id}/takeover")
def takeover_chat(
    buyer_id: str,
    body: TakeoverBody,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    ctrl = _inbox_control(request).set_paused(seller_id, buyer_id, body.paused)
    return {"ok": True, "paused": ctrl.paused}


@router.patch("/inbox/{buyer_id}/reply-mode")
def set_chat_reply_mode(
    buyer_id: str,
    body: ReplyModeBody,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    mode = body.reply_mode
    if mode is not None and mode not in _VALID_MODES:
        raise HTTPException(status_code=422, detail="reply_mode must be auto|approve|smart")
    ctrl = _inbox_control(request).set_reply_mode(seller_id, buyer_id, mode)
    return {"ok": True, "reply_mode": ctrl.reply_mode or shop.reply_mode}


@router.post("/inbox/{buyer_id}/send")
async def send_manual_message(
    buyer_id: str,
    body: SendMessageBody,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    store = _echo_store(request)
    buyer = store.get_buyer_by_id(buyer_id) if store else None
    if not buyer:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    control = _inbox_control(request)
    ctrl = control.get_control(seller_id, buyer_id)
    window = _window_status(ctrl.last_inbound_at)
    if not window["open"]:
        raise HTTPException(status_code=409, detail=window["warn"] or "Outside 24h window.")

    # Prefer the live OAuth session token for sends (settings may be empty).
    settings = request.app.state.settings
    if getattr(session, "access_token", None):
        settings.instagram_access_token = session.access_token
    adapter = InstagramAdapter(settings, transport=request.app.state.transport)
    external_id = str(buyer.get("external_id") or "")
    message_id = await adapter.send_text(external_id, body.text.strip())
    out_id = message_id or f"out-manual-{datetime.now(tz=UTC).timestamp()}"
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel=str(buyer.get("channel") or "instagram"),
        external_msg_id=out_id,
        text=body.text.strip(),
        meta={"manual": True, "mode": "human"},
    )
    return {"ok": True, "message_id": out_id}


@router.post("/drafts/{draft_id}/approve")
async def approve_draft(
    draft_id: str,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    control = _inbox_control(request)
    draft = control.get_draft(draft_id)
    if draft is None or draft.seller_id != seller_id:
        raise HTTPException(status_code=404, detail="Draft not found.")
    if draft.status != "pending":
        raise HTTPException(status_code=409, detail=f"Draft is {draft.status}.")

    ctrl = control.get_control(seller_id, draft.buyer_id)
    window = _window_status(ctrl.last_inbound_at)
    if not window["open"]:
        raise HTTPException(status_code=409, detail=window["warn"] or "Outside 24h window.")

    adapter = InstagramAdapter(request.app.state.settings, transport=request.app.state.transport)
    store = request.app.state.store
    image_url = (draft.product or {}).get("image_url") or ""
    message_id = ""
    if image_url.startswith("http://") or image_url.startswith("https://"):
        try:
            message_id = await adapter.send_image(
                draft.buyer_external_id,
                image_url,
                draft.draft_text,
            )
        except Exception:
            message_id = ""
    if not message_id:
        message_id = await adapter.send_text(draft.buyer_external_id, draft.draft_text)
    out_id = message_id or f"out-approved-{draft.id}"
    meta = {"mode": draft.mode, "approver": shop.handle or "seller", "draft_id": draft.id}
    if draft.product:
        meta["product"] = draft.product
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=draft.buyer_id,
        channel=draft.channel,
        external_msg_id=out_id,
        text=draft.draft_text,
        message_type="product" if draft.product else "text",
        media_path=image_url or None,
        meta=meta,
    )
    control.update_draft(draft_id, status="sent", approver=shop.handle or "seller")
    return {"ok": True, "message_id": out_id}


@router.post("/drafts/{draft_id}/reject")
def reject_draft(
    draft_id: str,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    control = _inbox_control(request)
    draft = control.get_draft(draft_id)
    if draft is None or draft.seller_id != seller_id:
        raise HTTPException(status_code=404, detail="Draft not found.")
    control.update_draft(draft_id, status="rejected", approver=shop.handle or "seller")
    return {"ok": True}


@router.post("/drafts/{draft_id}/edit")
def edit_draft(
    draft_id: str,
    body: DraftActionBody,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    control = _inbox_control(request)
    draft = control.get_draft(draft_id)
    if draft is None or draft.seller_id != seller_id:
        raise HTTPException(status_code=404, detail="Draft not found.")
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=422, detail="text is required")
    updated = control.update_draft(draft_id, draft_text=body.text.strip(), status="pending")
    return {"ok": True, "draft": updated.public_dict() if updated else None}


@router.patch("/settings")
def patch_settings(
    body: SettingsPatch,
    request: Request,
    x_ig_session: str | None = Header(default=None, alias=SESSION_HEADER),
) -> dict:
    _session, shop = _require_shop(request, x_ig_session)
    seller_id = _seller_id(request, shop.ig_account_id)
    if body.reply_mode is not None:
        mode = body.reply_mode.strip().lower()
        if mode not in _VALID_MODES:
            raise HTTPException(status_code=422, detail="reply_mode must be auto|approve|smart")
        shop.reply_mode = mode
    if body.smart_threshold_ngn is not None:
        shop.smart_threshold_ngn = max(int(body.smart_threshold_ngn), 0)
    if body.demo_mode is not None:
        shop.demo_mode = bool(body.demo_mode)
        _inbox_control(request).set_demo_mode(seller_id, shop.demo_mode)
    if body.seller_email is not None:
        shop.seller_email = body.seller_email.strip()
    if body.catalog_skipped is not None:
        shop.catalog_skipped = bool(body.catalog_skipped)
    _shops(request).upsert(shop)
    return {
        "ok": True,
        "settings": {
            "reply_mode": shop.reply_mode,
            "smart_threshold_ngn": shop.smart_threshold_ngn,
            "demo_mode": shop.demo_mode,
            "seller_email": shop.seller_email,
            "catalog_skipped": shop.catalog_skipped,
        },
    }

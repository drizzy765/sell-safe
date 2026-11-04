"""FastAPI application. Webhook routes and /health."""

import hashlib

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.api.internal.auth_accounts import router as auth_accounts_router
from app.api.internal.catalog_onboarding import router as catalog_onboarding_router
from app.api.internal.crypto import router as crypto_router
from app.api.internal.dashboard import router as dashboard_router
from app.api.internal.instagram_oauth import router as instagram_oauth_router
from app.api.internal.jobs import router as internal_jobs_router
from app.api.internal.jobs import sellers_router as internal_sellers_router
from app.api.internal.onboarding import router as onboarding_router
from app.api.internal.orders import router as internal_orders_router
from app.api.internal.waitlist import router as waitlist_router
from app.api.webhooks.router import router as webhooks_router
from app.config import Settings, get_settings
from app.db.catalog_store import CatalogStore, MemoryCatalogStore
from app.db.echo_store import DEFAULT_ECHO_PERSIST_PATH, EchoStore, MemoryEchoStore
from app.db.fraud_store import FraudStore
from app.db.inbox_control import InboxControlStore
from app.db.instagram_session_store import DEFAULT_PERSIST_PATH, InstagramSessionStore
from app.db.onboarding_catalog_store import MemoryOnboardingCatalogStore, OnboardingCatalogStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore
from app.db.shop_media_store import MemoryShopMediaStore
from app.db.shop_store import MemoryShopStore, ShopStore
from app.db.storage import ObjectStorage
from app.db.waitlist_store import WaitlistStore
from app.decisions.base import JevClient
from app.llm.base import LLMProvider
from app.speech.base import SpeechClient


class HealthResponse(BaseModel):
    status: str
    provider: str
    text_model: str = ""
    llm_key: str = "missing"
    llm_key_fingerprint: str = ""
    fallback_model: str = ""


def create_app(
    settings: Settings | None = None,
    store: EchoStore | None = None,
    transport: object | None = None,
    provider: LLMProvider | None = None,
    storage: ObjectStorage | None = None,
    catalog: CatalogStore | None = None,
    jev: JevClient | None = None,
    orders: OrderStore | None = None,
    payments: PaymentStore | None = None,
    speech: SpeechClient | None = None,
    fraud: FraudStore | None = None,
    waitlist: WaitlistStore | None = None,
    instagram_sessions: InstagramSessionStore | None = None,
    seller_accounts: object | None = None,
    shops: ShopStore | None = None,
    onboarding_catalog: OnboardingCatalogStore | None = None,
    shop_media: MemoryShopMediaStore | None = None,
    inbox_control: InboxControlStore | None = None,
) -> FastAPI:
    """Build the app. Tests inject settings, stores, and an HTTP transport."""
    resolved = settings or get_settings()
    app = FastAPI(title="Sell-Safe")
    app.state.settings = resolved
    # Persist local demo messages across StatReload when Supabase is unset.
    app.state.store = store or MemoryEchoStore(persist_path=DEFAULT_ECHO_PERSIST_PATH)
    app.state.transport = transport
    app.state.provider = provider
    app.state.storage = storage
    app.state.catalog = catalog or MemoryCatalogStore()
    app.state.jev = jev
    app.state.orders = orders
    app.state.payments = payments
    app.state.speech = speech
    app.state.fraud = fraud
    app.state.waitlist = waitlist
    if instagram_sessions is not None:
        app.state.instagram_sessions = instagram_sessions
    else:
        supabase_client = None
        if getattr(resolved, "supabase_url", "") and getattr(
            resolved, "supabase_service_role_key", ""
        ):
            try:
                from supabase import create_client

                supabase_client = create_client(
                    getattr(resolved, "supabase_url", ""),
                    getattr(resolved, "supabase_service_role_key", ""),
                )
            except Exception:
                supabase_client = None
        app.state.instagram_sessions = InstagramSessionStore(
            persist_path=DEFAULT_PERSIST_PATH, supabase_client=supabase_client
        )
    app.state.seller_accounts = seller_accounts
    app.state.shops = shops or MemoryShopStore()
    app.state.onboarding_catalog = onboarding_catalog or MemoryOnboardingCatalogStore()
    app.state.shop_media = shop_media or MemoryShopMediaStore()
    app.state.inbox_control = inbox_control or InboxControlStore()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        if resolved.llm_provider == "meta":
            model = resolved.meta_text_model
            raw_key = resolved.meta_api_key
        else:
            model = resolved.groq_text_model
            raw_key = resolved.groq_api_key
        fingerprint = hashlib.sha256(raw_key.encode()).hexdigest()[:8] if raw_key else ""
        return HealthResponse(
            status="ok",
            provider=resolved.llm_provider,
            text_model=model,
            llm_key="set" if raw_key else "missing",
            llm_key_fingerprint=fingerprint,
            fallback_model=resolved.groq_text_model if resolved.llm_provider == "meta" else "",
        )

    @app.get("/privacy", response_class=HTMLResponse)
    def privacy() -> str:
        return _PRIVACY_HTML

    app.include_router(webhooks_router)
    app.include_router(internal_orders_router)
    app.include_router(internal_jobs_router)
    app.include_router(internal_sellers_router)
    app.include_router(waitlist_router)
    app.include_router(crypto_router)
    app.include_router(instagram_oauth_router)
    app.include_router(onboarding_router)
    app.include_router(catalog_onboarding_router)
    app.include_router(dashboard_router)
    app.include_router(auth_accounts_router)
    return app


_PRIVACY_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Sell-Safe privacy</title></head>
<body>
<h1>Sell-Safe privacy</h1>
<p>Sell-Safe is a shop assistant. When someone messages the shop on Instagram,
Sell-Safe receives that message so it can answer questions about products and orders.</p>
<p>The message text, the sender id Instagram provides, and the time of the message
are used to run the shop conversation. Sell-Safe does not sell this information.</p>
<p>To stop, stop messaging the shop. Questions go to the Instagram account sellsafe000.</p>
</body>
</html>
"""

app = create_app()

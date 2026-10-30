"""FastAPI application. Webhook routes and /health."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.api.internal.crypto import router as crypto_router
from app.api.internal.jobs import router as internal_jobs_router
from app.api.internal.jobs import sellers_router as internal_sellers_router
from app.api.internal.orders import router as internal_orders_router
from app.api.internal.waitlist import router as waitlist_router
from app.api.webhooks.router import router as webhooks_router
from app.config import Settings, get_settings
from app.db.catalog_store import CatalogStore
from app.db.echo_store import EchoStore
from app.db.fraud_store import FraudStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore
from app.db.storage import ObjectStorage
from app.db.waitlist_store import WaitlistStore
from app.decisions.base import JevClient
from app.llm.base import LLMProvider
from app.speech.base import SpeechClient


class HealthResponse(BaseModel):
    status: str
    provider: str


class InstagramStatusResponse(BaseModel):
    """Whether Instagram Login is configured. Never includes tokens or ids."""

    ready: bool


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
) -> FastAPI:
    """Build the app. Tests inject settings, stores, and an HTTP transport."""
    resolved = settings or get_settings()
    app = FastAPI(title="Sell-Safe")
    app.state.settings = resolved
    app.state.store = store
    app.state.transport = transport
    app.state.provider = provider
    app.state.storage = storage
    app.state.catalog = catalog
    app.state.jev = jev
    app.state.orders = orders
    app.state.payments = payments
    app.state.speech = speech
    app.state.fraud = fraud
    app.state.waitlist = waitlist

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", provider=resolved.llm_provider)

    @app.get("/api/instagram/status", response_model=InstagramStatusResponse)
    def instagram_status() -> InstagramStatusResponse:
        token = resolved.instagram_access_token.strip()
        account_id = resolved.instagram_account_id.strip()
        return InstagramStatusResponse(ready=bool(token and account_id))

    @app.get("/privacy", response_class=HTMLResponse)
    def privacy() -> str:
        return _PRIVACY_HTML

    app.include_router(webhooks_router)
    app.include_router(internal_orders_router)
    app.include_router(internal_jobs_router)
    app.include_router(internal_sellers_router)
    app.include_router(waitlist_router)
    app.include_router(crypto_router)
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

"""FastAPI application. Webhook routes and /health."""

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.internal.jobs import router as internal_jobs_router
from app.api.internal.jobs import sellers_router as internal_sellers_router
from app.api.internal.orders import router as internal_orders_router
from app.api.webhooks.router import router as webhooks_router
from app.config import Settings, get_settings
from app.db.catalog_store import CatalogStore
from app.db.echo_store import EchoStore
from app.db.fraud_store import FraudStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore
from app.db.storage import ObjectStorage
from app.decisions.base import JevClient
from app.llm.base import LLMProvider
from app.speech.base import SpeechClient


class HealthResponse(BaseModel):
    status: str
    provider: str


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

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", provider=resolved.llm_provider)

    app.include_router(webhooks_router)
    app.include_router(internal_orders_router)
    app.include_router(internal_jobs_router)
    app.include_router(internal_sellers_router)
    return app


app = create_app()

"""FastAPI application. Webhook routes and /health."""

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.webhooks.router import router as webhooks_router
from app.config import Settings, get_settings
from app.db.echo_store import EchoStore


class HealthResponse(BaseModel):
    status: str
    provider: str


def create_app(
    settings: Settings | None = None,
    store: EchoStore | None = None,
    transport: object | None = None,
) -> FastAPI:
    """Build the app. Tests inject settings, an in-memory store, and an HTTP transport."""
    resolved = settings or get_settings()
    app = FastAPI(title="Sell-Safe")
    app.state.settings = resolved
    app.state.store = store
    app.state.transport = transport

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", provider=resolved.llm_provider)

    app.include_router(webhooks_router)
    return app


app = create_app()

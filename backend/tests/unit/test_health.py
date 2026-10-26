from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_reports_provider_from_settings() -> None:
    client = TestClient(create_app(Settings(llm_provider="groq")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "groq"}


def test_health_does_not_invent_a_provider() -> None:
    client = TestClient(create_app(Settings(llm_provider="meta")))

    response = client.get("/health")

    assert response.json()["provider"] == "meta"

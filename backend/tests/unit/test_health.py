from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_reports_provider_from_settings() -> None:
    client = TestClient(create_app(Settings(llm_provider="groq")))

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "groq"


def test_health_does_not_invent_a_provider() -> None:
    client = TestClient(create_app(Settings(llm_provider="meta")))

    response = client.get("/health")

    assert response.json()["provider"] == "meta"


def test_health_reports_effective_llm_model() -> None:
    """Operators must see which model the server will actually call."""
    app = create_app(
        settings=Settings(
            llm_provider="meta", meta_text_model="muse-spark-1.3", meta_api_key="LLM_test"
        )
    )
    body = TestClient(app).get("/health").json()
    assert body["status"] == "ok"
    assert body["provider"] == "meta"
    assert body["text_model"] == "muse-spark-1.3"
    assert body["llm_key"] == "set"

"""Instagram connect status. The response is a boolean and nothing else."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client(*, token: str = "", account_id: str = "") -> TestClient:
    settings = Settings(
        llm_provider="groq",
        instagram_access_token=token,
        instagram_account_id=account_id,
    )
    return TestClient(create_app(settings))


def test_ready_when_token_and_account_are_set() -> None:
    response = _client(token="login-token", account_id="17840000000000000").get(
        "/api/instagram/status"
    )
    assert response.status_code == 200
    assert response.json() == {"ready": True}
    assert "login-token" not in response.text
    assert "17840000000000000" not in response.text


def test_not_ready_when_either_value_is_missing() -> None:
    missing_token = _client(account_id="17840000000000000").get("/api/instagram/status")
    missing_account = _client(token="login-token").get("/api/instagram/status")
    blank = _client(token="   ", account_id="   ").get("/api/instagram/status")
    assert missing_token.json() == {"ready": False}
    assert missing_account.json() == {"ready": False}
    assert blank.json() == {"ready": False}

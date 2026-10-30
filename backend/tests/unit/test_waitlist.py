"""WhatsApp waitlist signup."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.waitlist_store import MemoryWaitlistStore
from app.main import create_app

PHONE = "+2348012345678"


def _client(store: MemoryWaitlistStore | None = None) -> tuple[TestClient, MemoryWaitlistStore]:
    waitlist = store or MemoryWaitlistStore()
    app = create_app(Settings(llm_provider="groq"), waitlist=waitlist)
    return TestClient(app), waitlist


def test_new_number_returns_201_and_stores_one_row() -> None:
    client, store = _client()
    response = client.post("/api/waitlist", json={"phone_number": PHONE})
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "We'll message you on WhatsApp when ready"
    assert body["phone_number"] == PHONE
    assert len(store.rows) == 1
    assert store.rows[0]["phone_number"] == PHONE


def test_duplicate_number_returns_409_and_keeps_one_row() -> None:
    client, store = _client()
    first = client.post("/api/waitlist", json={"phone_number": PHONE})
    second = client.post("/api/waitlist", json={"phone_number": PHONE})
    assert first.status_code == 201
    assert second.status_code == 409
    assert len(store.rows) == 1


def test_invalid_number_is_rejected_and_stores_nothing() -> None:
    client, store = _client()
    response = client.post("/api/waitlist", json={"phone_number": "+123"})
    assert response.status_code == 422
    assert store.rows == []


def test_notify_returns_501() -> None:
    client, store = _client()
    response = client.post("/api/waitlist/notify", json={"phone_number": PHONE})
    assert response.status_code == 501
    assert "Not implemented" in response.json()["message"]
    assert store.rows == []

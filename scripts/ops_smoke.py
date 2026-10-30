"""Smoke alerts + internal jobs with configured secrets.

Usage:
  PYTHONPATH=backend python scripts/ops_smoke.py
  SMOKE_BASE_URL=http://127.0.0.1:8000 PYTHONPATH=backend python scripts/ops_smoke.py
"""

from __future__ import annotations

import os
import sys

import httpx
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.main import create_app

RESULTS: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str) -> None:
    RESULTS.append((name, "PASS" if ok else "FAIL", detail))


def smoke(client: httpx.Client | TestClient, settings: Settings) -> None:
    secret = settings.alert_inbound_secret
    token = settings.internal_api_token
    if not secret:
        record("ALERT_INBOUND_SECRET", False, "unset")
    else:
        r = client.post(
            "/alerts/sms",
            json={
                "from": "+2348011111111",
                "text": "Credit Alert: NGN 15,000 from Ada Ref SS-1001",
            },
            headers={"x-alert-secret": secret},
        )
        # Auth passed if we are past the secret check (seller may be unregistered → 403).
        record(
            "POST /alerts/sms auth",
            r.status_code in {200, 400, 403},
            str(r.status_code),
        )
        bad = client.post(
            "/alerts/sms",
            json={
                "from": "+2348011111111",
                "text": "Credit Alert: NGN 15,000",
            },
            headers={"x-alert-secret": "wrong"},
        )
        record("POST /alerts/sms bad secret", bad.status_code in {401, 403}, str(bad.status_code))

    if not token:
        record("INTERNAL_API_TOKEN", False, "unset")
    else:
        r = client.post("/jobs/reminders", headers={"x-internal-token": token})
        record("POST /jobs/reminders", r.status_code == 200, str(r.status_code))
        r = client.post("/jobs/daily-summary", headers={"x-internal-token": token})
        record("POST /jobs/daily-summary", r.status_code == 200, str(r.status_code))
        bad = client.post("/jobs/reminders", headers={"x-internal-token": "wrong"})
        record(
            "POST /jobs/reminders bad token",
            bad.status_code in {401, 403},
            str(bad.status_code),
        )


def main() -> int:
    settings = get_settings()
    base = (os.environ.get("SMOKE_BASE_URL") or "").rstrip("/")
    if base:
        with httpx.Client(base_url=base, timeout=30.0) as client:
            smoke(client, settings)
    else:
        local = Settings(
            llm_provider=settings.llm_provider or "groq",
            alert_inbound_secret=settings.alert_inbound_secret or "ops-alert-secret",
            internal_api_token=settings.internal_api_token or "ops-internal-token",
            whatsapp_access_token=settings.whatsapp_access_token or "x",
            whatsapp_phone_number_id=settings.whatsapp_phone_number_id or "1",
        )
        app = create_app(
            local,
            store=MemoryEchoStore(),
            orders=MemoryOrderStore(),
            payments=MemoryPaymentStore(),
        )
        with TestClient(app) as client:
            smoke(client, local)

    failed = 0
    for name, status, detail in RESULTS:
        print(f"{status}\t{name}\t{detail}")
        if status != "PASS":
            failed += 1
    print(f"summary\t{len(RESULTS) - failed}/{len(RESULTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

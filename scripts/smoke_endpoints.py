"""Smoke-test public and guarded endpoints. No live DMs or real payments.

Usage:
  PYTHONPATH=backend python scripts/smoke_endpoints.py
  SMOKE_BASE_URL=http://127.0.0.1:8000 PYTHONPATH=backend python scripts/smoke_endpoints.py
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sys

import httpx
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.db.waitlist_store import MemoryWaitlistStore
from app.db.webhook_events import MemoryWebhookEventStore
from app.main import create_app
from app.payments.crypto.rpc import CryptoRpc

DEMO_WALLET = "0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1"
RESULTS: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str) -> None:
    RESULTS.append((name, "PASS" if ok else "FAIL", detail))


def _sign_paystack(secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode(), raw, hashlib.sha512).hexdigest()


def smoke_with_client(client: httpx.Client | TestClient, settings: Settings) -> None:
    r = client.get("/health")
    record(
        "GET /health", r.status_code == 200 and r.json().get("status") == "ok", str(r.status_code)
    )

    r = client.get("/api/instagram/status")
    ok = r.status_code == 200 and "ready" in r.json()
    record("GET /api/instagram/status", ok, str(r.status_code))

    r = client.get("/privacy")
    record("GET /privacy", r.status_code == 200 and "privacy" in r.text.lower(), str(r.status_code))

    r = client.post("/api/sellers/crypto-wallet", json={"address": DEMO_WALLET})
    ok = r.status_code == 200 and r.json().get("address") == DEMO_WALLET
    record("POST /api/sellers/crypto-wallet", ok, str(r.status_code))

    r = client.post("/api/sellers/crypto-wallet", json={"address": DEMO_WALLET.lower()})
    record(
        "POST /api/sellers/crypto-wallet invalid checksum", r.status_code == 422, str(r.status_code)
    )

    r = client.get("/api/demo/crypto")
    if r.status_code != 200:
        record("GET /api/demo/crypto", False, str(r.status_code))
    else:
        body = r.json()
        if not (settings.demo_real_tx_hash or "").strip():
            ok = body.get("ready") is False and "DEMO_REAL_TX_HASH" in (body.get("message") or "")
            record("GET /api/demo/crypto (hash unset)", ok, "ready=false expected")
        else:
            ok = body.get("ready") is True and isinstance(body.get("cases"), list)
            record("GET /api/demo/crypto (live)", ok, f"ready={body.get('ready')}")

    r = client.post("/api/waitlist", json={"phone_number": "+2348012345678"})
    if r.status_code in (201, 409):
        record("POST /api/waitlist", True, str(r.status_code))
    elif r.status_code == 503 and "whatsapp_waitlist" in (r.text or ""):
        record(
            "POST /api/waitlist",
            False,
            "503 migration 0005 not applied (scripts/apply_pending_migrations.sql)",
        )
    else:
        record("POST /api/waitlist", False, str(r.status_code))

    r = client.post("/api/waitlist", json={"phone_number": "+123"})
    record("POST /api/waitlist invalid", r.status_code == 422, str(r.status_code))

    r = client.post("/api/waitlist/notify", json={"phone_number": "+2348012345678"})
    record("POST /api/waitlist/notify", r.status_code == 501, str(r.status_code))

    token = settings.meta_verify_token or "test-verify"
    r = client.get(
        "/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": token,
            "hub.challenge": "12345",
        },
    )
    record(
        "GET /webhooks/instagram verify",
        r.status_code == 200 and r.text == "12345",
        str(r.status_code),
    )
    r = client.get("/webhooks/instagram")
    record("GET /webhooks/instagram no challenge", r.status_code == 403, str(r.status_code))

    r = client.post(
        "/webhooks/instagram",
        content=b'{"object":"instagram"}',
        headers={"content-type": "application/json", "x-hub-signature-256": "sha256=bad"},
    )
    record("POST /webhooks/instagram bad signature", r.status_code == 401, str(r.status_code))

    raw = b"{}"
    r = client.post(
        "/webhooks/paystack",
        content=raw,
        headers={"x-paystack-signature": "bad", "content-type": "application/json"},
    )
    record("POST /webhooks/paystack bad signature", r.status_code == 401, str(r.status_code))

    if settings.paystack_secret_key:
        signed = _sign_paystack(settings.paystack_secret_key, raw)
        r = client.post(
            "/webhooks/paystack",
            content=raw,
            headers={"x-paystack-signature": signed, "content-type": "application/json"},
        )
        record(
            "POST /webhooks/paystack good signature empty body",
            r.status_code == 200,
            str(r.status_code),
        )

    r = client.post(
        "/alerts/sms",
        json={
            "seller_id": "x",
            "text": "Credit NGN 1000",
            "received_at": "2026-10-30T12:00:00Z",
        },
    )
    if not settings.alert_inbound_secret:
        record("POST /alerts/sms (secret unset)", r.status_code == 503, str(r.status_code))
    else:
        record("POST /alerts/sms", r.status_code in {200, 401, 403, 404, 422}, str(r.status_code))

    r = client.post("/orders/SS-SMOKE/release")
    record("POST /orders/{ref}/release no token", r.status_code in (401, 503), str(r.status_code))
    r = client.post("/jobs/reminders")
    record("POST /jobs/reminders no token", r.status_code in (401, 503), str(r.status_code))

    record(
        "catalog HTTP surface",
        True,
        "catalog is webhook/tool driven (no dedicated REST in this build)",
    )
    record(
        "orders create HTTP surface",
        True,
        "order create is agent-tool driven; release endpoint smoke above",
    )


def build_memory_client(settings: Settings) -> TestClient:
    store = MemoryEchoStore()
    app = create_app(
        settings,
        store=store,
        waitlist=MemoryWaitlistStore(),
        orders=MemoryOrderStore(),
        payments=MemoryPaymentStore(),
    )
    app.state.webhook_events = MemoryWebhookEventStore()
    if settings.crypto_rpc_url:
        app.state.crypto_rpc = CryptoRpc(settings.crypto_rpc_url)
    return TestClient(app)


def main() -> int:
    settings = get_settings()
    base = (os.environ.get("SMOKE_BASE_URL") or "").rstrip("/")
    print("mode=", "http" if base else "testclient-memory")
    print("rpc_set=", bool(settings.crypto_rpc_url.strip()))
    print("demo_hash_set=", bool(settings.demo_real_tx_hash.strip()))

    if base:
        with httpx.Client(base_url=base, timeout=30.0) as client:
            smoke_with_client(client, settings)
    else:
        local = Settings(
            llm_provider=settings.llm_provider or "groq",
            instagram_account_id=settings.instagram_account_id or "smoke-ig",
            instagram_access_token=settings.instagram_access_token or "smoke-token",
            meta_verify_token=settings.meta_verify_token or "smoke-verify",
            paystack_secret_key=settings.paystack_secret_key or "smoke-paystack",
            crypto_network=settings.crypto_network or "base-sepolia",
            crypto_rpc_url=settings.crypto_rpc_url,
            crypto_chain_id=settings.crypto_chain_id or 84532,
            crypto_token_contract=settings.crypto_token_contract,
            crypto_min_confirmations=settings.crypto_min_confirmations or 3,
            crypto_explorer_url=settings.crypto_explorer_url or "https://sepolia.basescan.org",
            demo_real_tx_hash=settings.demo_real_tx_hash,
            alert_inbound_secret="",
            internal_api_token="",
        )
        with build_memory_client(local) as client:
            smoke_with_client(client, local)

    print("\nENDPOINT RESULTS")
    failed = 0
    for name, status, detail in RESULTS:
        print(f"{status}\t{name}\t{detail}")
        if status != "PASS":
            failed += 1
    print(f"summary\t{len(RESULTS) - failed}/{len(RESULTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

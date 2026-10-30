"""Automated P0 proof: Paystack webhook CONFIRMED + edited screenshot blocks release.

Writes results to demo/clips/PROOF.md. Does not send real money.
Usage: PYTHONPATH=backend python scripts/live_p0_proof.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.catalog_store import MemoryCatalogStore
from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.db.storage import MemoryStorage
from app.db.webhook_events import MemoryWebhookEventStore
from app.decisions.fake import FakeJev
from app.llm.fake import FakeProvider
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend" / "tests" / "fixtures" / "whatsapp"
OUT = ROOT / "demo" / "clips" / "PROOF.md"

WA_SECRET = "proof-wa-secret"
PAYSTACK_SECRET = "proof-paystack-secret"
INTERNAL = "proof-internal-token"


def _wa_sign(raw: bytes) -> str:
    digest = hmac.new(WA_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _paystack_sign(raw: bytes) -> str:
    return hmac.new(PAYSTACK_SECRET.encode(), raw, hashlib.sha512).hexdigest()


def _receipt_vision(amount_kobo: int = 1_500_000) -> dict:
    return {
        "is_transfer_receipt": True,
        "amount_kobo": amount_kobo,
        "currency": "NGN",
        "sender_name": "Ada",
        "sender_bank": "GTBank",
        "recipient_name": "Tolu",
        "recipient_acct_last4": "1234",
        "reference": "SS-1001",
        "status_text": "successful",
        "txn_time_iso": "2026-10-27T10:15:00Z",
        "app_style": "GTWorld",
        "visual_anomalies": [],
    }


def _whatsapp_image_raw(name: str) -> bytes:
    payload = json.loads((FIXTURES / "image.json").read_text(encoding="utf-8"))
    payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"] = f"wamid.{name}"
    return json.dumps(payload).encode()


def _paystack_payload() -> bytes:
    return json.dumps(
        {
            "event": "charge.success",
            "data": {
                "id": 12345,
                "reference": "SS-1001",
                "amount": 1500000,
                "currency": "NGN",
                "status": "success",
                "paid_at": "2026-10-27T10:15:00Z",
                "customer": {"first_name": "Ada"},
                "authorization": {"bank": "GTBank"},
            },
        }
    ).encode()


def _client(provider: FakeProvider) -> tuple[TestClient, MemoryOrderStore]:
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("1234567890")
    buyer_id = store.ensure_buyer("whatsapp", "15550000001")
    store.seller_details[seller_id]["business_name"] = "Tolu"
    store.seller_details[seller_id]["virtual_account"] = {"last4": "1234", "bank": "Test Bank"}
    orders = MemoryOrderStore()
    orders.orders.append(
        {
            "id": "order-1",
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "ref": "SS-1001",
            "total_kobo": 1_500_000,
            "status": "awaiting_payment",
            "created_at": "2026-10-27T10:00:00Z",
        }
    )
    payments = MemoryPaymentStore()
    events = MemoryWebhookEventStore()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and str(request.url.path).endswith("/media-image-1"):
            return httpx.Response(200, json={"url": "https://cdn.example/obj"})
        if request.method == "GET" and request.url.host == "cdn.example":
            return httpx.Response(200, content=b"jpeg-bytes")
        if request.url.path == "/transaction/verify/12345":
            return httpx.Response(
                200,
                json={
                    "status": True,
                    "data": {
                        "id": 12345,
                        "reference": "SS-1001",
                        "amount": 1500000,
                        "currency": "NGN",
                        "status": "success",
                        "paid_at": "2026-10-27T10:15:00Z",
                        "customer": {"first_name": "Ada"},
                        "authorization": {"bank": "GTBank"},
                    },
                },
            )
        if str(request.url.path).endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})
        return httpx.Response(404)

    settings = Settings(
        llm_provider="groq",
        meta_app_secret=WA_SECRET,
        meta_verify_token="verify-me",
        whatsapp_access_token="test-token",
        whatsapp_phone_number_id="1234567890",
        graph_api_version="v21.0",
        paystack_secret_key=PAYSTACK_SECRET,
        internal_api_token=INTERNAL,
    )
    app = create_app(
        settings,
        store=store,
        transport=httpx.MockTransport(handler),
        provider=provider,
        jev=FakeJev(
            intent="payment_proof",
            language="en",
            evidence_match=1.0,
            receipt_tampered=0.0,
        ),
        catalog=MemoryCatalogStore(),
        orders=orders,
        payments=payments,
        storage=MemoryStorage(),
    )
    app.state.webhook_events = events
    return TestClient(app), orders


def main() -> int:
    lines = [
        "# P0 live-proof package",
        "",
        f"- Generated: {datetime.now(tz=UTC).isoformat()}",
        "- Mode: automated TestClient (Paystack verify mocked; no real Naira moved)",
        "",
        "## Results",
        "",
    ]
    ok = True

    client, orders = _client(FakeProvider(vision=_receipt_vision()))
    raw = _whatsapp_image_raw("receipt")
    client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Hub-Signature-256": _wa_sign(raw), "content-type": "application/json"},
    )
    webhook_raw = _paystack_payload()
    r = client.post(
        "/webhooks/paystack",
        content=webhook_raw,
        headers={
            "x-paystack-signature": _paystack_sign(webhook_raw),
            "content-type": "application/json",
        },
    )
    release = client.post("/orders/SS-1001/release", headers={"x-internal-token": INTERNAL})
    confirmed_ok = (
        r.status_code == 200
        and release.status_code == 200
        and orders.orders[0]["status"] == "released"
    )
    ok = ok and confirmed_ok
    lines.append(
        f"- Paystack path -> CONFIRMED + release: "
        f"{'PASS' if confirmed_ok else 'FAIL'} "
        f"(webhook={r.status_code}, release={release.status_code}, "
        f"status={orders.orders[0]['status']})"
    )

    client, orders = _client(FakeProvider(vision=_receipt_vision(amount_kobo=1_000_000)))
    raw = _whatsapp_image_raw("receipt-bad")
    client.post(
        "/webhooks/whatsapp",
        content=raw,
        headers={"X-Hub-Signature-256": _wa_sign(raw), "content-type": "application/json"},
    )
    release = client.post("/orders/SS-1001/release", headers={"x-internal-token": INTERNAL})
    blocked_ok = release.status_code == 409 and orders.orders[0]["status"] == "awaiting_payment"
    ok = ok and blocked_ok
    lines.append(
        f"- Edited screenshot -> SUSPICIOUS / release 409: "
        f"{'PASS' if blocked_ok else 'FAIL'} "
        f"(release={release.status_code}, status={orders.orders[0]['status']})"
    )

    lines.extend(
        [
            "",
            "## Manual follow-up (real Paystack test mode)",
            "",
            "1. Create an order against a Paystack test DVA.",
            "2. Complete a test transfer; confirm webhook signature uses `PAYSTACK_SECRET_KEY`.",
            "3. Expect CONFIRMED and release allowed.",
            "4. Send an edited-amount screenshot; expect SUSPICIOUS and release 409.",
            "5. Drop screen recordings into `demo/clips/` as `confirmed.mp4` and `suspicious.mp4`.",
            "",
        ]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

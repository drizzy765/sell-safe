"""Tests for the bank-alert parser and webhook routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.echo_store import MemoryEchoStore
from app.db.orders import MemoryOrderStore
from app.db.payments import MemoryPaymentStore
from app.decisions.fake import FakeJev
from app.main import create_app
from app.payments.alerts.parse import alert_to_extraction_dict, parse_alert
from app.verification.extract import ReceiptExtraction
from app.verification.matchers import find_matching_evidence

GTB_CREDIT = """\
GTBank
Acct: ****1234 has been credited with NGN5,000.00
Desc: Transfer from John Doe
Ref: GTB-ABC123
Date: 27-Oct-2026 14:30 WAT
Bal: NGN25,000.00
"""

ACCESS_CREDIT = """\
Access Bank
Credit Alert
Amt: N10,000.00
Acc: ****5678
Desc: Transfer from Jane Smith
Ref: ACC-XYZ789
Time: 27 Oct 2026 15:45
Bal: N50,000.00
"""

OPAY_CREDIT = """\
OPay
You have received NGN 1,500.00 into your OPay account ****9012.
From: Mike Brown.
Ref: OPY-999888.
Time: 2026-10-27 16:00.
Balance: NGN 15,000.00
"""

GTB_DEBIT = """\
GTBank
Acct: ****1234 has been debited with NGN2,500.00
Desc: Transfer to Akin
Ref: GTB-DEBIT-1
Date: 27-Oct-2026 14:35 WAT
Bal: NGN22,500.00
"""


class TestParseAlert:
    def test_gtb_credit(self) -> None:
        alert = parse_alert(GTB_CREDIT)
        assert alert is not None
        assert alert.bank == "gtb"
        assert alert.type == "credit"
        assert alert.amount_kobo == 500_000
        assert alert.balance_kobo == 2_500_000
        assert alert.reference == "GTB-ABC123"
        assert alert.sender_hint == "John Doe"
        assert alert.txn_time_iso is not None

    def test_access_credit(self) -> None:
        alert = parse_alert(ACCESS_CREDIT)
        assert alert is not None
        assert alert.bank == "access"
        assert alert.amount_kobo == 1_000_000
        assert alert.reference == "ACC-XYZ789"
        assert alert.sender_hint == "Jane Smith"

    def test_opay_credit(self) -> None:
        alert = parse_alert(OPAY_CREDIT)
        assert alert is not None
        assert alert.bank == "opay"
        assert alert.amount_kobo == 150_000
        assert alert.reference == "OPY-999888"
        assert alert.sender_hint == "Mike Brown"

    def test_debit_is_parsed_but_flagged(self) -> None:
        alert = parse_alert(GTB_DEBIT)
        assert alert is not None
        assert alert.type == "debit"
        assert alert.amount_kobo == 250_000

    def test_unparseable_returns_none(self) -> None:
        assert parse_alert("Hello, no money here") is None


class TestAlertExtraction:
    def test_alert_maps_to_receipt_extraction(self) -> None:
        alert = parse_alert(GTB_CREDIT)
        assert alert is not None
        extracted = ReceiptExtraction.model_validate(alert_to_extraction_dict(alert))
        assert extracted.is_transfer_receipt is True
        assert extracted.amount_kobo == 500_000
        assert extracted.sender_name == "John Doe"
        assert extracted.reference == "GTB-ABC123"

    def test_alert_evidence_matches_screenshot(self) -> None:
        alert = parse_alert(GTB_CREDIT)
        assert alert is not None
        evidence_row = {
            "id": "ev1",
            "type": "bank_alert",
            "trust_level": 2,
            "extracted": alert_to_extraction_dict(alert),
        }
        screenshot = ReceiptExtraction(
            is_transfer_receipt=True,
            amount_kobo=500_000,
            currency="NGN",
            sender_name="John Doe",
            sender_bank="gtb",
            recipient_name="Shop",
            recipient_acct_last4="1234",
            reference="GTB-ABC123",
            status_text="successful",
            txn_time_iso=alert.txn_time_iso,
            app_style="GTWorld",
            visual_anomalies=[],
        )
        match = find_matching_evidence(screenshot, [evidence_row])
        assert match is not None
        assert match.trust_level == 2


@pytest.fixture
def alert_app():
    store = MemoryEchoStore()
    seller_id = store.ensure_seller("whatsapp-phone-id")
    store.register_channel(seller_id, "sms", "+234801")

    orders = MemoryOrderStore()
    payments = MemoryPaymentStore()
    settings = type(
        "Settings",
        (),
        {
            "alert_inbound_secret": "alert-secret",
            "pii_salt": "salt",
            "internal_api_token": "internal-secret",
            "llm_provider": "fake",
        },
    )()

    app = create_app(
        settings=settings,
        store=store,
        orders=orders,
        payments=payments,
    )
    app.state.jev = FakeJev(
        intent="payment_proof",
        language="en",
        evidence_match=1.0,
        receipt_tampered=0.0,
    )
    return app, store, orders, payments


class TestAlertRoutes:
    def test_sms_credit_creates_bank_alert_evidence(self, alert_app) -> None:
        app, store, orders, payments = alert_app
        seller_id = store.sellers["whatsapp-phone-id"]
        order = orders.create_order(
            seller_id=seller_id,
            buyer_id="buyer-1",
            items=[{"product_id": "p1", "qty": 1, "unit_price_kobo": 500_000}],
            total_kobo=500_000,
        )

        client = TestClient(app)
        response = client.post(
            "/alerts/sms",
            json={"from": "+234801", "text": GTB_CREDIT},
            headers={"x-alert-secret": "alert-secret"},
        )
        assert response.status_code == 200
        assert response.json()["matched_orders"] == 1

        evidence = payments.get_evidence_for_order(order["id"])
        assert len(evidence) == 1
        assert evidence[0]["type"] == "bank_alert"
        assert evidence[0]["trust_level"] == 2
        assert evidence[0]["extracted"]["amount_kobo"] == 500_000

    def test_missing_secret_returns_401(self, alert_app) -> None:
        app, *_ = alert_app
        client = TestClient(app)
        response = client.post("/alerts/sms", json={"from": "+234801", "text": GTB_CREDIT})
        assert response.status_code == 401

    def test_bad_secret_returns_403(self, alert_app) -> None:
        app, *_ = alert_app
        client = TestClient(app)
        response = client.post(
            "/alerts/sms",
            json={"from": "+234801", "text": GTB_CREDIT},
            headers={"x-alert-secret": "wrong"},
        )
        assert response.status_code == 403

    def test_buyer_number_not_registered_returns_403(self, alert_app) -> None:
        app, *_ = alert_app
        client = TestClient(app)
        response = client.post(
            "/alerts/sms",
            json={"from": "+234999", "text": GTB_CREDIT},
            headers={"x-alert-secret": "alert-secret"},
        )
        assert response.status_code == 403

    def test_debit_alert_not_stored(self, alert_app) -> None:
        app, store, orders, payments = alert_app
        seller_id = store.sellers["whatsapp-phone-id"]
        order = orders.create_order(
            seller_id=seller_id,
            buyer_id="buyer-1",
            items=[],
            total_kobo=250_000,
        )

        client = TestClient(app)
        response = client.post(
            "/alerts/sms",
            json={"from": "+234801", "text": GTB_DEBIT},
            headers={"x-alert-secret": "alert-secret"},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is False
        evidence = payments.get_evidence_for_order(order["id"])
        assert len(evidence) == 0

    def test_email_route_same_secret(self, alert_app) -> None:
        app, store, orders, payments = alert_app
        seller_id = store.sellers["whatsapp-phone-id"]
        store.register_channel(seller_id, "email", "seller@example.com")
        order = orders.create_order(
            seller_id=seller_id,
            buyer_id="buyer-1",
            items=[],
            total_kobo=500_000,
        )

        client = TestClient(app)
        response = client.post(
            "/alerts/email",
            json={"from": "seller@example.com", "text": GTB_CREDIT},
            headers={"x-alert-secret": "alert-secret"},
        )
        assert response.status_code == 200
        assert response.json()["matched_orders"] == 1
        evidence = payments.get_evidence_for_order(order["id"])
        assert evidence[0]["type"] == "bank_alert"

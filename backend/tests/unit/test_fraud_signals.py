"""Cross-seller fraud memory and R6 wiring."""

from datetime import UTC, datetime

from app.db.fraud_store import MemoryFraudStore
from app.db.payments import MemoryPaymentStore
from app.verification.extract import ReceiptExtraction
from app.verification.fraud import (
    dispute_fake_for_evidence,
    hash_pii,
    lookup_confirmed_signals,
    report_fake_from_evidence,
)
from app.verification.rules import apply_rules


def _extraction(**overrides: object) -> ReceiptExtraction:
    data = {
        "is_transfer_receipt": True,
        "amount_kobo": 1_500_000,
        "currency": "NGN",
        "sender_name": "Scammer Sam",
        "sender_bank": "GTBank",
        "sender_acct_last4": "9999",
        "recipient_name": "Tolu",
        "recipient_acct_last4": "1234",
        "reference": "ref-scam",
        "status_text": "successful",
        "txn_time_iso": "2026-10-27T10:15:00Z",
        "app_style": "GTWorld",
        "visual_anomalies": [],
        "image_sha256": "deadbeef",
        "image_phash": "abcd1234",
    }
    data.update(overrides)
    return ReceiptExtraction(**data)  # type: ignore[arg-type]


def test_confirmed_signal_from_seller_a_flags_seller_b() -> None:
    salt = "test-salt"
    fraud = MemoryFraudStore()
    payments = MemoryPaymentStore()

    # Seller A reports fake evidence.
    payment_a = payments.get_or_create_payment(
        order_id="order-a", method="bank_transfer", expected_kobo=1_500_000
    )
    evidence = payments.insert_evidence(
        payment_id=payment_a["id"],
        evidence_type="screenshot",
        source_id="src-a",
        extracted={
            "sender_name": "Scammer Sam",
            "sender_bank": "GTBank",
            "sender_acct_last4": "9999",
            "image_sha256": "deadbeef",
        },
        trust_level=1,
        image_sha256="deadbeef",
    )
    inserted = report_fake_from_evidence(
        fraud,
        seller_id="seller-a",
        evidence_rows=[evidence],
        pii_salt=salt,
    )
    assert inserted
    assert all(s["confirmed"] for s in inserted)
    # Raw account / name never stored (ignore UUID ids — they can contain "9999").
    for signal in fraud.signals:
        payload = {k: v for k, v in signal.items() if k != "id"}
        blob = repr(payload)
        assert "9999" not in blob
        assert "Scammer Sam" not in blob
        assert len(str(signal["value_hash"])) == 64


    # Seller B verifies matching extraction → R6.
    extraction = _extraction()
    signals = lookup_confirmed_signals(fraud, extraction, pii_salt=salt)
    assert signals
    result = apply_rules(
        {"id": "order-b", "total_kobo": 1_500_000, "created_at": "2026-10-27T10:00:00Z"},
        extraction,
        [],
        signals,
        seller_account_last4="1234",
        seller_name="Tolu",
        pii_salt=salt,
    )
    assert "R6_blocklist" in result.rule_hits


def test_unconfirmed_signal_does_not_add_r6() -> None:
    salt = "test-salt"
    fraud = MemoryFraudStore()
    fraud.insert_signal(
        kind="name",
        value_hash=hash_pii("Scammer Sam", salt),
        reported_by_seller_id="seller-a",
        confirmed=False,
    )
    extraction = _extraction()
    signals = lookup_confirmed_signals(fraud, extraction, pii_salt=salt)
    assert signals == []
    result = apply_rules(
        {"id": "order-b", "total_kobo": 1_500_000, "created_at": "2026-10-27T10:00:00Z"},
        extraction,
        [],
        [
            {
                "kind": "name",
                "value_hash": hash_pii("Scammer Sam", salt),
                "confirmed": False,
            }
        ],
        pii_salt=salt,
    )
    assert "R6_blocklist" not in result.rule_hits


def test_dispute_clears_confirmed() -> None:
    fraud = MemoryFraudStore()
    payments = MemoryPaymentStore()
    payment = payments.get_or_create_payment(
        order_id="order-a", method="bank_transfer", expected_kobo=100
    )
    evidence = payments.insert_evidence(
        payment_id=payment["id"],
        evidence_type="screenshot",
        source_id="src-a",
        extracted={"sender_name": "Scammer Sam"},
        trust_level=1,
    )
    report_fake_from_evidence(fraud, seller_id="seller-a", evidence_rows=[evidence], pii_salt="s")
    assert all(s["confirmed"] for s in fraud.signals)
    count = dispute_fake_for_evidence(fraud, evidence_rows=[evidence])
    assert count >= 1
    assert all(not s["confirmed"] for s in fraud.signals)


def test_phone_signal_matches_buyer_phone_hash() -> None:
    salt = "s"
    phone_hash = hash_pii("+2348011111111", salt)
    fraud = MemoryFraudStore()
    fraud.insert_signal(
        kind="phone",
        value_hash=phone_hash,
        reported_by_seller_id="seller-a",
        confirmed=True,
    )
    extraction = _extraction()
    signals = lookup_confirmed_signals(
        fraud, extraction, pii_salt=salt, buyer_phone_hash=phone_hash
    )
    assert len(signals) == 1
    result = apply_rules(
        {"id": "o", "total_kobo": 1_500_000, "created_at": datetime.now(tz=UTC).isoformat()},
        extraction,
        [],
        signals,
        pii_salt=salt,
        buyer_phone_hash=phone_hash,
    )
    assert "R6_blocklist" in result.rule_hits

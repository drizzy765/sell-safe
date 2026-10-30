from datetime import UTC, datetime, timedelta

import pytest

from app.verification.extract import ReceiptExtraction
from app.verification.rules import RulesResult, apply_rules


@pytest.fixture
def order() -> dict:
    return {
        "id": "order-1",
        "total_kobo": 1_500_000,
        "created_at": "2026-10-27T10:00:00Z",
    }


@pytest.fixture
def extraction() -> ReceiptExtraction:
    return ReceiptExtraction(
        is_transfer_receipt=True,
        amount_kobo=1_500_000,
        currency="NGN",
        sender_name="Ada O",
        sender_bank="GTBank",
        recipient_name="Tolu",
        recipient_acct_last4="1234",
        reference="ref-abc",
        status_text="successful",
        txn_time_iso="2026-10-27T10:15:00Z",
        app_style="GTWorld",
        visual_anomalies=[],
        image_phash="abcd1234",
    )


def _apply(
    order: dict,
    extraction: ReceiptExtraction,
    **overrides: object,
) -> RulesResult:
    kwargs = {
        "seller_account_last4": "1234",
        "seller_name": "Tolu",
        "evidence_rows": [],
        "fraud_signals": [],
    }
    kwargs.update(overrides)
    return apply_rules(order, extraction, **kwargs)


def test_clean_receipt_has_zero_risk(order: dict, extraction: ReceiptExtraction) -> None:
    result = _apply(order, extraction)
    assert result.rule_risk == 0.0
    assert result.rule_hits == []
    assert result.not_confirmable is False


def test_r1_amount_mismatch(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.amount_kobo = 1_000_000
    result = _apply(order, extraction)
    assert "R1_amount_mismatch" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.4)


def test_r2_recipient_last4_mismatch(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.recipient_acct_last4 = "9999"
    result = _apply(order, extraction)
    assert "R2_recipient_mismatch" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.5)


def test_r2_recipient_name_mismatch(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.recipient_name = "Other Seller"
    result = _apply(order, extraction)
    assert "R2_recipient_mismatch" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.5)


def test_r3_time_in_future(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.txn_time_iso = (datetime.now(tz=UTC) + timedelta(hours=2)).isoformat()
    result = _apply(order, extraction)
    assert "R3_time_window" in result.rule_hits


def test_r3_time_before_order(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.txn_time_iso = "2026-10-26T08:00:00Z"
    result = _apply(order, extraction)
    assert "R3_time_window" in result.rule_hits


def test_r4_duplicate_reference(order: dict, extraction: ReceiptExtraction) -> None:
    evidence = [{"extracted": {"reference": "ref-abc"}}]
    result = _apply(order, extraction, evidence_rows=evidence)
    assert "R4_duplicate_ref" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.6)


def test_r5_duplicate_image(order: dict, extraction: ReceiptExtraction) -> None:
    evidence = [{"image_phash": extraction.image_phash}]
    result = _apply(order, extraction, evidence_rows=evidence)
    assert "R5_duplicate_image" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.6)


def test_r6_blocklist_confirmed_only(order: dict, extraction: ReceiptExtraction) -> None:
    from app.verification.rules import _hash_value

    signal = {
        "kind": "name",
        "value_hash": _hash_value("Ada O"),
        "confirmed": True,
    }
    result = _apply(order, extraction, fraud_signals=[signal])
    assert "R6_blocklist" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.7)


def test_r6_unconfirmed_does_not_fire(order: dict, extraction: ReceiptExtraction) -> None:
    from app.verification.rules import _hash_value

    signal = {
        "kind": "name",
        "value_hash": _hash_value("Ada O"),
        "confirmed": False,
    }
    result = _apply(order, extraction, fraud_signals=[signal])
    assert "R6_blocklist" not in result.rule_hits


def test_r7_visual_anomaly_capped(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.visual_anomalies = ["a", "b", "c"]
    result = _apply(order, extraction)
    assert "R7_visual_anomaly" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.4)


def test_r8_status_text_pending(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.status_text = "pending"
    result = _apply(order, extraction)
    assert "R8_status_text" in result.rule_hits
    assert result.not_confirmable is True


def test_r9_metadata_editor(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.metadata_editor = "Adobe Photoshop"
    result = _apply(order, extraction)
    assert "R9_metadata_editor" in result.rule_hits
    assert result.rule_risk == pytest.approx(0.2)


def test_rule_risk_capped_at_one(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.amount_kobo = 1_000_000  # +0.4
    extraction.recipient_acct_last4 = "9999"  # +0.5
    extraction.visual_anomalies = ["a", "b", "c"]  # +0.4
    result = _apply(order, extraction)
    assert result.rule_risk == 1.0

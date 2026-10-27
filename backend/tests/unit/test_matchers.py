import pytest

from app.verification.extract import ReceiptExtraction
from app.verification.matchers import find_matching_evidence


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
    )


def _evidence_row(
    *,
    trust_level: int = 4,
    amount_kobo: int = 1_500_000,
    reference: str | None = "ref-abc",
    sender_name: str | None = "Ada O",
    txn_time_iso: str = "2026-10-27T10:10:00Z",
) -> dict:
    return {
        "id": "ev-1",
        "trust_level": trust_level,
        "extracted": {
            "amount_kobo": amount_kobo,
            "reference": reference,
            "sender_name": sender_name,
            "txn_time_iso": txn_time_iso,
        },
    }


def test_exact_reference_match(extraction: ReceiptExtraction) -> None:
    rows = [_evidence_row()]
    match = find_matching_evidence(extraction, rows)
    assert match is not None
    assert match.trust_level == 4


def test_fuzzy_sender_name_match(extraction: ReceiptExtraction) -> None:
    rows = [_evidence_row(reference=None, sender_name="Ada Ol")]
    match = find_matching_evidence(extraction, rows)
    assert match is not None


def test_amount_mismatch_returns_none(extraction: ReceiptExtraction) -> None:
    rows = [_evidence_row(amount_kobo=1_000_000)]
    match = find_matching_evidence(extraction, rows)
    assert match is None


def test_time_outside_window_returns_none(extraction: ReceiptExtraction) -> None:
    rows = [_evidence_row(txn_time_iso="2026-10-27T08:00:00Z")]
    match = find_matching_evidence(extraction, rows)
    assert match is None


def test_low_trust_level_skipped(extraction: ReceiptExtraction) -> None:
    rows = [_evidence_row(trust_level=1)]
    match = find_matching_evidence(extraction, rows)
    assert match is None


def test_returns_highest_trust_match(extraction: ReceiptExtraction) -> None:
    rows = [
        _evidence_row(trust_level=2),
        _evidence_row(trust_level=4),
        _evidence_row(trust_level=3),
    ]
    match = find_matching_evidence(extraction, rows)
    assert match is not None
    assert match.trust_level == 4

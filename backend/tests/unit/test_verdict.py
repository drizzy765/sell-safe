from datetime import UTC, datetime

import pytest

from app.decisions.base import RouteScores
from app.verification.extract import ReceiptExtraction
from app.verification.matchers import EvidenceMatch
from app.verification.rules import RulesResult, apply_rules
from app.verification.verdict import decide_verdict


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
        txn_time_iso=datetime.now(tz=UTC).isoformat(),
        app_style="GTWorld",
        visual_anomalies=[],
    )


def _jev(
    evidence_match: float = 0.0,
    receipt_tampered: float = 0.0,
) -> RouteScores:
    return RouteScores(
        intent="payment_proof",
        language="en",
        evidence_match=evidence_match,
        receipt_tampered=receipt_tampered,
    )


def _rules(extraction: ReceiptExtraction, order: dict, **overrides: object) -> RulesResult:
    kwargs = {
        "evidence_rows": [],
        "fraud_signals": [],
        "seller_account_last4": "1234",
        "seller_name": "Tolu",
    }
    kwargs.update(overrides)
    return apply_rules(order, extraction, **kwargs)


def _evidence(trust_level: int = 4, amount_kobo: int = 1_500_000) -> EvidenceMatch:
    return EvidenceMatch(
        {
            "id": f"ev-{trust_level}",
            "trust_level": trust_level,
            "extracted": {"amount_kobo": amount_kobo},
        }
    )


def test_level_4_match_confirmed_with_release(order: dict, extraction: ReceiptExtraction) -> None:
    rules = _rules(extraction, order)
    verdict = decide_verdict(order, extraction, rules, _evidence(trust_level=4), _jev(1.0, 0.0))
    assert verdict.verdict == "CONFIRMED"
    assert verdict.release_allowed is True
    assert verdict.confidence >= 0.9


def test_level_3_match_confirmed_with_release(order: dict, extraction: ReceiptExtraction) -> None:
    verdict = decide_verdict(
        order, extraction, _rules(extraction, order), _evidence(trust_level=3), _jev(1.0, 0.0)
    )
    assert verdict.verdict == "CONFIRMED"
    assert verdict.release_allowed is True


def test_level_2_match_confirmed_no_release(order: dict, extraction: ReceiptExtraction) -> None:
    verdict = decide_verdict(order, extraction, _rules(extraction, order), _evidence(trust_level=2))
    assert verdict.verdict == "CONFIRMED"
    assert verdict.release_allowed is False


def test_clean_screenshot_no_evidence_not_found(order: dict, extraction: ReceiptExtraction) -> None:
    verdict = decide_verdict(order, extraction, _rules(extraction, order), None)
    assert verdict.verdict == "NOT_FOUND"
    assert verdict.release_allowed is False


def test_screenshot_with_medium_risk_unverified(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.visual_anomalies = ["font_mismatch", "alignment_issue"]
    rules = _rules(extraction, order)
    verdict = decide_verdict(order, extraction, rules, None)
    assert verdict.verdict == "UNVERIFIED"
    assert verdict.release_allowed is False


def test_r4_blocks_release(order: dict, extraction: ReceiptExtraction) -> None:
    evidence = [{"extracted": {"reference": "ref-abc"}}]
    rules = _rules(extraction, order, evidence_rows=evidence)
    verdict = decide_verdict(order, extraction, rules, _evidence(), _jev(1.0, 0.0))
    assert verdict.verdict == "SUSPICIOUS"
    assert verdict.release_allowed is False


def test_high_rule_risk_suspicious(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.amount_kobo = 1_000_000
    extraction.recipient_acct_last4 = "9999"
    rules = _rules(extraction, order)
    verdict = decide_verdict(order, extraction, rules, None)
    assert verdict.verdict == "SUSPICIOUS"
    assert verdict.release_allowed is False


def test_screenshot_alone_never_confirmed(order: dict, extraction: ReceiptExtraction) -> None:
    for trust_level in [1, None]:
        matched = _evidence(trust_level=1) if trust_level else None
        verdict = decide_verdict(order, extraction, _rules(extraction, order), matched)
        assert verdict.release_allowed is False


def test_pending_status_unverified(order: dict, extraction: ReceiptExtraction) -> None:
    extraction.status_text = "pending"
    rules = _rules(extraction, order)
    verdict = decide_verdict(order, extraction, rules, _evidence())
    assert verdict.verdict == "CONFIRMED"
    assert verdict.release_allowed is False
    assert "level_2_evidence_requires_seller_confirmation" in verdict.reasons


def test_no_extraction_not_found(order: dict) -> None:
    rules = RulesResult(rule_hits=[], rule_risk=0.0, not_confirmable=False)
    verdict = decide_verdict(order, None, rules, None)
    assert verdict.verdict == "NOT_FOUND"
    assert verdict.release_allowed is False


def test_mid_confidence_holds_release(order: dict, extraction: ReceiptExtraction) -> None:
    verdict = decide_verdict(
        order, extraction, _rules(extraction, order), _evidence(trust_level=4), _jev(0.75, 0.1)
    )
    assert verdict.verdict == "CONFIRMED"
    assert verdict.release_allowed is False
    assert 0.60 <= verdict.confidence < 0.90


def test_low_confidence_unverified(order: dict, extraction: ReceiptExtraction) -> None:
    verdict = decide_verdict(
        order, extraction, _rules(extraction, order), _evidence(trust_level=4), _jev(0.5, 0.1)
    )
    assert verdict.verdict == "UNVERIFIED"
    assert verdict.release_allowed is False


def test_missing_jev_scores_do_not_auto_confirm(order: dict, extraction: ReceiptExtraction) -> None:
    verdict = decide_verdict(order, extraction, _rules(extraction, order), _evidence(trust_level=4))
    assert verdict.release_allowed is False
    assert verdict.verdict in ("UNVERIFIED", "SUSPICIOUS", "CONFIRMED")


def test_partial_payment_suspicious(order: dict, extraction: ReceiptExtraction) -> None:
    # Evidence shows only 1M arrived for a 1.5M order.
    extraction.amount_kobo = 1_000_000
    verdict = decide_verdict(
        order,
        extraction,
        _rules(extraction, order),
        _evidence(trust_level=4, amount_kobo=1_000_000),
        _jev(1.0, 0.0),
    )
    assert verdict.verdict == "SUSPICIOUS"
    assert verdict.release_allowed is False
    assert "partial_payment" in verdict.reasons

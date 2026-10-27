"""Unit tests for Jev confidence scoring inside the verdict engine."""

from app.decisions.base import RouteScores
from app.verification.rules import RulesResult
from app.verification.verdict import decide_verdict


def _make_evidence(trust_level: int = 4, amount_kobo: int = 1_500_000):
    return {
        "id": f"ev-{trust_level}",
        "trust_level": trust_level,
        "extracted": {"amount_kobo": amount_kobo},
    }


def _jev(evidence_match: float, receipt_tampered: float) -> RouteScores:
    return RouteScores(
        intent="payment_proof",
        language="en",
        evidence_match=evidence_match,
        receipt_tampered=receipt_tampered,
    )


def test_confidence_formula_with_clean_evidence() -> None:
    order = {"id": "order-1", "total_kobo": 1_500_000, "created_at": "2026-10-27T10:00:00Z"}
    rules = RulesResult(rule_hits=[], rule_risk=0.0, not_confirmable=False)
    verdict = decide_verdict(
        order,
        None,
        rules,
        type("Match", (), {"row": _make_evidence(4), "trust_level": 4})(),
        _jev(0.95, 0.05),
    )
    # confidence = 0.95 * (1 - max(0.05, 0.0)) = 0.9025
    assert round(verdict.confidence, 4) == 0.9025
    assert verdict.verdict == "CONFIRMED"
    assert verdict.release_allowed is True


def test_confidence_capped_by_rule_risk() -> None:
    order = {"id": "order-1", "total_kobo": 1_500_000, "created_at": "2026-10-27T10:00:00Z"}
    rules = RulesResult(rule_hits=["R3_time_window"], rule_risk=0.3, not_confirmable=False)
    verdict = decide_verdict(
        order,
        None,
        rules,
        type("Match", (), {"row": _make_evidence(4), "trust_level": 4})(),
        _jev(1.0, 0.0),
    )
    # confidence = 1.0 * (1 - max(0.0, 0.3)) = 0.70
    assert round(verdict.confidence, 4) == 0.7
    assert verdict.verdict == "CONFIRMED"
    assert verdict.release_allowed is False


def test_high_tamper_blocks_release() -> None:
    order = {"id": "order-1", "total_kobo": 1_500_000, "created_at": "2026-10-27T10:00:00Z"}
    rules = RulesResult(rule_hits=[], rule_risk=0.0, not_confirmable=False)
    verdict = decide_verdict(
        order,
        None,
        rules,
        type("Match", (), {"row": _make_evidence(4), "trust_level": 4})(),
        _jev(1.0, 0.7),
    )
    assert verdict.verdict == "SUSPICIOUS"
    assert verdict.release_allowed is False

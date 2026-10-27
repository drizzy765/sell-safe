"""Deterministic verdict engine. The only place verdicts are decided.

See docs/payment_verification.md for the verdict table.
"""

from typing import Any

from pydantic import BaseModel

from app.decisions.base import RouteScores
from app.verification.extract import ReceiptExtraction
from app.verification.matchers import EvidenceMatch
from app.verification.rules import RulesResult


class Verdict(BaseModel):
    verdict: str  # CONFIRMED, NOT_FOUND, SUSPICIOUS, UNVERIFIED
    confidence: float
    release_allowed: bool
    reasons: list[str]
    matched_evidence_id: str | None = None
    jev_scores: dict[str, float] | None = None


def _jev_dict(jev_scores: RouteScores | None) -> dict[str, float] | None:
    if jev_scores is None:
        return None
    return {
        "receipt_tampered": jev_scores.receipt_tampered,
        "evidence_match": jev_scores.evidence_match,
    }


def _compute_confidence(
    rules_result: RulesResult,
    jev_scores: RouteScores | None,
) -> float:
    """Compute confidence from Jev scores and rule risk.

    Missing Jev scores default to 0, which prevents an automatic CONFIRMED.
    """
    p_match = jev_scores.evidence_match if jev_scores else 0.0
    p_tamper = jev_scores.receipt_tampered if jev_scores else 0.0
    return p_match * (1 - max(p_tamper, rules_result.rule_risk))


def decide_verdict(
    order: dict[str, Any],
    extraction: ReceiptExtraction | None,
    rules_result: RulesResult,
    matched_evidence: EvidenceMatch | None,
    jev_scores: RouteScores | None = None,
) -> Verdict:
    """Return a verdict from extraction, rules, matched evidence, and Jev scores.

    Screenshot-only evidence (trust level 1) can never set release_allowed=true.
    """
    hard_hits = {"R4_duplicate_ref", "R5_duplicate_image", "R6_blocklist"}
    has_hard_hit = bool(hard_hits.intersection(set(rules_result.rule_hits)))
    jev_dict = _jev_dict(jev_scores)

    # Highest priority: hard rule hits or high rule risk.
    if has_hard_hit or rules_result.rule_risk >= 0.6:
        reasons = rules_result.rule_hits.copy()
        if (
            matched_evidence
            and extraction
            and extraction.amount_kobo
            != int((matched_evidence.row.get("extracted") or {}).get("amount_kobo") or 0)
        ):
            reasons.append("partial_payment")
        return Verdict(
            verdict="SUSPICIOUS",
            confidence=0.2,
            release_allowed=False,
            reasons=reasons,
            matched_evidence_id=matched_evidence.row.get("id") if matched_evidence else None,
            jev_scores=jev_dict,
        )

    # Partial payment on matched evidence.
    if matched_evidence:
        evidence_amount = int((matched_evidence.row.get("extracted") or {}).get("amount_kobo") or 0)
        if evidence_amount != int(order.get("total_kobo") or 0):
            return Verdict(
                verdict="SUSPICIOUS",
                confidence=0.2,
                release_allowed=False,
                reasons=rules_result.rule_hits.copy() + ["partial_payment"],
                matched_evidence_id=matched_evidence.row.get("id"),
                jev_scores=jev_dict,
            )

    # Matched evidence path.
    if matched_evidence is not None:
        trust_level = matched_evidence.trust_level
        row_id = matched_evidence.row.get("id")
        if trust_level >= 3 and not rules_result.not_confirmable:
            confidence = _compute_confidence(rules_result, jev_scores)
            if confidence >= 0.90:
                return Verdict(
                    verdict="CONFIRMED",
                    confidence=confidence,
                    release_allowed=True,
                    reasons=rules_result.rule_hits.copy() or ["level_3_or_4_evidence_match"],
                    matched_evidence_id=row_id,
                    jev_scores=jev_dict,
                )
            if confidence >= 0.60:
                return Verdict(
                    verdict="CONFIRMED",
                    confidence=confidence,
                    release_allowed=False,
                    reasons=rules_result.rule_hits.copy() or ["mid_confidence_seller_confirmation"],
                    matched_evidence_id=row_id,
                    jev_scores=jev_dict,
                )
            # Low confidence despite matching evidence.
            if rules_result.rule_risk >= 0.3 or (jev_scores and jev_scores.receipt_tampered >= 0.4):
                return Verdict(
                    verdict="SUSPICIOUS",
                    confidence=confidence,
                    release_allowed=False,
                    reasons=rules_result.rule_hits.copy() or ["low_confidence_match"],
                    matched_evidence_id=row_id,
                    jev_scores=jev_dict,
                )
            return Verdict(
                verdict="UNVERIFIED",
                confidence=confidence,
                release_allowed=False,
                reasons=rules_result.rule_hits.copy() or ["low_confidence_match"],
                matched_evidence_id=row_id,
                jev_scores=jev_dict,
            )
        # Trust level 2, or pending/processing status, always needs seller confirmation.
        return Verdict(
            verdict="CONFIRMED",
            confidence=0.8,
            release_allowed=False,
            reasons=["level_2_evidence_requires_seller_confirmation"],
            matched_evidence_id=row_id,
            jev_scores=jev_dict,
        )

    # No matched evidence.
    if extraction is None or not extraction.is_transfer_receipt:
        return Verdict(
            verdict="NOT_FOUND",
            confidence=0.5,
            release_allowed=False,
            reasons=["no_receipt_extracted"],
            jev_scores=jev_dict,
        )

    # Screenshot-only with tamper signal.
    if jev_scores and jev_scores.receipt_tampered >= 0.6:
        return Verdict(
            verdict="SUSPICIOUS",
            confidence=0.2,
            release_allowed=False,
            reasons=rules_result.rule_hits.copy() or ["receipt_looks_tampered"],
            jev_scores=jev_dict,
        )

    if rules_result.rule_risk < 0.3 and not rules_result.not_confirmable:
        return Verdict(
            verdict="NOT_FOUND",
            confidence=0.5,
            release_allowed=False,
            reasons=rules_result.rule_hits.copy() or ["clean_screenshot_no_matching_evidence"],
            jev_scores=jev_dict,
        )

    if rules_result.not_confirmable:
        return Verdict(
            verdict="UNVERIFIED",
            confidence=0.4,
            release_allowed=False,
            reasons=rules_result.rule_hits.copy() or ["pending_status"],
            jev_scores=jev_dict,
        )

    return Verdict(
        verdict="UNVERIFIED",
        confidence=0.4,
        release_allowed=False,
        reasons=rules_result.rule_hits.copy() or ["screenshot_with_risk"],
        jev_scores=jev_dict,
    )

"""Deterministic verdict engine. The only place verdicts are decided.

See docs/payment_verification.md for the verdict table.
"""

from typing import Any

from pydantic import BaseModel

from app.verification.extract import ReceiptExtraction
from app.verification.matchers import EvidenceMatch
from app.verification.rules import RulesResult


class Verdict(BaseModel):
    verdict: str  # CONFIRMED, NOT_FOUND, SUSPICIOUS, UNVERIFIED
    confidence: float
    release_allowed: bool
    reasons: list[str]
    matched_evidence_id: str | None = None


def decide_verdict(
    order: dict[str, Any],
    extraction: ReceiptExtraction | None,
    rules_result: RulesResult,
    matched_evidence: EvidenceMatch | None,
) -> Verdict:
    """Return a verdict from extraction, rules, and matched evidence.

    Screenshot-only evidence (trust level 1) can never set release_allowed=true.
    """
    hard_hits = {"R4_duplicate_ref", "R5_duplicate_image", "R6_blocklist"}
    has_hard_hit = bool(hard_hits.intersection(set(rules_result.rule_hits)))

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
        )

    # Matched evidence path.
    if matched_evidence is not None:
        trust_level = matched_evidence.trust_level
        row_id = matched_evidence.row.get("id")
        if trust_level >= 3 and not rules_result.not_confirmable:
            return Verdict(
                verdict="CONFIRMED",
                confidence=0.95 if trust_level == 4 else 0.94,
                release_allowed=True,
                reasons=rules_result.rule_hits.copy() or ["level_3_or_4_evidence_match"],
                matched_evidence_id=row_id,
            )
        if trust_level == 2 or rules_result.not_confirmable:
            return Verdict(
                verdict="CONFIRMED",
                confidence=0.8,
                release_allowed=False,
                reasons=["level_2_evidence_requires_seller_confirmation"],
                matched_evidence_id=row_id,
            )

    # No matched evidence.
    if extraction is None or not extraction.is_transfer_receipt:
        return Verdict(
            verdict="NOT_FOUND",
            confidence=0.5,
            release_allowed=False,
            reasons=["no_receipt_extracted"],
        )

    if rules_result.rule_risk < 0.3 and not rules_result.not_confirmable:
        return Verdict(
            verdict="NOT_FOUND",
            confidence=0.5,
            release_allowed=False,
            reasons=rules_result.rule_hits.copy() or ["clean_screenshot_no_matching_evidence"],
        )

    if rules_result.not_confirmable:
        return Verdict(
            verdict="UNVERIFIED",
            confidence=0.4,
            release_allowed=False,
            reasons=rules_result.rule_hits.copy() or ["pending_status"],
        )

    return Verdict(
        verdict="UNVERIFIED",
        confidence=0.4,
        release_allowed=False,
        reasons=rules_result.rule_hits.copy() or ["screenshot_with_risk"],
    )

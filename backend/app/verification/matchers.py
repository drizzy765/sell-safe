"""Match a receipt extraction to stored payment evidence."""

from datetime import datetime, timedelta
from typing import Any

from thefuzz import fuzz

from app.verification.extract import ReceiptExtraction


class EvidenceMatch:
    """A matched evidence row with its trust level."""

    def __init__(self, row: dict[str, Any]) -> None:
        self.row = row
        self.trust_level: int = int(row.get("trust_level") or 0)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        clean = value.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def _evidence_amount(row: dict[str, Any]) -> int | None:
    extracted = row.get("extracted") or {}
    amount = extracted.get("amount_kobo")
    if amount is None:
        return None
    try:
        return int(amount)
    except (TypeError, ValueError):
        return None


def _evidence_reference(row: dict[str, Any]) -> str | None:
    extracted = row.get("extracted") or {}
    ref = extracted.get("reference")
    return str(ref) if ref else None


def _evidence_sender(row: dict[str, Any]) -> str | None:
    extracted = row.get("extracted") or {}
    sender = extracted.get("sender_name")
    return str(sender) if sender else None


def _evidence_time(row: dict[str, Any]) -> datetime | None:
    extracted = row.get("extracted") or {}
    return _parse_iso(extracted.get("txn_time_iso"))


def _reference_matches(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return a.strip().lower() == b.strip().lower()


def _sender_matches(a: str | None, b: str | None, threshold: int = 85) -> bool:
    if not a or not b:
        return False
    return fuzz.ratio(a, b) >= threshold


def _time_matches(
    claim_time: datetime | None,
    evidence_time: datetime | None,
    window: timedelta = timedelta(minutes=30),
) -> bool:
    if claim_time is None or evidence_time is None:
        # If no times available, treat as matching (other fields must match).
        return True
    return abs(claim_time - evidence_time) <= window


def find_matching_evidence(
    extraction: ReceiptExtraction,
    evidence_rows: list[dict[str, Any]],
    min_trust_level: int = 2,
) -> EvidenceMatch | None:
    """Return the highest-trust evidence row that matches the extraction."""
    claim_time = _parse_iso(extraction.txn_time_iso)
    candidates: list[tuple[int, dict[str, Any]]] = []

    for row in evidence_rows:
        trust_level = int(row.get("trust_level") or 0)
        if trust_level < min_trust_level:
            continue

        amount = _evidence_amount(row)
        if amount is None or extraction.amount_kobo is None or amount != extraction.amount_kobo:
            continue

        ref_match = _reference_matches(extraction.reference, _evidence_reference(row))
        sender_match = _sender_matches(extraction.sender_name, _evidence_sender(row))
        if not (ref_match or sender_match):
            continue

        if not _time_matches(claim_time, _evidence_time(row)):
            continue

        candidates.append((trust_level, row))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return EvidenceMatch(candidates[0][1])

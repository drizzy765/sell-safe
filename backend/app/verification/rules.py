"""Deterministic rule checks R1-R9 for payment verification.

See docs/payment_verification.md for the rule table.
"""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel

from app.verification.extract import ReceiptExtraction


class RulesResult(BaseModel):
    rule_hits: list[str]
    rule_risk: float
    not_confirmable: bool


_WEIGHTS: dict[str, float] = {
    "R1_amount_mismatch": 0.4,
    "R2_recipient_mismatch": 0.5,
    "R3_time_window": 0.3,
    "R4_duplicate_ref": 0.6,
    "R5_duplicate_image": 0.6,
    "R6_blocklist": 0.7,
    "R7_visual_anomaly": 0.2,
    "R9_metadata_editor": 0.2,
}

_R7_MAX = 0.4


def _phash_distance(a: str, b: str) -> int:
    """Hamming distance between two hexadecimal average-hash strings."""
    if not a or not b or len(a) != len(b):
        return 999
    try:
        bits_a = bin(int(a, 16))[2:].zfill(len(a) * 4)
        bits_b = bin(int(b, 16))[2:].zfill(len(b) * 4)
    except ValueError:
        return 999
    return sum(x != y for x, y in zip(bits_a, bits_b))


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        clean = value.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def _hash_value(value: str, salt: str = "") -> str:
    return hashlib.sha256(f"{salt}{value}".encode()).hexdigest()


def apply_rules(
    order: dict[str, Any],
    extraction: ReceiptExtraction,
    evidence_rows: list[dict[str, Any]],
    fraud_signals: list[dict[str, Any]],
    *,
    seller_account_last4: str | None = None,
    seller_name: str | None = None,
    pii_salt: str = "",
    buyer_phone_hash: str | None = None,
    exclude_evidence_ids: set[str] | None = None,
    current_payment_id: str | None = None,
) -> RulesResult:
    """Apply rules R1-R9 and return aggregated risk."""
    excluded = exclude_evidence_ids or set()
    hits: list[str] = []
    risk = 0.0
    not_confirmable = False

    # R1 amount mismatch
    order_total = int(order.get("total_kobo") or 0)
    if extraction.amount_kobo is not None and extraction.amount_kobo != order_total:
        hits.append("R1_amount_mismatch")
        risk += _WEIGHTS["R1_amount_mismatch"]

    # R2 recipient mismatch
    if seller_account_last4 and extraction.recipient_acct_last4:
        if extraction.recipient_acct_last4 != seller_account_last4:
            hits.append("R2_recipient_mismatch")
            risk += _WEIGHTS["R2_recipient_mismatch"]
    if seller_name and extraction.recipient_name:
        if extraction.recipient_name.lower() != seller_name.lower():
            hits.append("R2_recipient_mismatch")
            risk += _WEIGHTS["R2_recipient_mismatch"]

    # R3 time window
    txn_time = _parse_iso(extraction.txn_time_iso)
    order_created = _parse_iso(order.get("created_at"))
    now = datetime.now(tz=UTC)
    if txn_time is not None:
        if txn_time > now + timedelta(minutes=5):
            hits.append("R3_time_window")
            risk += _WEIGHTS["R3_time_window"]
        elif txn_time < (order_created or now) - timedelta(hours=24):
            hits.append("R3_time_window")
            risk += _WEIGHTS["R3_time_window"]

    # R4 duplicate reference
    if extraction.reference:
        for row in evidence_rows:
            if row.get("id") in excluded:
                continue
            if current_payment_id and row.get("payment_id") == current_payment_id:
                continue
            extracted = row.get("extracted") or {}
            if extracted.get("reference") == extraction.reference:
                hits.append("R4_duplicate_ref")
                risk += _WEIGHTS["R4_duplicate_ref"]
                break

    # R5 duplicate image
    if extraction.image_phash:
        for row in evidence_rows:
            if row.get("id") in excluded:
                continue
            if current_payment_id and row.get("payment_id") == current_payment_id:
                continue
            if _phash_distance(extraction.image_phash, row.get("image_phash") or "") <= 5:
                hits.append("R5_duplicate_image")
                risk += _WEIGHTS["R5_duplicate_image"]
                break

    # R6 blocklist — match confirmed signals against hashed extraction fields.
    if fraud_signals:
        sender_name_hashed = (
            _hash_value(extraction.sender_name, pii_salt) if extraction.sender_name else None
        )
        sender_acct = getattr(extraction, "sender_acct_last4", None)
        account_raw = sender_acct if isinstance(sender_acct, str) and sender_acct else None
        if not account_raw:
            account_raw = extraction.sender_bank
        account_hashed = _hash_value(account_raw, pii_salt) if account_raw else None
        image_sha256_hashed = (
            _hash_value(extraction.image_sha256, pii_salt) if extraction.image_sha256 else None
        )
        for signal in fraud_signals:
            if not signal.get("confirmed"):
                continue
            kind = signal.get("kind")
            value = signal.get("value_hash") or ""
            if kind == "name" and sender_name_hashed and value == sender_name_hashed:
                hits.append("R6_blocklist")
                risk += _WEIGHTS["R6_blocklist"]
                break
            if kind == "account_number" and account_hashed and value == account_hashed:
                hits.append("R6_blocklist")
                risk += _WEIGHTS["R6_blocklist"]
                break
            if kind == "phone" and buyer_phone_hash and value == buyer_phone_hash:
                hits.append("R6_blocklist")
                risk += _WEIGHTS["R6_blocklist"]
                break
            if kind == "image_hash" and image_sha256_hashed and value == image_sha256_hashed:
                hits.append("R6_blocklist")
                risk += _WEIGHTS["R6_blocklist"]
                break

    # R7 visual anomalies
    if extraction.visual_anomalies:
        count = len(extraction.visual_anomalies)
        anomaly_risk = min(count * _WEIGHTS["R7_visual_anomaly"], _R7_MAX)
        if anomaly_risk:
            hits.append("R7_visual_anomaly")
            risk += anomaly_risk

    # R8 pending/processing status
    if extraction.status_text and extraction.status_text.lower() in ("pending", "processing"):
        hits.append("R8_status_text")
        not_confirmable = True

    # R9 metadata editing software
    if extraction.metadata_editor:
        hits.append("R9_metadata_editor")
        risk += _WEIGHTS["R9_metadata_editor"]

    return RulesResult(
        rule_hits=hits,
        rule_risk=min(1.0, risk),
        not_confirmable=not_confirmable,
    )

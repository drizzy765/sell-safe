"""Fraud memory helpers: hash PII and build signal candidates from evidence."""

from __future__ import annotations

import hashlib
from typing import Any

from app.db.fraud_store import FraudStore
from app.verification.extract import ReceiptExtraction


def hash_pii(value: str, salt: str = "") -> str:
    """SHA-256 of salt+value. Never log the raw value."""
    return hashlib.sha256(f"{salt}{value}".encode()).hexdigest()


def candidate_hashes_from_extraction(
    extraction: ReceiptExtraction,
    *,
    pii_salt: str = "",
    buyer_phone_hash: str | None = None,
) -> dict[str, str]:
    """Map fraud kinds to salted hashes derived from a receipt extraction."""
    out: dict[str, str] = {}
    if extraction.sender_name:
        out["name"] = hash_pii(extraction.sender_name, pii_salt)
    # Prefer sender account last4 when present; else bank name as account key.
    acct = getattr(extraction, "sender_acct_last4", None) or None
    if isinstance(acct, str) and acct:
        out["account_number"] = hash_pii(acct, pii_salt)
    elif extraction.sender_bank:
        out["account_number"] = hash_pii(extraction.sender_bank, pii_salt)
    if buyer_phone_hash:
        out["phone"] = buyer_phone_hash
    if extraction.image_sha256:
        out["image_hash"] = hash_pii(extraction.image_sha256, pii_salt)
    return out


def lookup_confirmed_signals(
    fraud_store: FraudStore,
    extraction: ReceiptExtraction,
    *,
    pii_salt: str = "",
    buyer_phone_hash: str | None = None,
) -> list[dict[str, Any]]:
    candidates = candidate_hashes_from_extraction(
        extraction,
        pii_salt=pii_salt,
        buyer_phone_hash=buyer_phone_hash,
    )
    if not candidates:
        return []
    found = fraud_store.find_confirmed_by_hashes(list(candidates.values()))
    # Keep only signals whose kind matches the candidate map.
    matched: list[dict[str, Any]] = []
    for signal in found:
        kind = signal.get("kind")
        value = signal.get("value_hash")
        if kind in candidates and candidates[kind] == value:
            matched.append(signal)
    return matched


def report_fake_from_evidence(
    fraud_store: FraudStore,
    *,
    seller_id: str,
    evidence_rows: list[dict[str, Any]],
    pii_salt: str = "",
    buyer_phone_hash: str | None = None,
) -> list[dict[str, Any]]:
    """Insert confirmed fraud_signals from order evidence. Returns inserted rows."""
    inserted: list[dict[str, Any]] = []
    for row in evidence_rows:
        extracted = row.get("extracted") or {}
        evidence_id = str(row.get("id") or "") or None
        pairs: list[tuple[str, str]] = []
        if extracted.get("sender_name"):
            pairs.append(("name", hash_pii(str(extracted["sender_name"]), pii_salt)))
        acct = extracted.get("sender_acct_last4") or extracted.get("sender_bank")
        if acct:
            pairs.append(("account_number", hash_pii(str(acct), pii_salt)))
        if buyer_phone_hash:
            pairs.append(("phone", buyer_phone_hash))
        image_sha = row.get("image_sha256") or extracted.get("image_sha256")
        if image_sha:
            pairs.append(("image_hash", hash_pii(str(image_sha), pii_salt)))
        for kind, value_hash in pairs:
            inserted.append(
                fraud_store.insert_signal(
                    kind=kind,
                    value_hash=value_hash,
                    reported_by_seller_id=seller_id,
                    evidence_id=evidence_id,
                    severity=2,
                    confirmed=True,
                )
            )
    return inserted


def dispute_fake_for_evidence(
    fraud_store: FraudStore,
    *,
    evidence_rows: list[dict[str, Any]],
) -> int:
    ids = [str(r["id"]) for r in evidence_rows if r.get("id")]
    return fraud_store.set_confirmed_for_evidence(evidence_ids=ids, confirmed=False)

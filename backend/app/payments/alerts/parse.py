"""Parse seller-forwarded bank alerts into normalized evidence.

Templates are fictional and based on common Nigerian bank alert wording.
Real bank wording changes frequently; this parser is intentionally a
best-effort extractor for the eval set, not a universal parser.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class BankAlert(BaseModel):
    """A parsed bank alert."""

    amount_kobo: int
    type: str = Field(..., pattern="^(credit|debit)$")
    narration: str | None = None
    balance_kobo: int | None = None
    txn_time_iso: str | None = None
    bank: str | None = None
    sender_hint: str | None = None
    reference: str | None = None


def _detect_bank(text: str, bank: str | None) -> str | None:
    if bank:
        return bank.lower()
    lowered = text.lower()
    if "gtbank" in lowered or "gtb" in lowered or "guaranty trust" in lowered:
        return "gtb"
    if "access" in lowered:
        return "access"
    if "opay" in lowered:
        return "opay"
    return None


def _find_amount_kobo(text: str) -> int | None:
    """Find the first NGN/₦/N amount and return kobo."""
    # Look for currency symbols, then digits with optional commas and decimals.
    pattern = re.compile(
        r"(?:NGN|₦|N)[\s]*([0-9,]+(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        # Also try bare "Amt: 5000" style.
        pattern = re.compile(
            r"(?:amt|amount)[\s]*[:\-]?[\s]*([0-9,]+(?:\.[0-9]{1,2})?)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
    if not match:
        return None
    return _money_to_kobo(match.group(1))


def _money_to_kobo(value: str) -> int | None:
    cleaned = value.replace(",", "").replace(" ", "")
    try:
        if "." in cleaned:
            return int(round(float(cleaned) * 100))
        return int(cleaned) * 100
    except ValueError:
        return None


def _find_balance_kobo(text: str) -> int | None:
    pattern = re.compile(
        r"(?:bal|balance)[\s]*[:\-]?[\s]*(?:NGN|₦|N)?[\s]*([0-9,]+(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return _money_to_kobo(match.group(1))
    return None


def _find_reference(text: str) -> str | None:
    for label in ("ref", "reference", "txn id", "transaction id", "trf id"):
        pattern = re.compile(
            rf"(?:{label})[\s]*[:\-]?[\s]*([A-Za-z0-9\-]+)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def _find_sender_hint(text: str, bank: str | None) -> str | None:
    # Generic "from: Name" or "sender: Name". Do not cross a newline.
    patterns = [
        re.compile(
            r"(?:from|sender|by)[:\s]+([A-Za-z][A-Za-z .\-]{0,39})(?=\n|\.|Ref|Txn|$)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:transfer from|trf from)[:\s]+([A-Za-z][A-Za-z .\-]{0,39})(?=\n|\.|Ref|Txn|$)",
            re.IGNORECASE,
        ),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip().rstrip(".").strip()
    return None


def _find_narration(text: str) -> str | None:
    for label in ("desc", "description", "narration", "details"):
        pattern = re.compile(
            rf"(?:{label})[\s]*[:\-]?[\s]*(.{{0,120}}?)(?:\n|ref|bal|date|time|$)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def _find_transaction_type(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("credited", "credit", "received", "inflow")):
        return "credit"
    if any(word in lowered for word in ("debited", "debit", "deducted", "outflow")):
        return "debit"
    return "credit"


_DATE_FORMATS = [
    "%d-%b-%Y %H:%M",
    "%d-%b-%y %H:%M",
    "%d %b %Y %H:%M",
    "%d %b %y %H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%d/%m/%Y %H:%M",
    "%d/%m/%y %H:%M",
]


def _find_time_iso(text: str) -> str | None:
    # Try to capture a date-time near a Date/Time label first.
    for label in ("date", "time", "dt"):
        pattern = re.compile(
            rf"(?:{label})[\s]*[:\-]?[\s]*(.{{0,40}}?)(?:\n|WAT|GMT|UTC|Bal|Ref|$)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            parsed = _parse_datetime(match.group(1).strip())
            if parsed:
                return parsed
    # Fall back to any date-like substring in the text.
    candidates = re.findall(r"\d{1,4}[\-/]\d{1,2}[\-/]\d{1,4}[\sT]\d{1,2}:\d{2}", text)
    for candidate in candidates:
        parsed = _parse_datetime(candidate)
        if parsed:
            return parsed
    return None


def _parse_datetime(value: str) -> str | None:
    value = value.strip().replace("Z", "+00:00")
    if value.endswith(" WAT"):
        value = value[: -len(" WAT")]
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            # Naive datetimes are treated as WAT (UTC+1) and converted to UTC.
            if dt.tzinfo is None:
                from datetime import timedelta

                dt = dt.replace(tzinfo=UTC) - timedelta(hours=1)
            return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        return None


def parse_alert(text: str, bank: str | None = None) -> BankAlert | None:
    """Parse a bank alert text into a `BankAlert`.

    Returns `None` if no amount can be extracted.
    """
    amount = _find_amount_kobo(text)
    if amount is None:
        return None

    detected_bank = _detect_bank(text, bank)
    txn_type = _find_transaction_type(text)
    narration = _find_narration(text)
    sender_hint = _find_sender_hint(text, detected_bank)
    reference = _find_reference(text)
    balance = _find_balance_kobo(text)
    txn_time = _find_time_iso(text)

    return BankAlert(
        amount_kobo=amount,
        type=txn_type,
        narration=narration,
        balance_kobo=balance,
        txn_time_iso=txn_time,
        bank=detected_bank,
        sender_hint=sender_hint or narration,
        reference=reference,
    )


def alert_to_extraction_dict(alert: BankAlert) -> dict[str, Any]:
    """Convert a parsed alert into the same shape used by screenshot extraction."""
    return {
        "is_transfer_receipt": True,
        "amount_kobo": alert.amount_kobo,
        "currency": "NGN",
        "sender_name": alert.sender_hint,
        "sender_bank": alert.bank,
        "recipient_name": None,
        "recipient_acct_last4": None,
        "reference": alert.reference,
        "status_text": "successful",
        "txn_time_iso": alert.txn_time_iso,
        "app_style": alert.bank,
        "visual_anomalies": [],
    }

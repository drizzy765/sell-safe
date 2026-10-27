"""Extract receipt fields from a buyer's screenshot. One retry, then ask to resend."""

import hashlib
from io import BytesIO
from typing import Any

from PIL import Image
from PIL.ExifTags import IFD
from pydantic import BaseModel, Field, ValidationError

from app.llm.base import LLMJsonError, LLMProvider

SCREENSHOT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "is_transfer_receipt": {"type": "boolean"},
        "amount_kobo": {"type": ["integer", "null"]},
        "currency": {"type": "string"},
        "sender_name": {"type": ["string", "null"]},
        "sender_bank": {"type": ["string", "null"]},
        "recipient_name": {"type": ["string", "null"]},
        "recipient_acct_last4": {"type": ["string", "null"]},
        "reference": {"type": ["string", "null"]},
        "status_text": {"type": ["string", "null"]},
        "txn_time_iso": {"type": ["string", "null"]},
        "app_style": {"type": ["string", "null"]},
        "visual_anomalies": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "is_transfer_receipt",
        "amount_kobo",
        "currency",
        "sender_name",
        "sender_bank",
        "recipient_name",
        "recipient_acct_last4",
        "reference",
        "status_text",
        "txn_time_iso",
        "app_style",
        "visual_anomalies",
    ],
}

_PROMPT = (
    "Extract the transfer receipt in this image. Return JSON with: "
    "is_transfer_receipt (bool), amount_kobo (integer kobo or null), currency, "
    "sender_name, sender_bank, recipient_name, recipient_acct_last4, reference, "
    "status_text, txn_time_iso (ISO 8601), app_style, visual_anomalies (list of strings). "
    "Set is_transfer_receipt=false if this is not a transfer receipt. "
    "Do not invent values you cannot see."
)


class ReceiptExtraction(BaseModel):
    is_transfer_receipt: bool
    amount_kobo: int | None
    currency: str = "NGN"
    sender_name: str | None = None
    sender_bank: str | None = None
    sender_acct_last4: str | None = None
    recipient_name: str | None = None
    recipient_acct_last4: str | None = None
    reference: str | None = None
    status_text: str | None = None
    txn_time_iso: str | None = None
    app_style: str | None = None
    visual_anomalies: list[str] = Field(default_factory=list)
    image_sha256: str = ""
    image_phash: str = ""
    metadata_editor: str | None = None


class AskResend:
    """Vision could not read the image. Ask the buyer to resend it."""


class ReceiptExtractError(RuntimeError):
    """Extraction failed after retry."""


def _average_hash(image: bytes, size: int = 8) -> str:
    """Compute a lightweight average hash using only Pillow."""
    try:
        with Image.open(BytesIO(image)) as img:
            gray = img.convert("L").resize((size, size), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
    except Exception:
        return ""
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= avg else "0" for p in pixels)
    return hex(int(bits, 2))[2:].zfill(size * size // 4)


def _metadata_editor(image: bytes) -> str | None:
    """Return editing-software name from image EXIF, if present."""
    try:
        with Image.open(BytesIO(image)) as img:
            exif = img._getexif() or {}
            for tag_id, value in exif.items():
                tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                if tag in ("Software", "MakerNote") and isinstance(value, str):
                    return value
            # Also check IFD1/thumbnail software.
            ifd1 = img.getexif().get_ifd(IFD.IFD1) or {}
            for tag_id, value in ifd1.items():
                tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                if tag == "Software" and isinstance(value, str):
                    return value
    except Exception:
        pass
    return None


def _compute_hashes(image: bytes) -> tuple[str, str]:
    sha256 = hashlib.sha256(image).hexdigest()
    return sha256, _average_hash(image)


async def extract_receipt(provider: LLMProvider, image: bytes) -> ReceiptExtraction | AskResend:
    sha256, phash_str = _compute_hashes(image)
    metadata_editor = _metadata_editor(image)
    try:
        extracted = await _once(provider, image, _PROMPT)
    except (LLMJsonError, ValidationError) as exc:
        retry_prompt = f"{_PROMPT}\n\nThe previous output was invalid: {exc}"
        try:
            extracted = await _once(provider, image, retry_prompt)
        except (LLMJsonError, ValidationError):
            return AskResend()
    extracted.image_sha256 = sha256
    extracted.image_phash = phash_str
    extracted.metadata_editor = metadata_editor
    return extracted


async def _once(provider: LLMProvider, image: bytes, prompt: str) -> ReceiptExtraction:
    payload = await provider.vision(image, prompt, SCREENSHOT_SCHEMA)
    return ReceiptExtraction.model_validate(payload)

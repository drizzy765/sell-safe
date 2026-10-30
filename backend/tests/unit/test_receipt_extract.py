import pytest

from app.llm.fake import FakeProvider
from app.verification.extract import AskResend, ReceiptExtraction, extract_receipt

_IMAGE = b"\xff\xd8not-logged"

_RECEIPT_VISION = {
    "is_transfer_receipt": True,
    "amount_kobo": 1_500_000,
    "currency": "NGN",
    "sender_name": "Ada O",
    "sender_bank": "GTBank",
    "recipient_name": "Tolu",
    "recipient_acct_last4": "1234",
    "reference": "ref-abc",
    "status_text": "successful",
    "txn_time_iso": "2026-10-27T10:00:00Z",
    "app_style": "GTWorld",
    "visual_anomalies": [],
}


@pytest.mark.asyncio
async def test_extraction_maps_vision_json() -> None:
    provider = FakeProvider(vision=dict(_RECEIPT_VISION))

    result = await extract_receipt(provider, _IMAGE)

    assert isinstance(result, ReceiptExtraction)
    assert result.is_transfer_receipt is True
    assert result.amount_kobo == 1_500_000
    assert result.reference == "ref-abc"
    assert result.image_sha256
    # Image bytes must not appear in the prompt passed to the provider.
    assert provider.vision_calls[0].count(str(_IMAGE)) == 0


@pytest.mark.asyncio
async def test_not_a_receipt_is_allowed() -> None:
    provider = FakeProvider(
        vision={
            "is_transfer_receipt": False,
            "amount_kobo": None,
            "currency": "NGN",
            "sender_name": None,
            "sender_bank": None,
            "recipient_name": None,
            "recipient_acct_last4": None,
            "reference": None,
            "status_text": None,
            "txn_time_iso": None,
            "app_style": None,
            "visual_anomalies": [],
        }
    )

    result = await extract_receipt(provider, _IMAGE)

    assert isinstance(result, ReceiptExtraction)
    assert result.is_transfer_receipt is False


@pytest.mark.asyncio
async def test_invalid_json_retries_once_then_asks_resend() -> None:
    retry = FakeProvider(vision=dict(_RECEIPT_VISION), json_failures=1)
    recovered = await extract_receipt(retry, _IMAGE)
    assert isinstance(recovered, ReceiptExtraction)
    assert recovered.amount_kobo == 1_500_000
    assert len(retry.vision_calls) == 2
    assert "invalid" in retry.vision_calls[1].lower()

    give_up = FakeProvider(json_failures=2)
    failed = await extract_receipt(give_up, _IMAGE)
    assert isinstance(failed, AskResend)
    assert len(give_up.vision_calls) == 2

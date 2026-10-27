"""Verify payment proof branch of the agent graph."""

from typing import Any

from app.agent.templates import (
    confirmed_payment,
    not_found_payment,
    release_card,
    suspicious_payment,
)
from app.channels.base import ChannelAdapter, InboundMessage
from app.db.echo_store import EchoStore
from app.db.orders import OrderStore
from app.db.payments import PaymentStore
from app.llm.base import LLMProvider
from app.verification.extract import AskResend, ReceiptExtraction, extract_receipt
from app.verification.matchers import EvidenceMatch, find_matching_evidence
from app.verification.rules import RulesResult, apply_rules
from app.verification.verdict import Verdict, decide_verdict


class VerifyResult:
    """Result of a payment verification turn."""

    def __init__(
        self,
        *,
        verdict: Verdict,
        extraction: ReceiptExtraction | None = None,
    ) -> None:
        self.verdict = verdict
        self.extraction = extraction


def _seller_account_info(seller: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if seller is None:
        return None, None
    virtual_account = seller.get("virtual_account") or {}
    return virtual_account.get("last4"), seller.get("business_name") or seller.get("name")


def _run_verdict(
    order: dict[str, Any],
    extraction: ReceiptExtraction,
    evidence_rows: list[dict[str, Any]],
    seller_last4: str | None,
    seller_name: str | None,
    pii_salt: str,
    exclude_evidence_ids: set[str] | None = None,
    current_payment_id: str | None = None,
) -> tuple[RulesResult, EvidenceMatch | None, Verdict]:
    rules_result = apply_rules(
        order,
        extraction,
        evidence_rows,
        fraud_signals=[],
        seller_account_last4=seller_last4,
        seller_name=seller_name,
        pii_salt=pii_salt,
        exclude_evidence_ids=exclude_evidence_ids,
        current_payment_id=current_payment_id,
    )
    matched = find_matching_evidence(extraction, evidence_rows)
    verdict = decide_verdict(order, extraction, rules_result, matched)
    return rules_result, matched, verdict


async def verify_payment_turn(
    message: InboundMessage,
    *,
    seller_id: str,
    buyer_id: str,
    channel_adapter: ChannelAdapter,
    store: EchoStore,
    order_store: OrderStore,
    payment_store: PaymentStore,
    provider: LLMProvider,
    pii_salt: str = "",
) -> VerifyResult:
    """Run the payment verification branch for an image receipt."""
    if not message.media_id:
        return await _respond_no_receipt(
            seller_id, buyer_id, message.sender_id, channel_adapter, store
        )

    image = await channel_adapter.fetch_media(message.media_id)
    extracted = await extract_receipt(provider, image)
    if isinstance(extracted, AskResend):
        await _send_resend_message(message.sender_id, channel_adapter, store, seller_id, buyer_id)
        return VerifyResult(verdict=_not_found_verdict("could_not_read_receipt"))

    order = order_store.get_open_order(seller_id, buyer_id)
    if order is None:
        await _send_no_order_message(message.sender_id, channel_adapter, store, seller_id, buyer_id)
        return VerifyResult(verdict=_not_found_verdict("no_open_order"), extraction=extracted)

    seller = store.get_seller(seller_id)
    seller_last4, seller_name = _seller_account_info(seller)
    evidence_rows = payment_store.get_evidence_for_order(order["id"])

    _, _, verdict = _run_verdict(
        order, extracted, evidence_rows, seller_last4, seller_name, pii_salt
    )

    _persist_evidence_and_verdict(
        payment_store,
        order,
        extracted,
        verdict,
        image_sha256=extracted.image_sha256,
        image_phash=extracted.image_phash,
    )

    if verdict.verdict == "CONFIRMED" and verdict.release_allowed:
        order_store.update_order_status(order["ref"], "paid")

    await _send_verdict_messages(
        seller_id,
        buyer_id,
        message.sender_id,
        order,
        verdict,
        channel_adapter,
        store,
    )

    return VerifyResult(verdict=verdict, extraction=extracted)


async def reevaluate_order_after_webhook(
    order: dict[str, Any],
    *,
    store: EchoStore,
    order_store: OrderStore,
    payment_store: PaymentStore,
    pii_salt: str = "",
) -> Verdict | None:
    """Re-run verdict for an order after new webhook evidence arrives.

    Returns the new verdict if a screenshot extraction exists, otherwise decides
    from the webhook evidence alone.
    """
    evidence_rows = payment_store.get_evidence_for_order(order["id"])
    if not evidence_rows:
        return None

    screenshot_rows = [r for r in evidence_rows if r.get("type") == "screenshot"]
    if screenshot_rows:
        source_row = screenshot_rows[0]
        extracted_data = source_row.get("extracted") or {}
        try:
            extraction = ReceiptExtraction.model_validate(extracted_data)
        except Exception:
            return None
        seller = store.get_seller(order["seller_id"])
        seller_last4, seller_name = _seller_account_info(seller)
        _, _, verdict = _run_verdict(
            order,
            extraction,
            evidence_rows,
            seller_last4,
            seller_name,
            pii_salt,
            exclude_evidence_ids={source_row.get("id")} if source_row.get("id") else None,
            current_payment_id=source_row.get("payment_id"),
        )
    else:
        # Webhook-only: level-4 evidence alone is treated as CONFIRMED.
        webhook_rows = [r for r in evidence_rows if r.get("type") == "va_webhook"]
        if not webhook_rows:
            return None
        best = max(webhook_rows, key=lambda r: int(r.get("trust_level") or 0))
        extracted_data = best.get("extracted") or {}
        try:
            extraction = ReceiptExtraction.model_validate(extracted_data)
        except Exception:
            return None
        _, _, verdict = _run_verdict(
            order,
            extraction,
            evidence_rows,
            None,
            None,
            pii_salt,
            exclude_evidence_ids={best.get("id")} if best.get("id") else None,
            current_payment_id=best.get("payment_id"),
        )

    payment = payment_store.get_payment_for_order(order["id"])
    if payment:
        payment["verdict"] = verdict.model_dump()

    if verdict.verdict == "CONFIRMED" and verdict.release_allowed:
        order_store.update_order_status(order["ref"], "paid")

    return verdict


def _persist_evidence_and_verdict(
    payment_store: PaymentStore,
    order: dict[str, Any],
    extraction: ReceiptExtraction,
    verdict: Verdict,
    image_sha256: str,
    image_phash: str,
) -> None:
    payment = payment_store.get_or_create_payment(
        order_id=order["id"],
        method="bank_transfer",
        expected_kobo=int(order.get("total_kobo") or 0),
    )
    payment_store.insert_evidence(
        payment_id=payment["id"],
        evidence_type="screenshot",
        source_id=image_sha256 or f"screenshot-{order['id']}",
        extracted=extraction.model_dump(exclude={"image_sha256", "image_phash", "metadata_editor"}),
        trust_level=1,
        image_sha256=image_sha256,
        image_phash=image_phash,
    )
    # Verdict persistence is intentionally a simple dict in-memory for Phase 4.
    payment["verdict"] = verdict.model_dump()


def _not_found_verdict(reason: str) -> Verdict:
    return Verdict(
        verdict="NOT_FOUND",
        confidence=0.5,
        release_allowed=False,
        reasons=[reason],
    )


async def _respond_no_receipt(
    seller_id: str,
    buyer_id: str,
    sender_id: str,
    adapter: ChannelAdapter,
    store: EchoStore,
) -> VerifyResult:
    await adapter.send_text(sender_id, "Please send a clear photo of the transfer receipt.")
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id=f"out-noreceipt-{seller_id}-{buyer_id}",
        text="Please send a clear photo of the transfer receipt.",
    )
    return VerifyResult(verdict=_not_found_verdict("no_image"))


async def _send_resend_message(
    sender_id: str,
    adapter: ChannelAdapter,
    store: EchoStore,
    seller_id: str,
    buyer_id: str,
) -> None:
    text = "I couldn't read that photo. Send it again."
    await adapter.send_text(sender_id, text)
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id=f"out-resend-{seller_id}-{buyer_id}",
        text=text,
    )


async def _send_no_order_message(
    sender_id: str,
    adapter: ChannelAdapter,
    store: EchoStore,
    seller_id: str,
    buyer_id: str,
) -> None:
    text = "I don't see an open order. Send a price question or place an order first."
    await adapter.send_text(sender_id, text)
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id=f"out-noorder-{seller_id}-{buyer_id}",
        text=text,
    )


async def _send_verdict_messages(
    seller_id: str,
    buyer_id: str,
    buyer_sender_id: str,
    order: dict[str, Any],
    verdict: Verdict,
    adapter: ChannelAdapter,
    store: EchoStore,
) -> None:
    total_kobo = int(order.get("total_kobo") or 0)
    ref = str(order.get("ref") or "")

    if verdict.verdict == "CONFIRMED":
        buyer_text = confirmed_payment(total_kobo, None, ref)
    elif verdict.verdict == "SUSPICIOUS":
        buyer_text = suspicious_payment(verdict.reasons)
    else:
        buyer_text = not_found_payment()

    await adapter.send_text(buyer_sender_id, buyer_text)
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id=f"out-verdict-{seller_id}-{buyer_id}",
        text=buyer_text,
    )

    seller_text = release_card(ref, verdict.verdict)
    store.save_outbound(
        seller_id=seller_id,
        buyer_id=buyer_id,
        channel="whatsapp",
        external_msg_id=f"out-seller-{seller_id}-{buyer_id}",
        text=seller_text,
    )

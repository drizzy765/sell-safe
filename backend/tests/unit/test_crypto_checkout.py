"""Checkout sentence and USDC formatting."""

from app.payments.crypto.checkout import crypto_checkout, expected_usdc_base, format_usdc
from app.payments.crypto.handle import crypto_instructions_for_items, extract_tx_hash


def test_format_usdc() -> None:
    assert format_usdc(15_000_000) == "15 USDC"
    assert format_usdc(15_500_000) == "15.5 USDC"


def test_checkout_sentence() -> None:
    text = crypto_checkout(
        wallet="0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1",
        usdc_base=15_000_000,
        ref="SS-1042",
        network="base-sepolia",
    )
    assert "15 USDC" in text
    assert "SS-1042" in text
    assert "0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1" in text
    assert "paste the transaction hash" in text


def test_extract_tx_hash() -> None:
    tx = "0x" + "ab" * 32
    assert extract_tx_hash(f"I paid {tx} just now") == tx
    assert extract_tx_hash("no hash here") is None


def test_instructions_need_wallet_and_usdc_items() -> None:
    total, text = crypto_instructions_for_items(
        [{"qty": 1, "unit_price_kobo": 1500000, "unit_usdc_base": 15_000_000}],
        wallet="0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1",
        network="base-sepolia",
        ref="SS-1",
    )
    assert total == 15_000_000
    assert text is not None
    assert expected_usdc_base({"expected_usdc_base": total}) == total
    none_total, none_text = crypto_instructions_for_items(
        [{"qty": 1, "unit_price_kobo": 1500000}],
        wallet="0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1",
        network="base-sepolia",
        ref="SS-1",
    )
    assert none_total is None and none_text is None

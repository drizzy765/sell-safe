"""Checkout sentence. The model copies this; it does not invent the address or amount."""

USDC_BASE = 1_000_000


def format_usdc(base_units: int) -> str:
    whole, frac = divmod(base_units, USDC_BASE)
    if frac == 0:
        return f"{whole} USDC"
    text = f"{whole}.{frac:06d}".rstrip("0")
    return f"{text} USDC"


def crypto_checkout(*, wallet: str, usdc_base: int, ref: str, network: str) -> str:
    amount = format_usdc(usdc_base)
    return (
        f"Pay {amount} in USDC on {network} to {wallet}. "
        f"Order {ref}. Then paste the transaction hash here."
    )


def expected_usdc_base(order: dict) -> int | None:
    """USDC base units (6 decimals) stored on the order. Naira kobo is not converted."""
    raw = order.get("expected_usdc_base")
    if raw is None:
        return None
    return int(raw)

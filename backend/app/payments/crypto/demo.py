"""Live crypto demo: real hash, reused hash, and a fake hash."""

from datetime import UTC, datetime, timedelta
from secrets import token_hex
from typing import Any

from pydantic import BaseModel

from app.payments.crypto.checkout import format_usdc
from app.payments.crypto.rpc import CryptoRpc
from app.payments.crypto.service import verify_tx
from app.payments.crypto.store import CryptoPaymentStore, MemoryCryptoStore
from app.payments.crypto.verify import ChainView


class DemoCase(BaseModel):
    label: str
    verdict: str
    reason: str | None = None
    tx_hash: str
    amount_usdc: str | None = None
    to_address: str | None = None
    confirmations: int | None = None
    explorer_url: str | None = None
    network: str


class DemoResult(BaseModel):
    ready: bool
    message: str | None = None
    cases: list[DemoCase] | None = None


def explorer_tx_url(explorer_base: str, tx_hash: str) -> str:
    return f"{explorer_base.rstrip('/')}/tx/{tx_hash}"


def _fake_hash() -> str:
    return "0x" + token_hex(32)


def _order(order_id: str, expected_usdc_base: int, created_at: datetime) -> dict[str, Any]:
    return {
        "id": order_id,
        "ref": f"SS-DEMO-{order_id}",
        "expected_usdc_base": expected_usdc_base,
        "created_at": created_at.isoformat(),
    }


def _expected_from_view(view: ChainView, seller_wallet: str, token_contract: str) -> int:
    from app.payments.crypto.address import require_checksum_address

    seller = require_checksum_address(seller_wallet)
    token = require_checksum_address(token_contract)
    matching = [
        row.amount
        for row in view.transfers
        if require_checksum_address(row.token) == token
        and require_checksum_address(row.recipient) == seller
    ]
    if matching:
        return sum(matching)
    return 1_000_000


def _case(
    *,
    label: str,
    verdict: str,
    reason: str | None,
    tx_hash: str,
    amount: int | None,
    to_address: str | None,
    confirmations: int | None,
    network: str,
    explorer_base: str,
) -> DemoCase:
    return DemoCase(
        label=label,
        verdict=verdict,
        reason=reason,
        tx_hash=tx_hash,
        amount_usdc=format_usdc(amount) if amount is not None else None,
        to_address=to_address,
        confirmations=confirmations,
        explorer_url=explorer_tx_url(explorer_base, tx_hash) if tx_hash.startswith("0x") else None,
        network=network,
    )


async def run_crypto_demo(
    *,
    real_tx_hash: str,
    seller_wallet: str,
    token_contract: str,
    min_confirmations: int,
    chain_id: int,
    network: str,
    explorer_base: str,
    rpc: CryptoRpc,
    store: CryptoPaymentStore | None = None,
) -> DemoResult:
    """Verify a real Base Sepolia hash, the same hash reused, and a random fake hash."""
    hash_value = real_tx_hash.strip()
    if not hash_value:
        return DemoResult(
            ready=False,
            message=(
                "DEMO_REAL_TX_HASH is not set. Add a Base Sepolia USDC transfer "
                "hash to .env, then restart the API."
            ),
            cases=None,
        )
    if not seller_wallet.strip():
        return DemoResult(
            ready=False,
            message=(
                "Demo seller wallet is not registered. "
                "POST a checksummed address to /api/sellers/crypto-wallet first."
            ),
            cases=None,
        )
    if not token_contract.strip():
        return DemoResult(
            ready=False,
            message="CRYPTO_TOKEN_CONTRACT is not set.",
            cases=None,
        )

    payments = store or MemoryCryptoStore()
    view = await rpc.load(hash_value)
    expected = _expected_from_view(view, seller_wallet, token_contract)
    # Order time before the block so a real funded transfer can confirm.
    if view.block_timestamp is not None:
        created = view.block_timestamp - timedelta(minutes=5)
    else:
        created = datetime.now(UTC) - timedelta(hours=1)

    real = await verify_tx(
        tx_hash=hash_value,
        order=_order("demo-real", expected, created),
        seller_wallet=seller_wallet,
        token_contract=token_contract,
        min_confirmations=min_confirmations,
        chain_id=chain_id,
        network=network,
        rpc=rpc,
        store=payments,
        order_created_at=created,
    )
    reused = await verify_tx(
        tx_hash=hash_value,
        order=_order("demo-reused", expected, created),
        seller_wallet=seller_wallet,
        token_contract=token_contract,
        min_confirmations=min_confirmations,
        chain_id=chain_id,
        network=network,
        rpc=rpc,
        store=payments,
        order_created_at=created,
    )
    fake_hash = _fake_hash()
    fake = await verify_tx(
        tx_hash=fake_hash,
        order=_order("demo-fake", expected, created),
        seller_wallet=seller_wallet,
        token_contract=token_contract,
        min_confirmations=min_confirmations,
        chain_id=chain_id,
        network=network,
        rpc=rpc,
        store=payments,
        order_created_at=created,
    )

    return DemoResult(
        ready=True,
        message=None,
        cases=[
            _case(
                label="real",
                verdict=real.status,
                reason=real.reason,
                tx_hash=hash_value,
                amount=real.amount,
                to_address=real.recipient or seller_wallet,
                confirmations=real.confirmations,
                network=network,
                explorer_base=explorer_base,
            ),
            _case(
                label="reused",
                verdict=reused.status,
                reason=reused.reason,
                tx_hash=hash_value,
                amount=reused.amount,
                to_address=reused.recipient or seller_wallet,
                confirmations=reused.confirmations,
                network=network,
                explorer_base=explorer_base,
            ),
            _case(
                label="fake",
                verdict=fake.status,
                reason=fake.reason,
                tx_hash=fake_hash,
                amount=fake.amount,
                to_address=fake.recipient,
                confirmations=fake.confirmations,
                network=network,
                explorer_base=explorer_base,
            ),
        ],
    )

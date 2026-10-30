"""Seller USDC wallet and the live crypto demo. No RefPay."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db.echo_store import EchoStore, MemoryEchoStore, build_store
from app.payments.crypto.address import AddressError, require_checksum_address
from app.payments.crypto.demo import DemoCase, DemoResult, run_crypto_demo
from app.payments.crypto.rpc import CryptoRpc
from app.payments.crypto.store import MemoryCryptoStore

router = APIRouter(prefix="/api", tags=["crypto"])

DEMO_SELLER_WALLET = "0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1"


class WalletRequest(BaseModel):
    address: str


class WalletResponse(BaseModel):
    address: str
    network: str


def _supabase_ready(settings: object) -> bool:
    return bool(
        getattr(settings, "supabase_url", "") and getattr(settings, "supabase_service_role_key", "")
    )


def _store(request: Request) -> EchoStore:
    current = request.app.state.store
    if current is None:
        settings = request.app.state.settings
        if _supabase_ready(settings):
            current = build_store(settings)
        else:
            current = MemoryEchoStore()
        request.app.state.store = current
    return current


def _crypto_rpc(request: Request) -> CryptoRpc | None:
    current = getattr(request.app.state, "crypto_rpc", None)
    if current is not None:
        return current
    settings = request.app.state.settings
    if not settings.crypto_rpc_url:
        return None
    return CryptoRpc(settings.crypto_rpc_url, transport=request.app.state.transport)


@router.post("/sellers/crypto-wallet", response_model=WalletResponse)
def save_crypto_wallet(body: WalletRequest, request: Request) -> WalletResponse:
    """Save the seller's receiving wallet. Optional during onboarding."""
    try:
        address = require_checksum_address(body.address)
    except AddressError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    settings = request.app.state.settings
    account_id = settings.instagram_account_id or "local-seller"
    network = settings.crypto_network or "base-sepolia"
    seller_id = _store(request).ensure_seller(account_id, channel="instagram")
    _store(request).set_crypto_wallet(seller_id, address, network)
    return WalletResponse(address=address, network=network)


@router.get("/demo/crypto", response_model=DemoResult)
async def crypto_demo(request: Request) -> DemoResult:
    """Live Base Sepolia checks: real hash, reused hash, and a fake hash."""
    settings = request.app.state.settings
    real_hash = (settings.demo_real_tx_hash or "").strip()
    if not real_hash:
        return DemoResult(
            ready=False,
            message=(
                "DEMO_REAL_TX_HASH is not set. Add a Base Sepolia USDC transfer "
                "hash to .env, then restart the API."
            ),
            cases=None,
        )

    store = _store(request)
    account_id = settings.instagram_account_id or "local-seller"
    seller_id = store.ensure_seller(account_id, channel="instagram")
    seller = store.get_seller(seller_id) or {}
    wallet = str(seller.get("crypto_wallet") or "")
    if not wallet:
        # Register the known demo seller wallet so the live demo can run.
        store.set_crypto_wallet(
            seller_id,
            DEMO_SELLER_WALLET,
            settings.crypto_network or "base-sepolia",
        )
        wallet = DEMO_SELLER_WALLET

    rpc = _crypto_rpc(request)
    if rpc is None:
        return DemoResult(
            ready=False,
            message="CRYPTO_RPC_URL is not set. Add a Base Sepolia RPC URL to .env.",
            cases=None,
        )

    demo_store = getattr(request.app.state, "crypto_demo_store", None)
    if demo_store is None:
        demo_store = MemoryCryptoStore()
        request.app.state.crypto_demo_store = demo_store
    # Fresh store per request so reused_hash is demonstrated cleanly.
    demo_store = MemoryCryptoStore()

    return await run_crypto_demo(
        real_tx_hash=real_hash,
        seller_wallet=wallet,
        token_contract=settings.crypto_token_contract,
        min_confirmations=settings.crypto_min_confirmations,
        chain_id=settings.crypto_chain_id,
        network=settings.crypto_network or "base-sepolia",
        explorer_base=settings.crypto_explorer_url or "https://sepolia.basescan.org",
        rpc=rpc,
        store=demo_store,
    )


# Re-export for OpenAPI / tests that import DemoCase.
__all__ = ["router", "DEMO_SELLER_WALLET", "DemoCase", "DemoResult", "WalletResponse"]

"""Check CRYPTO_* env: chain id, latest block, USDC symbol and decimals.

Usage (from repo root):
  PYTHONPATH=backend python -m scripts.check_crypto_rpc

Does not print RPC URLs or other secrets.
"""

from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.payments.crypto.address import require_checksum_address, to_checksum_address
from app.payments.crypto.rpc import CryptoRpc, RpcError


async def main() -> int:
    settings = get_settings()
    if not settings.crypto_rpc_url.strip():
        print("CRYPTO_RPC_URL is empty")
        return 1
    if not settings.crypto_token_contract.strip():
        print("CRYPTO_TOKEN_CONTRACT is empty")
        return 1

    try:
        token = to_checksum_address(settings.crypto_token_contract)
    except Exception as exc:
        print(f"CRYPTO_TOKEN_CONTRACT is not a valid address: {exc}")
        return 1

    rpc = CryptoRpc(settings.crypto_rpc_url)
    try:
        info = await rpc.probe(token)
    except RpcError as exc:
        print(f"RPC error: {exc}")
        return 1
    except Exception as exc:
        print(f"RPC call failed: {type(exc).__name__}")
        return 1

    expected_chain = settings.crypto_chain_id
    print(f"network={settings.crypto_network or 'unset'}")
    print(f"chain_id={info['chain_id']} expected={expected_chain}")
    print(f"latest_block={info['latest_block']}")
    print(f"token={token}")
    print(f"symbol={info['symbol']!r}")
    print(f"decimals={info['decimals']}")
    print(f"token_call_ok={info.get('token_call_ok')}")

    ok = True
    if info["chain_id"] != expected_chain:
        print("FAIL: chain id does not match CRYPTO_CHAIN_ID")
        ok = False
    if info["latest_block"] is None or info["latest_block"] <= 0:
        print("FAIL: latest block missing")
        ok = False
    if not info.get("token_call_ok"):
        print("FAIL: token eth_call returned empty (check CRYPTO_TOKEN_CONTRACT on this network)")
        ok = False
    elif info["decimals"] != 6:
        print("FAIL: expected USDC decimals=6")
        ok = False
    symbol = (info["symbol"] or "").upper()
    if info.get("token_call_ok") and "USD" not in symbol:
        print("WARN: symbol does not look like USDC")
    if settings.demo_real_tx_hash.strip():
        print("DEMO_REAL_TX_HASH=set")
    else:
        print("DEMO_REAL_TX_HASH=empty")

    # Demo seller wallet constant for operators.
    demo_wallet = "0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1"
    print(f"demo_seller_wallet={require_checksum_address(demo_wallet)}")
    print("OK" if ok else "NOT_OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

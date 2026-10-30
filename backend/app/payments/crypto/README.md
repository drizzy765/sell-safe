# backend/app/payments/crypto

Direct USDC verification on Base. No RefPay or other payment provider.

Buyer pays USDC to the seller wallet, pastes the transaction hash in Instagram DM, and Sell-Safe checks the receipt over JSON-RPC:

1. Receipt status is success.
2. Transfer logs are from `CRYPTO_TOKEN_CONTRACT` only.
3. Recipient is the seller wallet, amount ≥ order USDC (6 decimals).
4. Confirmations ≥ `CRYPTO_MIN_CONFIRMATIONS`.
5. Hash is unique (`crypto_payments.tx_hash`) and the block time is after the order.

Default network is Base Sepolia. Mainnet is an env switch.

Demo seller wallet (checksummed): `0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1`.

```bash
# Confirm RPC + token (no secrets printed)
PYTHONPATH=backend python scripts/check_crypto_rpc.py

# Register wallet
curl -X POST http://127.0.0.1:8000/api/sellers/crypto-wallet \
  -H 'Content-Type: application/json' \
  -d '{"address":"0x89d53C4A47989D4beA4a9C5972Bcca71E56012C1"}'

# Live demo (needs DEMO_REAL_TX_HASH in .env)
curl http://127.0.0.1:8000/api/demo/crypto
```

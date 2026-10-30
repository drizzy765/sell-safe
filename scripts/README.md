# scripts

Helper scripts: seed demo data (docs/demo_data.md), register webhooks, run evals, check crypto RPC.

```bash
# Confirm CRYPTO_* env (chain id, latest block, USDC symbol/decimals). No secrets printed.
PYTHONPATH=backend python scripts/check_crypto_rpc.py

# Smoke HTTP endpoints (memory TestClient, or live with SMOKE_BASE_URL=http://127.0.0.1:8000)
PYTHONPATH=backend python scripts/smoke_endpoints.py

# Apply pending SQL (0005 waitlist + 0006 crypto_payments) in the Supabase SQL editor:
# scripts/apply_pending_migrations.sql
```

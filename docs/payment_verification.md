# Payment Verification

## Evidence layers (trust level)
| Level | Layer | Source | Notes |
|---|---|---|---|
| 4 | Virtual account webhook | Paystack DVA `charge.success` / Flutterwave `charge.completed` | Signature-verified, then re-fetched via provider verify API. Strongest. |
| 4 | On-chain (optional) | RefPay / RPC: tx hash on Base Sepolia or Solana devnet, USDC | Check recipient, token contract, amount, confirmations ≥ N. |
| 3 | Mono open banking (optional) | Sandbox account transactions | Credit matching amount & time window. |
| 2 | Forwarded bank alert | Seller forwards SMS/email | Parsed; spoofable, so only trusted if forwarded by the seller's registered number/email and format matches bank template. |
| 1 | Screenshot only | Buyer image | Can never confirm alone → `UNVERIFIED` at best. |

## Step 1 – Screenshot extraction
Llama vision → JSON (see `agent.md`). Store image privately; compute perceptual hash (`imagehash`) and SHA-256.

## Step 2 – Rule checks (`verification/rules.py`)
| Rule id | Check | Effect |
|---|---|---|
| R1 amount_mismatch | extracted amount ≠ order total (tolerance ₦0) | suspicious +0.4 |
| R2 recipient_mismatch | recipient name/last4 ≠ seller's account | suspicious +0.5 |
| R3 time_window | txn time before order created or > 24h old / in future | suspicious +0.3 |
| R4 duplicate_ref | reference already used in any payment_evidence | suspicious +0.6 |
| R5 duplicate_image | image hash / phash distance ≤ 5 seen before | suspicious +0.6 |
| R6 blocklist | sender acct/phone/name in confirmed fraud_signals | suspicious +0.7 |
| R7 visual_anomaly | vision reported font/alignment/cropping anomalies | suspicious +0.2 each (max 0.4) |
| R8 status_text | "pending"/"processing" shown | not_confirmable |
| R9 metadata | EXIF shows editing software (if present) | suspicious +0.2 |
`rule_risk = min(1, sum)`.

## Step 3 – Evidence matching (`verification/matchers.py`)
A match requires: same amount_kobo AND (reference match OR sender name fuzzy ≥ 0.85) AND time within ±30 min of claimed time, AND credit to the seller's account. Each matched evidence row links to exactly one payment (unique `source_id`). Webhooks arriving before a screenshot auto-confirm the order directly.

## Step 4 – Jev scoring
Ask `evidence_match` (p_match) and `receipt_tampered` (p_tamper) with extraction, rule hits, evidence summary as context.
`confidence = p_match * (1 - max(p_tamper, rule_risk))` when evidence exists.

## Verdict table
| Evidence found (level) | Rules / Jev | Verdict | Release goods? | Seller message |
|---|---|---|---|---|
| ≥3, matches | confidence ≥ 0.90 | **CONFIRMED** | ✅ yes | "Money don land. ₦X from NAME, ref …" |
| ≥3, matches | 0.60–0.90 | **CONFIRMED (check)** | ask seller | "Looks paid – please confirm in your bank app" |
| 2 (alert), matches | any | **CONFIRMED (alert)** | seller decides; default ✅ if auto_confirm on and ≥0.90 | |
| none yet, screenshot clean | rule_risk < 0.3 | **NOT FOUND** (pending) | ❌ DON'T RELEASE | "No money yet. Wait for alert. We'll recheck for 30 min." |
| none, screenshot only | rule_risk 0.3–0.6 or p_tamper 0.4–0.6 | **UNVERIFIED** | ❌ DON'T RELEASE | |
| any | rule_risk ≥ 0.6 or p_tamper ≥ 0.6 or R4/R5/R6 hit | **SUSPICIOUS** | ❌ DON'T RELEASE | "⚠️ This receipt looks fake: reasons…" |
| ≥3 shows different amount | – | **SUSPICIOUS** (partial) | ❌ | "Only ₦Y arrived of ₦X" |
**Golden rule:** goods are released only on level ≥3 evidence (or level 2 explicitly accepted by the seller). A screenshot alone never confirms.

## Re-check loop
NOT FOUND / UNVERIFIED payments re-check every 5 min for 30 min (webhook arrival triggers immediately). Late match flips verdict to CONFIRMED and notifies both sides. After expiry → reminder to buyer (max 2), then `cancelled`.

## Scammer memory
On SUSPICIOUS confirmed by seller (`/fake SS-1042`): insert fraud_signals for sender account (hashed), buyer phone hash, image hash. Shared across sellers; only `confirmed=true` signals trigger R6. Sellers can dispute (`/notfake`).

## Webhook safety
- Paystack: verify `x-paystack-signature` = HMAC-SHA512(secret key, raw body). Flutterwave: `verif-hash` header equals configured secret. Then call verify-transaction API.
- Idempotency: `webhook_events.event_id` unique; return 200 on duplicates.
- **TODO verify** Paystack DVA availability in test mode and exact event names in current docs.

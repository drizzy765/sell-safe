# Sell-Safe Task List — Revised Priority Order

**Status:** Oct 30, 2026. Foundation complete. Payment verification is P0.
**Deadline:** Nov 5, 02:00 WAT.

Standing checks for every code task: `ruff check . && ruff format --check .`, `pytest -q -m "not live"`, Conventional Commit, no secrets.

---

## Changes from Previous Plan

**New priority order:**
1. **P0: Payment verification** — Elevated to critical path (was Phase 4, now must complete first)
2. **P1: WhatsApp waitlist** — Collect WhatsApp numbers, not email; notify on unblock
3. **P2: Simplified Instagram** — One button, hide 7 technical steps
4. **P3: Sample reply demo** — Prove value before asking for work
5. **P4: Payment safety demo** — Fake vs real screenshot, build trust
6. **P5: Stretch only** — Profile import, chat onboarding, draft catalog

**Removed/cut:**
- Voice transcription (cut)
- Fraud memory (stretch only)
- Daily summary (stretch only)
- Messenger adapter (cut)
- Full 7-step technical onboarding (replaced with one-click)

---

## P0: Payment Verification (Oct 30-31) — MUST COMPLETE

### Task 15: Receipt extraction and image hashes

**Description:** Payment images run vision into the screenshot schema. Store privately. Compute SHA-256 and perceptual hash. Trust level 1.

**Acceptance criteria:**
- [ ] Extracts: amount_kobo, reference, sender, recipient last4, status text, visual anomalies
- [ ] `is_transfer_receipt=false` does not open verdict path
- [ ] Hashes stored on evidence row

**Verification:**
- [ ] Unit test maps fake vision payload to `payment_evidence`
- [ ] Invalid JSON retries once

**Files:**
- `backend/app/verification/extract.py`
- `backend/tests/unit/test_receipt_extract.py`

**Estimated:** Medium

---

### Task 16: Rules R1–R9

**Description:** Implement `verification/rules.py` exactly per `docs/payment_verification.md`. Include weights, R7 cap, R8 `not_confirmable`.

**Acceptance criteria:**
- [ ] Each rule has pass and fail case
- [ ] `rule_risk = min(1, sum(weights))`
- [ ] Duplicate reference (R4) and blocklist (R6) fire from stored rows

**Verification:**
- [ ] Table-driven unit tests cover R1–R9
- [ ] Weights match spec

**Files:**
- `backend/app/verification/rules.py`
- `backend/tests/unit/test_rules.py`

**Estimated:** Medium

---

### Task 17: Verdict engine

**Description:** `verdict.py` is the only verdict writer. Applies trust level, match result, confidence band, hard rules. Screenshot alone never sets `release_allowed`.

**Acceptance criteria:**
- [ ] Every verdict table row has test (partial, pending, etc.)
- [ ] Level ≥3 + match + confidence ≥0.90 → CONFIRMED, `release_allowed=true`
- [ ] Rule risk ≥0.6, R4, R5, or R6 → SUSPICIOUS, `release_allowed=false`

**Verification:**
- [ ] `pytest -q -m "not live" backend/tests/unit/test_verdict.py`
- [ ] No LLM import in `verdict.py`

**Files:**
- `backend/app/verification/verdict.py`
- `backend/app/verification/matchers.py`
- `backend/tests/unit/test_verdict.py`

**Estimated:** Medium

---

### Task 18: Paystack webhook

**Description:** `POST /webhooks/paystack` checks `x-paystack-signature` HMAC-SHA512, dedupes on event id, returns 200, re-fetches transaction, inserts level-4 evidence.

**Acceptance criteria:**
- [ ] Bad signature → 401
- [ ] Duplicate event id → 200, one evidence row
- [ ] Evidence stored only after verify-transaction succeeds

**Verification:**
- [ ] Unit tests for signature, duplicate, verify-call failure
- [ ] Manual test transfer on Paystack test mode

**Files:**
- `backend/app/payments/paystack/webhook.py`
- `backend/app/payments/paystack/dva.py`
- `backend/app/api/webhooks/paystack.py`
- `backend/tests/unit/test_paystack_webhook.py`

**Estimated:** Medium

---

### Task 19: Screenshot and webhook paths to verdict

**Description:** Connect extraction, rules, matcher, Paystack evidence. Webhook can confirm before or after screenshot. `POST /orders/{ref}/release` returns 409 when `release_allowed=false`.

**Acceptance criteria:**
- [ ] Level-4 evidence → CONFIRMED (any order of arrival)
- [ ] Edited amount or reused reference → SUSPICIOUS/NOT FOUND, release blocked
- [ ] Seller message states verdict and release status

**Verification:**
- [ ] Integration tests: webhook-first, screenshot-first, release 409
- [ ] Manual: test transfer CONFIRMED; edited screenshot blocked

**Files:**
- `backend/app/verification/matchers.py`
- `backend/app/agent/graph/verify.py`
- `backend/app/api/internal/orders.py`
- `backend/tests/integration/test_verify_flow.py`

**Estimated:** Medium

---

### Task 20: Flutterwave webhook

**Description:** `POST /webhooks/flutterwave` checks `verif-hash` header, dedupes, writes level-4 evidence same as Paystack.

**Acceptance criteria:**
- [ ] Header mismatch → 401
- [ ] Matching event → confirms through verdict engine
- [ ] Duplicate → stored once

**Verification:**
- [ ] Unit test with fixture payloads
- [ ] Paystack tests still pass

**Files:**
- `backend/app/payments/flutterwave/webhook.py`
- `backend/app/api/webhooks/flutterwave.py`
- `backend/tests/unit/test_flutterwave_webhook.py`

**Estimated:** Small

---

### Checkpoint: After Tasks 15-20
- [ ] Test transfer → CONFIRMED
- [ ] Edited screenshot → SUSPICIOUS, release 409
- [ ] Verdict table fully tested
- [ ] Zero screenshot-only CONFIRMED paths
- [ ] Review with human before P1

---

## P1: WhatsApp Waitlist (Nov 1)

### Task WA-1: Waitlist schema

**Description:** Add table to store WhatsApp numbers for notification when WhatsApp unblocks.

**Acceptance criteria:**
- [ ] Table: `whatsapp_waitlist(id, phone_number, created_at, notified_at)`
- [ ] Phone number validated (Nigeria format)
- [ ] Unique constraint on phone_number

**Files:**
- `backend/app/db/migrations/0005_waitlist.sql`

**Estimated:** Small

---

### Task WA-2: Waitlist UI component

**Description:** "Coming soon to WhatsApp" card with phone number input and "Notify me" button.

**Acceptance criteria:**
- [ ] Prominent card on platform selection
- [ ] Phone input with Nigeria +234 prefix
- [ ] Success message: "We'll message you on WhatsApp when ready"

**Files:**
- `web/components/WhatsAppWaitlist.tsx`
- `web/content/whatsapp.ts` (update to show waitlist, not setup steps)

**Estimated:** Small

---

### Task WA-3: Waitlist API endpoint

**Description:** `POST /api/waitlist` stores WhatsApp number.

**Acceptance criteria:**
- [ ] Accepts `{phone_number}`
- [ ] Validates Nigeria format
- [ ] Returns 201 on success, 409 if already registered

**Files:**
- `backend/app/api/internal/waitlist.py`

**Estimated:** Small

---

### Task WA-4: Future notification endpoint (stub)

**Description:** `POST /api/waitlist/notify` — for when WhatsApp unblocks, send message with one-tap connect link.

**Acceptance criteria:**
- [ ] Stub endpoint (returns 501 "Not implemented")
- [ ] Documented how it will work

**Files:**
- `backend/app/api/internal/waitlist.py`

**Estimated:** Small

---

### Checkpoint: After P1
- [ ] Seller can enter WhatsApp number
- [ ] "Coming soon" messaging clear
- [ ] Phone number validated

---

## P2: Simplified Instagram Connect (Nov 1)

### Task IG-1: Replace 7-step guide with one-click

**Description:** Current guide has 7 technical steps. Replace with single "Connect Instagram" button using Instagram Login API.

**Acceptance criteria:**
- [ ] One prominent button: "Connect Instagram"
- [ ] OAuth flow handles authentication
- [ ] On success: redirect to sample reply demo

**Files:**
- `web/content/instagram.ts` (simplify)
- `web/components/InstagramConnect.tsx` (new)

**Estimated:** Medium

---

### Task IG-2: Hide technical steps

**Description:** Move current 7-step guide behind "Advanced setup (for developers)" collapsible.

**Acceptance criteria:**
- [ ] Technical steps hidden by default
- [ ] Expandable for developers who need manual setup
- [ ] Copy buttons still work for manual flow

**Files:**
- `web/components/AdvancedSetup.tsx` (new)
- `web/content/instagram.ts`

**Estimated:** Small

---

### Checkpoint: After P2
- [ ] Instagram connect is one click
- [ ] Technical steps hidden but accessible
- [ ] Seller lands in sample reply demo after connect

---

## P3: Sample Reply Demo (Nov 1)

### Task DEMO-1: Mock customer message generator

**Description:** Generate realistic customer questions based on seller's actual products.

**Acceptance criteria:**
- [ ] Reads seller's first product from connected Instagram
- [ ] Generates 3 mock questions (price, availability, delivery)
- [ ] Questions in English, Pidgin, Yoruba options

**Files:**
- `backend/app/demo/mock_questions.py`

**Estimated:** Small

---

### Task DEMO-2: Live reply preview

**Description:** Show LLM-generated reply to mock question using seller's real product.

**Acceptance criteria:**
- [ ] Mock question displayed
- [ ] LLM generates reply in real-time
- [ ] Reply uses seller's product name, price, tone
- [ ] Display: "This is how Sell-Safe replies to your customers"

**Files:**
- `web/components/SampleReplyDemo.tsx`
- `backend/app/api/demo/sample_reply.py`

**Estimated:** Medium

---

### Task DEMO-3: Demo state management

**Description:** Track whether seller has seen demo.

**Acceptance criteria:**
- [ ] `sellers.demo_seen` boolean flag
- [ ] After demo, proceed to payment safety demo

**Files:**
- `backend/app/db/migrations/0006_demo_flags.sql`

**Estimated:** Small

---

### Checkpoint: After P3
- [ ] Seller sees sample reply before any configuration
- [ ] Reply uses their real product
- [ ] Clear value proposition demonstrated

---

## P4: Payment Safety Demo (Nov 1-2)

### Task SAFE-1: Fake screenshot fixture

**Description:** Create synthetic fake transfer screenshot for demo purposes.

**Acceptance criteria:**
- [ ] Image: Edited amount (₦50,000 → ₦20,000)
- [ ] Clearly marked as demo/fake
- [ ] No real account numbers

**Files:**
- `evals/data/synthetic/demo_fake.png`

**Estimated:** Small

---

### Task SAFE-2: Demo UI component

**Description:** Side-by-side comparison: fake vs real, SUSPICIOUS vs CONFIRMED.

**Acceptance criteria:**
- [ ] Left: Fake screenshot → SUSPICIOUS verdict
- [ ] Right: Real bank alert → CONFIRMED verdict
- [ ] Explanation text: "Sell-Safe checks every payment"
- [ ] "Start selling" CTA at bottom

**Files:**
- `web/components/PaymentSafetyDemo.tsx`

**Estimated:** Medium

---

### Task SAFE-3: Demo verdict endpoint

**Description:** `GET /api/demo/verdict` returns verdict for demo images (no real processing).

**Acceptance criteria:**
- [ ] Returns canned SUSPICIOUS for fake
- [ ] Returns canned CONFIRMED for real
- [ ] Fast response, no LLM call needed

**Files:**
- `backend/app/api/demo/verdict.py`

**Estimated:** Small

---

### Checkpoint: After P4
- [ ] Seller sees fake caught and real confirmed
- [ ] Trust established
- [ ] Ready to start selling

---

## P5: Stretch (Nov 2, only if P0-P4 solid)

### Task STRETCH-1: Profile import (opt-in)

**Description:** Fetch recent Instagram posts, extract products, show "approve/edit/skip."

**Constraints:**
- Opt-in only
- Recent public posts only
- Nothing goes live without approval
- Frame as "organizing your catalog," not "watching you"

**Files:**
- `backend/app/instagram/import.py`
- `web/components/ProfileImport.tsx`

**Estimated:** Medium

---

### Task STRETCH-2: Chat-style onboarding

**Description:** Conversational flow, pre-fill from profile, policies one at a time.

**Features:**
- [ ] "Do this later" on every step
- [ ] Smart defaults based on business type
- [ ] Partial setup flag

**Files:**
- `web/components/ChatOnboarding.tsx`

**Estimated:** Medium

---

### Task STRETCH-3: Draft catalog from posts

**Description:** Approve/edit/skip UI for imported products.

**Features:**
- [ ] Grid of suggested products
- [ ] Edit name, price, description
- [ ] Skip (don't add)
- [ ] Bulk approve

**Files:**
- `web/components/DraftCatalog.tsx`

**Estimated:** Medium

---

### Checkpoint: Stretch Complete
- [ ] Profile import works (opt-in)
- [ ] Chat onboarding smooth
- [ ] Draft catalog functional

---

## Phase 7: Freeze and Submit (Nov 2-4)

### Task FREEZE-1: Feature freeze

**Description:** Tag `v0.1-demo`, lock eval datasets.

**Acceptance criteria:**
- [ ] Tag `v0.1-demo` created
- [ ] No new features after 23:59 WAT Nov 2
- [ ] Deployed URL stable

**Estimated:** Small

---

### Task DEMO-1: Seed demo data

**Description:** `python -m scripts.seed_demo` loads Tolu's Bags scenario.

**Acceptance criteria:**
- [ ] Idempotent
- [ ] Amounts match demo doc
- [ ] Refuses to run in production without flag

**Files:**
- `scripts/seed_demo.py`

**Estimated:** Small

---

### Task DEMO-2: Final video

**Description:** Two takes, edit, captions, ≤3 minutes.

**Scenes:**
1. Product photo → catalog item
2. Pidgin price question → order
3. Fake screenshot → SUSPICIOUS
4. Real webhook → CONFIRMED

**Acceptance criteria:**
- [ ] ≤3 minutes
- [ ] Logged-out viewable
- [ ] No real account numbers

**Estimated:** Small (human)

---

### Task SUBMIT-1: Final README and screenshots

**Description:** README, screenshots, architecture, pre-submit tests.

**Acceptance criteria:**
- [ ] Fresh order → CONFIRMED
- [ ] Fake screenshot → SUSPICIOUS, 409
- [ ] Duplicate webhook → 200, one row
- [ ] `pytest`, evals, gitleaks green

**Files:**
- `README.md`
- `docs/hackathon_launch.md`

**Estimated:** Medium

---

### Task SUBMIT-2: Submit

**Description:** Submit by 18:00 WAT, tag `v1.0-submission`.

**Acceptance criteria:**
- [ ] Repo public, MIT license
- [ ] Confirmation saved
- [ ] Tag exists on submitted commit

**Estimated:** Small (human)

---

## Cut List (If Behind Schedule)

**Cut in this order:**
1. Draft catalog from posts (P5)
2. Chat-style onboarding (P5)
3. Profile import (P5)
4. Voice transcription (already cut)
5. Fraud memory (already cut)
6. Daily summary (already cut)
7. Payment reminders (already cut)
8. Messenger adapter (already cut)
9. Web onboarding beyond one page (keep simple)

**Never cut:**
- Payment verification (Tasks 15-20)
- Sample reply demo
- Payment safety demo
- Simplified Instagram connect
- WhatsApp waitlist
- Demo video

---

## Design Principles (New)

1. **Hide all technical complexity.** No visible Meta app IDs, webhook URLs, verify tokens.
2. **Feel like a helpful assistant, not a form.** Conversational, warm.
3. **Prove value before asking for work.** Sample reply demo first.
4. **Never sound like surveillance.** Frame as "organizing," not "watching."
5. **WhatsApp number, not email.** Meet sellers where they are.
6. **"Do this later" on every step.** Partial setup is fine.

---

## Standing Definition of Done

- Branch `feat/…`, one concern, Conventional Commit, PR into `main`
- `ruff check . && ruff format --check .` pass
- `pytest -q -m "not live"` passes
- New env names in `.env.example` only
- No secrets, real phone numbers, or real receipts
- User-visible work saves a clip under `demo/clips/`

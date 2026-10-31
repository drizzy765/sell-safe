# Sell-Safe Task List — Full Feature Set

**Status:** Oct 30, 2026. Foundation complete. Payment verification is P0.
**Deadline:** Nov 5, 02:00 WAT.
**Belief:** We can finish everything. Nothing is cut.

Standing checks for every code task: `ruff check . && ruff format --check .`, `pytest -q -m "not live"`, Conventional Commit, no secrets.

---

## Philosophy: Nothing Is Cut

We have 6 days. The foundation is solid. We can build everything.

**Priority order:**
1. **P0:** Payment verification (must work flawlessly)
2. **P1-P4:** Onboarding improvements (waitlist, simplified connect, demos)
3. **P5:** Everything else (bank alerts, evals, voice, fraud memory, reminders)

**If time gets tight:** Defer P5 features, but try to build them all.

---

## P0: Payment Verification (Oct 30-31) — MUST COMPLETE FIRST

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

## P5: Verification V2 (Nov 2)

### Task 21: Forwarded bank-alert parser

**Description:** Parse seller-forwarded SMS or email into structured evidence. GTB, Access, OPay formats. Trust level 2.

**Acceptance criteria:**
- [ ] Credit and debit fixtures parse to kobo and UTC timestamps
- [ ] Buyer-originated alert not stored as seller evidence
- [ ] `POST /alerts/sms` requires secret

**Verification:**
- [ ] Fixture tests in `evals/fixtures/` and `backend/tests/unit/test_alerts.py`
- [ ] Matcher can link level-2 alert to order

**Files:**
- `backend/app/payments/alerts/parse.py`
- `backend/app/api/webhooks/alerts.py`
- `evals/fixtures/bank_alerts.txt`
- `backend/tests/unit/test_alerts.py`

**Estimated:** Medium

---

### Task 22: Jev tamper and match scores

**Description:** Ask `receipt_tampered` and `evidence_match`. `confidence = p_match * (1 - max(p_tamper, rule_risk))`.

**Acceptance criteria:**
- [ ] Formula matches `docs/payment_verification.md`
- [ ] Missing Jev scores don't upgrade verdict to CONFIRMED
- [ ] Scores stored on `verdicts.jev_scores`

**Verification:**
- [ ] Unit tests for three bands and Jev outage
- [ ] Question ids match `docs/agent.md`

**Files:**
- `backend/app/decisions/questions.py`
- `backend/app/verification/verdict.py`
- `backend/tests/unit/test_confidence.py`

**Estimated:** Small

---

### Task 23: Seller verdict card + human-in-the-loop

**Description:** Seller receives verdict template. Confidence 0.60–0.90 waits for `/release` or rejection. NOT FOUND rechecks for 30 min. Reminders max 2.

**Acceptance criteria:**
- [ ] Mid-band confidence never sets `release_allowed` until seller accepts
- [ ] Late matching webhook flips NOT FOUND to CONFIRMED
- [ ] Reminder count stops at 2

**Verification:**
- [ ] Integration test with clock fixture for 30-min window
- [ ] Seller command resumes stored checkpoint

**Files:**
- `backend/app/agent/graph/verify.py`
- `backend/app/agent/templates.py`
- `backend/app/jobs/recheck.py`
- `backend/tests/integration/test_recheck.py`

**Estimated:** Medium

---

### Task 24: Eval runner and synthetic set v1

**Description:** `python -m evals.run` scores extraction and verdicts. v1 set: 20+ synthetic images, `labels.jsonl`.

**Acceptance criteria:**
- [ ] Report at `evals/report.md` includes confusion matrix
- [ ] Fake labelled class returning CONFIRMED fails the run
- [ ] Real-derived images in `evals/data/private/` (gitignored)

**Verification:**
- [ ] `python -m evals.run` exits 0 on synthetic set
- [ ] Fixture forcing CONFIRMED on fake fails gate

**Files:**
- `evals/run.py`
- `evals/data/synthetic/labels.jsonl`
- `evals/gen_receipts.py`
- `backend/tests/unit/test_eval_gate.py`

**Estimated:** Medium

---

### Checkpoint: After Tasks 21-24
- [ ] Bank alerts parse correctly
- [ ] Jev scores integrated
- [ ] Human-in-the-loop for mid-confidence
- [ ] Eval runner passes synthetic set
- [ ] Review with human before P6

---

## P6: Fraud + Ops (Nov 2-3)

### Task 28: Scammer memory

**Description:** Seller command `/fake SS-1042` inserts confirmed `fraud_signals`. `/notfake` disputes. Only `confirmed=true` triggers R6.

**Acceptance criteria:**
- [ ] Confirmed signal from seller A flags seller B's matching evidence
- [ ] Unconfirmed signals don't add R6
- [ ] Raw account numbers stored only as hashes

**Verification:**
- [ ] Unit test across two seller ids
- [ ] Manual: repeat scammer flagged, clip saved

**Files:**
- `backend/app/verification/fraud.py`
- `backend/app/agent/graph/seller_cmd.py`
- `backend/tests/unit/test_fraud_signals.py`

**Estimated:** Medium

---

### Task 29: Payment reminders and daily summary

**Description:** Cron endpoints `POST /jobs/reminders` and `POST /jobs/daily-summary`. Max 2 reminders. Summary includes ₦ saved.

**Acceptance criteria:**
- [ ] Unpaid orders get at most two reminders
- [ ] Summary counts SUSPICIOUS/NOT FOUND with goods held, no later CONFIRMED within 48h
- [ ] Both routes reject missing internal token

**Verification:**
- [ ] Unit tests for naira-saved query and reminder cap
- [ ] Manual summary message on test number

**Files:**
- `backend/app/jobs/reminders.py`
- `backend/app/jobs/daily_summary.py`
- `backend/app/api/internal/jobs.py`
- `backend/tests/unit/test_daily_summary.py`

**Estimated:** Medium

---

### Checkpoint: After Tasks 28-29
- [ ] Repeat scammer flagged across sellers
- [ ] Daily summary includes ₦ saved
- [ ] Review with human before P7

---

## P7: Voice + Channels (Nov 3)

### Task 27: Voice-note transcription

**Description:** Audio messages call Intron Sahara STT (Yoruba-English `yo`, Pidgin-English `pcm`, English `en`). Transcript stored, re-enters graph as text.

**Acceptance criteria:**
- [ ] Voice note with fake transcript can search catalog and create order
- [ ] Transcription failure replies "please type that" template
- [ ] Audio bytes not logged

**Verification:**
- [ ] Unit test with fake Intron client (no live call, no audio in logs)
- [ ] Manual voice note on Instagram

**Files:**
- `backend/app/speech/` (Intron STT/TTS client)
- `backend/app/agent/graph/nodes.py`
- `backend/tests/unit/test_voice_note.py`

**Estimated:** Small

---

### Checkpoint: After Task 27
- [ ] Voice note transcribed (yo, pcm, en)
- [ ] Order flow works with voice
- [ ] Review with human before P8

---

## P8: Demo + Freeze (Nov 2-4)

### Task 25: Demo storyboard draft

**Description:** Write 2:45 storyboard: hook, catalog, Pidgin order, fake caught, webhook confirmed, close.

**Acceptance criteria:**
- [ ] Each scene has visual and voiceover line
- [ ] Runtime ≤3 minutes
- [ ] No real phone numbers or account numbers

**Verification:**
- [ ] Script read aloud once
- [ ] Saved under `demo/`

**Files:**
- `demo/storyboard.md`

**Estimated:** Small (human)

---

### Task 30: Onboarding site polish

**Description:** Finish `web/`: platform tabs, copy buttons, theme. Remove TODOs, verify against current Meta docs.

**Acceptance criteria:**
- [ ] `/`, `/?platform=instagram` show correct steps
- [ ] Copy control announces "Copied"
- [ ] Light/dark/system themes work

**Verification:**
- [ ] `npm run lint && npm run build` in `web/`
- [ ] Keyboard tab change works

**Files:**
- `web/app/page.tsx`
- `web/components/PlatformTabs.tsx`
- `web/components/StepCard.tsx`
- `web/content/whatsapp.ts`
- `web/content/instagram.ts`
- `web/content/messenger.ts`

**Estimated:** Medium

---

### Task 31: Rough demo recording

**Description:** Screen recording: catalog, Pidgin order, suspicious screenshot, webhook confirmation.

**Acceptance criteria:**
- [ ] All four beats visible
- [ ] No live customer data
- [ ] Notes on reshoots written

**Verification:**
- [ ] Clip plays locally
- [ ] Storyboard gaps listed

**Files:**
- `demo/storyboard.md`

**Estimated:** Small (human)

---

### Task 32: Status, FAQ, privacy

**Description:** Finish `/status`, `/faq`, `/privacy`. Status: idle, checking, connected, failed. Mobile-first, accessible.

**Acceptance criteria:**
- [ ] `/status` shows connected and failed, links to FAQ
- [ ] `/privacy` lists stored data in plain language
- [ ] Below 640px: one column, code blocks scroll

**Verification:**
- [ ] Browser pass: desktop + narrow viewport
- [ ] `npm run build` succeeds

**Files:**
- `web/app/status/page.tsx`
- `web/app/faq/page.tsx`
- `web/app/privacy/page.tsx`
- `web/components/StatusCheck.tsx`

**Estimated:** Medium

---

### Task 33: Deploy and tag v0.1-demo

**Description:** API on Render/Railway. Site on Vercel. Secrets in host env only. Tag `v0.1-demo`.

**Acceptance criteria:**
- [ ] Public `/health` returns ok
- [ ] Instagram webhook on deployed URL works
- [ ] Tag `v0.1-demo` exists

**Verification:**
- [ ] Fresh test message on deployed bot
- [ ] No secrets in build logs

**Files:**
- `README.md`

**Estimated:** Medium

---

### Task 35: Seed demo data

**Description:** `python -m scripts.seed_demo` loads Tolu's Bags, products, buyers, scammer scenario.

**Acceptance criteria:**
- [ ] Idempotent
- [ ] Amounts match demo doc
- [ ] Refuses to run in production without flag

**Verification:**
- [ ] Unit test of seed payload
- [ ] Running twice doesn't duplicate

**Files:**
- `scripts/seed_demo.py`
- `backend/tests/unit/test_seed_demo.py`

**Estimated:** Small

---

### Task 36: Final video

**Description:** Two takes, edit, captions, 1080p, ≤3 minutes, unlisted YouTube/Loom.

**Acceptance criteria:**
- [ ] Logged-out browser can view
- [ ] Fake receipt and real payment on screen
- [ ] No real account numbers

**Verification:**
- [ ] Watch in private window
- [ ] Link in submission notes

**Files:**
- `demo/storyboard.md`

**Estimated:** Small (human)

---

### Checkpoint: After Tasks 25, 30-33, 35-36
- [ ] Feature freeze at 23:59 WAT Nov 2
- [ ] Tag `v0.1-demo`
- [ ] Deployed URL stable
- [ ] Demo video ≤3 minutes
- [ ] Demo seller and products exist

---

## P9: Submit (Nov 4)

### Task 37: README, screenshots, pre-submit tests

**Description:** Public README: pitch, setup, architecture. Screenshots: catalog, Pidgin, Yoruba, SUSPICIOUS, CONFIRMED, summary.

**Acceptance criteria:**
- [ ] Fresh order → test pay → CONFIRMED
- [ ] Fake screenshot → SUSPICIOUS, release 409
- [ ] Duplicate webhook → 200, one row
- [ ] `pytest`, evals, gitleaks green

**Verification:**
- [ ] `docs/hackathon_launch.md` checklist ticked
- [ ] README setup commands match repo

**Files:**
- `README.md`
- `docs/hackathon_launch.md`
- `web/public/screenshots/`

**Estimated:** Medium

---

### Task 38: Submit and tag v1.0-submission

**Description:** Submit Indie track by 18:00 WAT. Save confirmation. Tag `v1.0-submission`.

**Acceptance criteria:**
- [ ] Repo public, MIT license
- [ ] Write-up uses measured numbers only
- [ ] Confirmation saved (outside repo if personal data)

**Verification:**
- [ ] Submission page shows received
- [ ] Tag on submitted commit

**Files:**
- `README.md`
- `LICENSE`

**Estimated:** Small (human)

---

### Checkpoint: After Tasks 37-38
- [ ] Submitted by 18:00 WAT
- [ ] Confirmation saved
- [ ] Tests, evals, gitleaks green on tag

---

## P10: Stretch (Nov 4, if time)

### Task 34: Direct Base USDC (replaces RefPay)

**Description:** Buyers pay USDC on Base. Sell-Safe verifies the tx hash over JSON-RPC. No RefPay. Messenger remains a separate stretch if time remains.

**Acceptance criteria:**
- [x] Seller wallet saved as checksummed EVM address (optional, "Do this later")
- [x] Checkout sentence includes wallet, USDC amount, order ref
- [x] Buyer pastes tx hash → receipt success, correct token, seller `to`, amount, confirmations, unique hash, after order time
- [x] CONFIRMED / PENDING / SUSPICIOUS map to the existing verdict model
- [x] `crypto_payments` table with unique `tx_hash`
- [x] Demo shows real Base Sepolia confirm vs reused hash
- [x] Tests for each verification rule

**Files:**
- `backend/app/payments/crypto/`
- `backend/app/db/migrations/0006_crypto_payments.sql`

**Estimated:** Medium

---

## Summary Table

| Phase | Tasks | Timeline | Status |
|---|---|---|---|
| P0 | 15-20 | Oct 30-31 | ⏸️ Not started |
| P1 | WA 1-4 | Nov 1 | ⏸️ Not started |
| P2 | IG 1-2 | Nov 1 | ⏸️ Not started |
| P3 | DEMO 1-3 | Nov 1 | ⏸️ Not started |
| P4 | SAFE 1-3 | Nov 1-2 | ⏸️ Not started |
| P5 | 21-24 | Nov 2 | ⏸️ Not started |
| P6 | 28-29 | Nov 2-3 | ⏸️ Not started |
| P7 | 27 | Nov 3 | ⏸️ Not started |
| P8 | 25, 30-33, 35-36 | Nov 2-3 | ⏸️ Not started |
| P9 | 37-38 | Nov 4 | ⏸️ Not started |
| P10 | 34 | Nov 4 (if time) | ⏸️ Not started |

**Total:** ~38 tasks in 6 days = ~6 tasks/day

---

## Design Principles (All Tasks)

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

---

## Final Note

**Status refresh (Oct 31):** P0–P7 and P10 (crypto) are largely merged. Checklist rows above are stale for those phases.

**Finish order before Meta submit:**
1. Website redesign (`docs/design/website-design-plan.md`)
2. SellSafe-Bench best-effort — **partial OK**; full bench does not block submit
3. Deploy + `v0.1-demo` + README / pre-submit
4. **Demo video last**
5. Submit + `v1.0-submission` (P9)

Website redesign and demo video both land before the deadline. Full benchmark is optional for Meta.

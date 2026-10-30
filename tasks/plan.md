# Implementation Plan: Sell-Safe

## Overview

Sell-Safe is a **payment safety layer** for Nigerian small sellers on Instagram and WhatsApp. It verifies transfer screenshots against real bank evidence before goods leave the shop. The LLM phrases replies; it never sets a payment verdict. The verdict engine does.

**Current status:** Oct 30, 2026. Phases 1-3 complete (foundation, LLM, buyer chat). WhatsApp locked (error 131031). Instagram working. 155/156 tests passing.

**Deadline:** Nov 5, 02:00 WAT (hard stop). Feature freeze: Nov 2, 23:59 WAT.

---

## Changes from Previous Plan

| Aspect | Before | Now |
|---|---|---|
| **Primary channel** | WhatsApp-first | Instagram-first (WhatsApp locked) |
| **Onboarding** | 7 technical Meta steps | One "Connect Instagram" button; hide complexity |
| **WhatsApp** | Full setup guide | "Coming Soon" waitlist with phone number capture |
| **Core feature** | Same priority | Elevated to P0: payment verification must be flawless |
| **Value demonstration** | Happens after setup | Sample reply demo *before* seller does any work |
| **Safety demo** | None | New: fake vs real screenshot comparison |

---

## Architecture Decisions (Unchanged)

- **Code lives in `backend/app/` and `web/`** as already implemented
- **One brain, channel adapters at the edge** — WhatsApp, Instagram, Messenger normalize to `InboundMessage`
- **`LLMProvider` is the only LLM entry** — Meta Muse target, Groq fallback
- **Verdicts come only from `backend/app/verification/`** — deterministic engine, no LLM decides
- **Money is integer kobo. Times are UTC `timestamptz`.**
- **Webhooks:** verify signature, dedupe, return 200 fast, process async

---

## Dependency Graph

```
settings + /health + CI ✓
         │
         ├── SQL schema ✓
         │       │
         │       ├── repos (sellers, products, orders, messages) ✓
         │       │
         │       └── webhook dedupe ✓
         │
         ├── Instagram adapter ✓
         │       │
         │       └── Working DMs (seller catalog, buyer orders)
         │
         └── LLMProvider (Groq, Meta) ✓
                 │
                 ├── vision: photo → catalog item ✓
                 │
                 ├── Jev route → sales graph → order ✓
                 │
                 └── vision: receipt extract → rules → verdict ← P0 PRIORITY
                         │
                         ├── Paystack webhook (level 4) → CONFIRMED
                         ├── bank alert (level 2) → seller decides
                         └── evidence matching → verdict

web/ onboarding (P1-P4)
    ├── WhatsApp waitlist (phone number capture)
    ├── Simplified Instagram connect (one button)
    ├── Sample reply demo (prove value first)
    └── Payment safety demo (fake vs real)
```

---

## New Priority Order

### P0: Payment Verification (Tasks 15-20)
**The core promise. Must work flawlessly.**

| Task | What | Why Critical |
|---|---|---|
| 15 | Receipt extraction | Vision reads screenshot fields |
| 16 | Rules R1–R9 | Hard-coded fraud detection rules |
| 17 | Verdict engine | CONFIRMED/SUSPICIOUS/NOT_FOUND logic |
| 18 | Paystack webhook | Level-4 evidence from real bank |
| 19 | Screenshot+webhook → verdict | Full verification flow |
| 20 | Flutterwave webhook | Backup payment provider |

**Success criteria:**
- Fake screenshot → SUSPICIOUS → release blocked
- Real Paystack webhook → CONFIRMED → release allowed
- Edited amount → NOT FOUND → release blocked
- No path confirms from screenshot alone

---

### P1: WhatsApp Waitlist

| Component | Description |
|---|---|
| UI | "WhatsApp coming soon — get notified" card with phone input |
| Backend | `POST /api/waitlist` stores `{whatsapp_number, created_at}` |
| Future | `POST /api/waitlist/notify` sends WhatsApp message with one-tap connect link |

**Why WhatsApp number, not email:** Nigerian sellers live on WhatsApp. When it's unblocked, we message them where they already are.

---

### P2: Simplified Instagram Connect

| Current (Overwhelming) | New (Simple) |
|---|---|
| 7 technical steps with Meta app IDs | One "Connect Instagram" button |
| Webhook URL, verify token, permissions | OAuth flow handles it |
| Code blocks to copy | Automatic configuration |
| "Link to Facebook Page" | Handled by Instagram Login API |

**Technical steps hidden behind:** "Advanced setup (for developers)" link

---

### P3: Sample Reply Demo

| Flow | Description |
|---|---|
| Step 1 | Seller connects Instagram, Sell-Safe reads one product from their profile |
| Step 2 | Mock customer asks: "How much for the [product name]?" |
| Step 3 | LLM generates reply using seller's actual product, price, and tone |
| Step 4 | Seller sees: "This is how Sell-Safe would reply to your customers" |

**Value proposition:** Prove it works before asking for business details.

---

### P4: Payment Safety Demo

| Screen | Content |
|---|---|
| Left side | Fake transfer screenshot (edited amount: ₦50,000 → ₦20,000) |
| Right side | Real bank alert from Paystack |
| Verdicts | SUSPICIOUS vs CONFIRMED |
| Explanation | "Sell-Safe checks every screenshot against real bank data" |

**Builds trust:** Shows the problem and the solution.

---

### P5: Stretch (Only if P0-P4 Are Solid)

| Feature | Description |
|---|---|
| Profile import | Fetch recent Instagram posts, extract products, show "approve/edit/skip" |
| Chat onboarding | Conversational flow, pre-fill from profile, policies one at a time |
| Draft catalog | Public posts only, opt-in, nothing live without approval |
| "Do this later" | Every step has skip option; partial setup flag |

---

## Task List (Reordered by Priority)

### Phase 4: Payment Verification (Oct 30-31) — P0

- [ ] Task 15: Receipt extraction and image hashes
- [ ] Task 16: Rules R1–R9
- [ ] Task 17: Verdict engine
- [ ] Task 18: Paystack webhook
- [ ] Task 19: Screenshot and webhook paths to verdict
- [ ] Task 20: Flutterwave webhook

**Checkpoint:**
- [ ] Test transfer CONFIRMED with release allowed
- [ ] Fake screenshot SUSPICIOUS with release blocked
- [ ] Every verdict table row has a test
- [ ] Review before moving to P1

---

### Phase 5: WhatsApp Waitlist (Nov 1) — P1

- [ ] Add waitlist table to schema
- [ ] Build waitlist UI component (phone number input)
- [ ] `POST /api/waitlist` endpoint
- [ ] Update platform tabs: WhatsApp shows "Coming soon"

---

### Phase 6: Simplified Onboarding (Nov 1) — P2-P4

- [ ] Replace 7-step Instagram guide with one-click OAuth
- [ ] Sample reply demo component
- [ ] Payment safety demo component
- [ ] Update onboarding copy to match principles

---

### Phase 7: Freeze and Demo (Nov 2-4)

- [ ] Tag `v0.1-demo`
- [ ] Seed demo data
- [ ] Record video (two takes, edit, captions)
- [ ] Final README, screenshots
- [ ] Submit

---

## Design Principles

1. **Hide all technical complexity.** No Meta app IDs, webhook URLs, or verify tokens visible to sellers.
2. **Feel like a helpful assistant, not a form.** Conversational, warm, never bureaucratic.
3. **Prove value before asking for work.** Sample reply demo first, business details second.
4. **Never sound like surveillance.** Frame profile import as "organizing your public posts," not "watching you."
5. **WhatsApp number, not email.** Meet sellers where they are.
6. **"Do this later" on every step.** Partial setup is better than abandoned setup.

---

## What Never Gets Cut

- Payment verification (screenshot → SUSPICIOUS, webhook → CONFIRMED)
- Sample reply demo
- Payment safety demo
- Simplified Instagram connect
- Demo video

## Cut List (If Behind)

1. Draft catalog from Instagram posts
2. Chat-style onboarding
3. Voice transcription
4. Fraud memory
5. Daily summary
6. Payment reminders
7. Messenger adapter
8. Advanced onboarding features

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Verdict engine false CONFIRMED on fake | Critical | Launch gate: zero tolerance; trust level 1 for screenshots |
| Instagram OAuth breaks | High | Keep technical flow as fallback |
| WhatsApp never unblocks | Medium | Position as Instagram-first; waitlist keeps demand |
| Demo video quality | Medium | Two recording sessions; script read aloud |

---

## Standing Definition of Done

- Branch `feat/…`, one concern, Conventional Commit, PR into `main`
- `ruff check . && ruff format --check .` pass
- `pytest -q -m "not live"` passes
- New env names in `.env.example` only
- No secrets, real phone numbers, or real receipts
- User-visible work saves a clip under `demo/clips/`

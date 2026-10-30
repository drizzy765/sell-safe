# Implementation Plan: Sell-Safe

## Overview

Sell-Safe is a **payment safety layer** for Nigerian small sellers on Instagram and WhatsApp. It verifies transfer screenshots against real bank evidence before goods leave the shop. The LLM phrases replies; it never sets a payment verdict. The verdict engine does.

**Current status:** Oct 30, 2026. Phases 1-3 complete (foundation, LLM, buyer chat). WhatsApp locked (error 131031). Instagram working. 155/156 tests passing.

**Deadline:** Nov 5, 02:00 WAT (hard stop). Feature freeze: Nov 2, 23:59 WAT.

**Belief:** We can finish everything before the deadline. Nothing is cut.

---

## Changes from Previous Plan

| Aspect | Before | Now |
|---|---|---|
| **Primary channel** | WhatsApp-first | Instagram-first (WhatsApp locked) |
| **Onboarding** | 7 technical Meta steps | One "Connect Instagram" button + sample reply demo first |
| **WhatsApp** | Full setup guide | "Coming Soon" waitlist with phone number capture |
| **Core feature** | Same priority | **P0:** Payment verification must be flawless |
| **Other features** | Many marked CUT | **All restored** — nothing cut, build if time permits |
| **Value demonstration** | After setup | Before setup — sample reply + safety demo |

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
                         ├── evidence matching → verdict
                         └── fraud signals (R6) → blocklist

web/ onboarding (P1-P4)
    ├── WhatsApp waitlist (phone number capture)
    ├── Simplified Instagram connect (one button)
    ├── Sample reply demo (prove value first)
    ├── Payment safety demo (fake vs real)
    └── Chat onboarding (stretch)

ops/ (P5, if time)
    ├── Voice transcription (Intron STT)
    ├── Fraud memory (cross-seller blocklist)
    ├── Payment reminders
    └── Daily summary
```

---

## Priority Order (Nothing Cut)

### P0: Payment Verification (Tasks 15-20) — MUST COMPLETE FIRST
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

**Timeline:** Oct 30-31 (2 days)

---

### P1: WhatsApp Waitlist

| Component | Description |
|---|---|
| UI | "WhatsApp coming soon — get notified" card with phone input |
| Backend | `POST /api/waitlist` stores `{whatsapp_number, created_at}` |
| Future | `POST /api/waitlist/notify` sends WhatsApp message with connect link (stub) |

**Why WhatsApp number, not email:** Nigerian sellers live on WhatsApp.

**Timeline:** Nov 1 (1 day)

---

### P2: Simplified Instagram Connect

| Current (Overwhelming) | New (Simple) |
|---|---|
| 7 technical steps with Meta app IDs | One "Connect Instagram" button |
| Webhook URL, verify token, permissions | OAuth flow handles it |
| Code blocks to copy | Automatic configuration |

**Technical steps hidden behind:** "Advanced setup (for developers)" link

**Timeline:** Nov 1 (1 day, parallel with P1)

---

### P3: Sample Reply Demo

| Flow | Description |
|---|---|
| Step 1 | Seller connects Instagram, Sell-Safe reads one product |
| Step 2 | Mock customer asks: "How much for the [product name]?" |
| Step 3 | LLM generates reply using seller's actual product |
| Step 4 | Seller sees: "This is how Sell-Safe would reply" |

**Timeline:** Nov 1 (1 day, parallel with P1-P2)

---

### P4: Payment Safety Demo

| Screen | Content |
|---|---|
| Left side | Fake transfer screenshot (edited amount) |
| Right side | Real bank alert from Paystack |
| Verdicts | SUSPICIOUS vs CONFIRMED |

**Timeline:** Nov 1 (1 day, parallel with P1-P3)

---

### P5: All Remaining Features (Nothing Cut)

**If P0-P4 solid by Nov 1, build everything:**

| Task | Feature | Timeline |
|---|---|---|
| 21 | Bank alert parser | Nov 2 morning |
| 22 | Jev tamper scores | Nov 2 morning |
| 23 | Human-in-the-loop | Nov 2 afternoon |
| 24 | Eval runner | Nov 2 afternoon |
| 25 | Demo storyboard | Nov 2 evening |
| 27 | Voice transcription | Nov 3 morning |
| 28 | Fraud memory | Nov 3 afternoon |
| 29 | Reminders + daily summary | Nov 3 afternoon |
| 30 | Onboarding polish | Nov 4 morning |
| 32 | Web finish (status, FAQ) | Nov 4 morning |
| 34 | Direct Base USDC (replaces RefPay) | Nov 4 if time |

**Timeline:** Nov 2-4 (3 days)

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

### Phase 5: Onboarding Improvements (Nov 1) — P1-P4

**P1: WhatsApp Waitlist**
- [ ] Task WA-1: Waitlist schema
- [ ] Task WA-2: Waitlist UI component
- [ ] Task WA-3: Waitlist API endpoint
- [ ] Task WA-4: Future notification endpoint (stub)

**P2: Simplified Instagram**
- [ ] Task IG-1: Replace 7-step guide with one-click OAuth
- [ ] Task IG-2: Hide technical steps behind "Advanced setup"

**P3: Sample Reply Demo**
- [ ] Task DEMO-1: Mock customer message generator
- [ ] Task DEMO-2: Live reply preview
- [ ] Task DEMO-3: Demo state management

**P4: Payment Safety Demo**
- [ ] Task SAFE-1: Fake screenshot fixture
- [ ] Task SAFE-2: Demo UI component
- [ ] Task SAFE-3: Demo verdict endpoint

**Checkpoint:**
- [ ] WhatsApp waitlist captures phone numbers
- [ ] Instagram connect is one click
- [ ] Sample reply demo shows value
- [ ] Payment safety demo builds trust

---

### Phase 6: Verification V2 (Nov 2) — P5

- [ ] Task 21: Forwarded bank-alert parser
- [ ] Task 22: Jev tamper and match scores
- [ ] Task 23: Seller verdict card + human-in-the-loop
- [ ] Task 24: Eval runner and synthetic set v1

**Checkpoint:**
- [ ] Bank alerts parse correctly
- [ ] Jev scores integrated
- [ ] Human-in-the-loop for mid-confidence
- [ ] Eval runner passes synthetic set

---

### Phase 7: Fraud + Ops (Nov 2-3) — P5

- [ ] Task 28: Scammer memory (fraud signals)
- [ ] Task 29: Payment reminders and daily summary

**Checkpoint:**
- [ ] Fraud signals block repeat scammers
- [ ] Daily summary calculates ₦ saved

---

### Phase 8: Voice + Channels (Nov 3) — P5

- [ ] Task 27: Voice-note transcription (Intron STT)

**Checkpoint:**
- [ ] Voice notes transcribed (yo, pcm, en)
- [ ] Order flow works with voice

---

### Phase 9: Freeze and Demo (Nov 2-4)

- [ ] Task 25: Demo storyboard draft
- [ ] Task 30: Onboarding site polish
- [ ] Task 31: Rough demo recording
- [ ] Task 32: Status, FAQ, privacy pages
- [ ] Task 33: Deploy and tag v0.1-demo
- [ ] Task 35: Seed demo data
- [ ] Task 36: Final video
- [ ] Task 37: README, screenshots, pre-submit
- [ ] Task 38: Submit and tag v1.0-submission

**Checkpoint:**
- [ ] Feature freeze at 23:59 WAT Nov 2
- [ ] Tag v0.1-demo
- [ ] Video ≤3 minutes
- [ ] Submitted by 18:00 WAT Nov 4

---

### Phase 10: Stretch (Nov 4, if time) — P5

- [x] Task 34: Direct Base USDC verification (RefPay removed)

---

## Design Principles

1. **Hide all technical complexity.** No visible Meta app IDs, webhook URLs, verify tokens.
2. **Feel like a helpful assistant, not a form.** Conversational, warm.
3. **Prove value before asking for work.** Sample reply demo first.
4. **Never sound like surveillance.** Frame as "organizing," not "watching."
5. **WhatsApp number, not email.** Meet sellers where they are.
6. **"Do this later" on every step.** Partial setup is better than abandoned setup.

---

## Nothing Gets Cut

| Feature | Status |
|---|---|
| Payment verification | P0 — must complete |
| WhatsApp waitlist | P1 — build |
| Simplified Instagram | P2 — build |
| Sample reply demo | P3 — build |
| Payment safety demo | P4 — build |
| Bank alert parser | P5 — build if P0-P4 solid |
| Jev tamper scores | P5 — build if P0-P4 solid |
| Human-in-the-loop | P5 — build if P0-P4 solid |
| Eval runner | P5 — build if P0-P4 solid |
| Voice transcription | P5 — build if P0-P4 solid |
| Fraud memory | P5 — build if P0-P4 solid |
| Reminders + summary | P5 — build if P0-P4 solid |
| Demo video | Required — build |
| Deploy + submit | Required — build |

---

## Schedule Summary

| Day | Focus | Tasks |
|---|---|---|
| **Oct 30** | Payment verification | Tasks 15-16 |
| **Oct 31** | Payment verification | Tasks 17-20 |
| **Nov 1** | Onboarding | Tasks WA, IG, DEMO, SAFE (P1-P4) |
| **Nov 2** | Verification V2 + Freeze | Tasks 21-25, freeze at 23:59 |
| **Nov 3** | Voice + Ops + Video | Tasks 27-29, 31, 35-36 |
| **Nov 4** | Submit | Tasks 30, 32-33, 37-38 |

**Total:** 6 days, ~38 tasks, ~6 tasks per day.

**Belief:** We can do this.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Payment verification doesn't catch fakes | Critical | Screenshot trust level 1; eval gate zero tolerance |
| Instagram OAuth breaks | High | Keep technical flow as fallback |
| WhatsApp never unblocks | Medium | Position as Instagram-first; waitlist captures demand |
| Voice transcription fails | Low | Skip if broken; not core feature |
| Running out of time | Medium | Prioritize P0-P4; P5 is bonus |
| Demo video quality poor | Medium | Two recording sessions; script ready |

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

**Nothing is cut. Everything is possible. We have 6 days. Let's build.**

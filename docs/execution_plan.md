# Execution Plan (Oct 30 – Nov 4, 2026)

**Deadline:** Nov 5, 02:00 WAT (hard stop). Internal target: submitted by Nov 4, 18:00 WAT.
**Feature freeze:** Nov 2, 23:59 WAT. Nov 3: video recording. Nov 4: submission.

**Current status:** Oct 30, 2026. Phases 1-3 complete (foundation, LLM, buyer chat). WhatsApp locked (error 131031). Instagram working. 155/156 tests passing.

**Team confidence:** We can finish everything before the deadline.

---

## Changes from Previous Plan

**Revised approach:** Nothing is cut. All features are back on the table.

| Aspect | Before | Now |
|---|---|---|
| **Primary channel** | WhatsApp-first | Instagram-first (WhatsApp locked, waitlist active) |
| **Onboarding** | 7 technical Meta steps | One "Connect Instagram" button + sample reply demo first |
| **WhatsApp** | Full setup guide | "Coming Soon" waitlist with phone number capture |
| **Payment verification** | Same priority | **P0:** Elevated to critical path — must be flawless |
| **Other features** | Many marked CUT | **All restored** — P5/stretch, build if time permits |
| **Value demonstration** | After setup | Before setup — sample reply + safety demo |

---

## Priority Order (Nothing Cut)

| Priority | Feature | Why This Priority |
|---|---|---|
| **P0** | Payment verification (Tasks 15-20): fake screenshot → SUSPICIOUS, real Paystack webhook → CONFIRMED | Core product promise; hackathon judges will test this first |
| **P1** | WhatsApp "Coming Soon" waitlist: collect WhatsApp numbers, notify on unblock | Capture demand; future growth channel |
| **P2** | Simplified Instagram connect: one button, hide technical steps | Reduce friction; current 7-step process is overwhelming |
| **P3** | Sample reply demo: show LLM-generated reply to mock customer question | Prove value before seller does any work |
| **P4** | Payment safety demo: fake vs real screenshot comparison | Build trust; show the problem Sell-Safe solves |
| **P5** | **Stretch — build if P0-P4 solid:** All remaining features | Complete product vision |

**P5 Features (All Restored):**
- Bank alert parser (Task 21)
- Jev tamper and match scores (Task 22)
- Seller verdict card + human-in-the-loop (Task 23)
- Eval runner and synthetic set (Task 24)
- Demo storyboard draft (Task 25)
- Instagram adapter (✅ already done)
- Voice-note transcription (Task 27)
- Scammer memory / fraud signals (Task 28)
- Payment reminders and daily summary (Task 29)
- Onboarding site polish (Task 30 — partially done)
- Fraud signals, reminders, daily summary (Tasks 28-29)
- Web finish, status, FAQ (Task 32)
- Stretch: Direct Base USDC (Task 34; RefPay removed). Messenger only if time remains.

---

## Detailed Schedule

### Thu Oct 30 – Fri Oct 31: Payment Verification (P0) — 2 Days

| Day | Tasks |
|---|---|
| **Oct 30** | Task 15: Receipt extraction, Task 16: Rules R1–R9 |
| **Oct 31** | Task 17: Verdict engine, Task 18: Paystack webhook, Task 19: Screenshot→verdict, Task 20: Flutterwave webhook |

**Deliverable:**
- [ ] Test transfer → CONFIRMED with `release_allowed=true`
- [ ] Edited screenshot → SUSPICIOUS, release blocked (409)
- [ ] Every verdict-table row has unit test
- [ ] No screenshot-only CONFIRMED paths

---

### Sat Nov 1: Onboarding Improvements (P1-P4) — 1 Day

| Time | Tasks |
|---|---|
| Morning | P1: WhatsApp waitlist (schema, UI, API) |
| Afternoon | P2: Simplified Instagram connect (one button, hide steps) |
| Evening | P3: Sample reply demo + P4: Payment safety demo |

**Deliverable:**
- [ ] Seller can enter WhatsApp number on waitlist
- [ ] Instagram connect is one click
- [ ] Sample reply demo shows value immediately
- [ ] Payment safety demo builds trust

---

### Sun Nov 2: Verification V2 + Ops + Freeze — 1 Day

| Time | Tasks |
|---|---|
| Morning | Task 21: Bank alert parser, Task 22: Jev tamper scores |
| Afternoon | Task 23: Human-in-the-loop, Task 24: Eval runner |
| Evening | Feature freeze, tag `v0.1-demo` |

**Deliverable:**
- [ ] Bank alerts parse (GTB, Access, OPay formats)
- [ ] Jev scores integrated into confidence
- [ ] Human-in-the-loop for mid-band confidence
- [ ] Eval runner with synthetic set
- [ ] Tag `v0.1-demo`

---

### Mon Nov 3 – early Nov 4: Remaining polish (no video yet)

Product P0–P7 and crypto are largely in tree. Use this window for deploy/README polish and any leftover web work. **Do not record the demo video yet.**

---

### Remaining path to submit (locked order — Oct 31)

**Hard rule:** Demo video is **last** before Indie submit. Website redesign ships before video. Full SellSafe-Bench is optional for Meta submit.

| Order | Work | Rule |
|---|---|---|
| **1** | Website redesign (`docs/design/website-design-plan.md` T1–T14) | Required before deadline if time allows; prioritize T1–T11 landing |
| **2** | SellSafe-Bench (`docs/benchmark.md`) | Best-effort. Partial OK. Do **not** block redesign or video. If short on time, skip full bench for Meta; keep `evals/report.md` headlines |
| **3** | Deploy + tag `v0.1-demo` + README / pre-submit checks | Before or interleaved with #2; must be ready before video |
| **4** | Demo video (record → edit → unlisted link) | **Last** creative deliverable |
| **5** | Submit + tag `v1.0-submission` | After video link works logged-out |

**Deliverable before submit:**
- [ ] Redesigned site live (or best shippable slice of T1–T11)
- [ ] Measured numbers only in write-up (full bench optional)
- [ ] Deployed URL + `v0.1-demo`
- [ ] Demo video ≤3 min, link in `docs/hackathon_launch.md`
- [ ] Submitted by Nov 4, 18:00 WAT target

---

## Stretch Slot (If Ahead of Schedule)

- Full SellSafe-Bench (tiers, charts, kappa) if #1 and deploy are solid
- Messenger adapter only if time remains after video
- Task 34 Base USDC already done

---

## Design Principles

1. **Hide all technical complexity.** No visible Meta app IDs, webhook URLs, verify tokens.
2. **Feel like a helpful assistant, not a form.** Conversational, warm.
3. **Prove value before asking for work.** Sample reply demo first.
4. **Never sound like surveillance.** Frame as "organizing," not "watching."
5. **WhatsApp number, not email.** Meet sellers where they are.
6. **"Do this later" on every step.** Partial setup is fine.

---

## What We Believed vs What Happened

| Belief | Reality |
|---|---|
| Need to cut features to hit deadline | **We can build everything** — 6 days is enough |
| WhatsApp will be primary | **Instagram is live**, WhatsApp is waitlist |
| Technical onboarding is required | **Simplified flow** with one-click connect |
| Sellers need forms | **Chat-style** with demos proves value first |

---

## Risks (And Mitigations)

| Risk | Impact | Mitigation |
|---|---|---|
| Payment verification doesn't catch fakes | Critical | Screenshot trust level stays 1; eval gate at zero false CONFIRMED |
| Instagram OAuth breaks | High | Keep technical flow as fallback behind "Advanced" link |
| WhatsApp never unblocks | Medium | Position as Instagram-first; waitlist captures demand |
| Voice transcription fails | Low | Cut TTS, keep STT only; or skip if broken |
| Eval runner fails on synthetic set | Medium | Manual verification of key cases |
| Demo video quality poor | Medium | Two recording sessions; script read aloud |

---

## Daily Definition of Done

- [ ] Code on `main` via PR, CI green, no secrets in diff
- [ ] Feature demonstrable end-to-end on Instagram
- [ ] `CHANGELOG` line + one screenshot/clip saved to `demo/clips/`

---

## Final Note

Foundation and P0–P7 are largely done. Path to deadline:

1. **Website redesign** (plan → ship landing first)
2. **Benchmark** (best-effort / partial OK; full bench not required to submit Sell-Safe)
3. **Deploy + README**
4. **Demo video last**
5. **Submit**

Website redesign and demo video both land before the deadline. Full SellSafe-Bench does not block submit.

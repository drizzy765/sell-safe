# Execution Plan (Oct 30 – Nov 4, 2026)

**Deadline:** Nov 5, 02:00 WAT (hard stop). Internal target: submitted by Nov 4, 18:00 WAT.
**Feature freeze:** Nov 2, 23:59 WAT. Nov 3: benchmark day + video recording. Nov 4: submission.

**Current status:** Backend foundation complete (Phases 1-3). 155/156 tests passing. WhatsApp locked (error 131031). Instagram working.

---

## Changes from Previous Plan

**Shifted priorities based on user feedback:**
1. **Payment verification is now P0** — the core differentiator that must work flawlessly
2. **Onboarding redesigned** — hide all technical Meta steps, lead with value, not forms
3. **WhatsApp status clarified** — blocked by Meta business verification; pivot to waitlist
4. **User experience principles added** — helpful assistant, not surveillance; prove value before asking for work

---

## New Priority Order

| Priority | Feature | Why First |
|---|---|---|
| **P0** | Payment verification (fake screenshot → SUSPICIOUS, real webhook → CONFIRMED) | Core promise of the product; hackathon judges will test this |
| **P1** | WhatsApp "Coming Soon" waitlist (collect WhatsApp number, notify on launch) | Capture demand; notify via WhatsApp when unblocked |
| **P2** | Simplified Instagram connect (one button, hide technical steps) | Reduce friction; current 7-step process is overwhelming |
| **P3** | Sample reply demo (show LLM-generated reply to mock customer question) | Prove value before seller does any work |
| **P4** | Payment safety demo (fake vs real screenshot, visual comparison) | Build trust; show the problem Sell-Safe solves |
| **P5** | Stretch only if time: Profile import, chat onboarding, draft catalog from posts | Nice to have; only if P0-P4 are solid |

---

## Revised Schedule

### Thu Oct 30 – Fri Oct 31: Payment Verification (P0)
**Focus:** Tasks 15-20 must be complete and tested.

| Task | Deliverable |
|---|---|
| 15: Receipt extraction | Vision extracts amount, ref, sender, recipient from screenshots |
| 16: Rules R1–R9 | All rules implemented with weights |
| 17: Verdict engine | CONFIRMED/SUSPICIOUS/NOT_FOUND logic, no release without level-3 evidence |
| 18: Paystack webhook | Signature verification, idempotency, level-4 evidence |
| 19: Screenshot → verdict | Full flow: screenshot upload → extraction → rules → verdict |
| 20: Flutterwave webhook | Same evidence path as Paystack |

**DoD:**
- [ ] Test transfer (real Paystack test mode) ends CONFIRMED with `release_allowed=true`
- [ ] Edited screenshot ends SUSPICIOUS or NOT FOUND, release returns 409
- [ ] Every verdict-table row has a unit test
- [ ] Zero path sets CONFIRMED from screenshot alone
- [ ] `pytest -q -m "not live"` passes

---

### Sat Nov 1: WhatsApp Waitlist + Simplified Instagram (P1-P2)

| Task | Deliverable |
|---|---|
| WhatsApp waitlist UI | "Coming soon to WhatsApp" card with phone number input |
| Backend: store waitlist | `POST /api/waitlist` stores WhatsApp numbers |
| Future: notify endpoint | `POST /api/waitlist/notify` sends WhatsApp message with connect link (stub for now) |
| Simplified Instagram | Single "Connect Instagram" button, hide technical Meta steps |
| Update onboarding content | Remove 7-step technical guide, replace with one-click flow |

**DoD:**
- [ ] Seller can enter WhatsApp number on waitlist
- [ ] Seller connects Instagram in one click
- [ ] Technical steps moved to `/docs` or hidden behind "Advanced setup"

---

### Sun Nov 2: Demo Features + Freeze (P3-P4)

| Task | Deliverable |
|---|---|
| Sample reply demo | Mock customer message → LLM generates reply using seller's real product |
| Payment safety demo | Side-by-side: fake screenshot vs real bank alert, SUSPICIOUS vs CONFIRMED |
| Feature freeze | Tag `v0.1-demo`, lock eval datasets |

**DoD:**
- [ ] Seller sees preview: "This is how Sell-Safe would reply to 'How much?'"
- [ ] Demo shows fake receipt flagged, real payment confirmed
- [ ] Deployed URL stable
- [ ] No new features after 23:59 WAT

---

### Mon Nov 3: Demo Recording

| Task | Deliverable |
|---|---|
| Seed demo data | Tolu's Bags, products, buyers, one scammer scenario |
| Record video | Two takes, edit, captions, ≤3 minutes |

**Scenes:**
1. **Hook:** Seller sends product photo → catalog item created
2. **Order:** Buyer asks price in Pidgin → order created
3. **Fake caught:** Edited screenshot → SUSPICIOUS, goods held
4. **Real confirmed:** Paystack webhook → CONFIRMED, goods released

**DoD:**
- [ ] Video ≤3 minutes
- [ ] Logged-out browser can view
- [ ] No real account numbers or customer data visible

---

### Tue Nov 4: Submit

| Task | Deliverable |
|---|---|
| README | Pitch, setup, architecture, screenshots |
| Final tests | `pytest`, evals, gitleaks green |
| Submit | Tag `v1.0-submission`, confirmation saved |

---

## Stretch Items (Only if P0-P4 Are Green)

| Priority | Feature | Notes |
|---|---|---|
| P5 | Draft catalog from Instagram posts | Opt-in only; recent public posts; approve/edit/skip UI |
| P5 | Chat-style onboarding | Pre-fill from profile; ask policies one at a time; "Do this later" on every step |
| P5 | Voice transcription | Intron STT for buyer voice notes |
| P5 | Fraud memory | `/fake` command, cross-seller blocklist |

---

## Cut List (If Behind Schedule)

**Cut from top:**
1. ~~Draft catalog from Instagram posts~~ (stretch only)
2. ~~Chat-style onboarding~~ (keep simple button flow)
3. ~~Voice transcription~~ (cut entirely for this release)
4. ~~Fraud memory~~ (cut entirely for this release)
5. ~~Daily summary~~ (cut entirely)
6. ~~Payment reminders~~ (cut entirely)
7. ~~Messenger adapter~~ (cut entirely)
8. ~~Web onboarding beyond one page~~ (keep single CTA page)

**Never cut:**
- Payment verification (screenshot → SUSPICIOUS, webhook → CONFIRMED)
- Sample reply demo (proves value)
- Payment safety demo (builds trust)
- Simplified Instagram connect
- Demo video

---

## Design Principles (New)

1. **Hide all technical complexity.** Meta app IDs, webhook URLs, verify tokens — invisible to sellers.
2. **Feel like a helpful assistant, not a form.** Chat-style, conversational, warm.
3. **Prove value before asking for work.** Show sample reply before asking for business details.
4. **Never sound like surveillance.** "Here's a catalog draft from your public posts" — not "I watched your last 20 posts."
5. **WhatsApp number, not email.** Nigerian sellers live on WhatsApp.
6. **"Do this later" on every step.** Sellers can start selling with partial info.

---

## Risks

| Risk | Mitigation |
|---|---|
| Payment verification doesn't catch fake screenshots | Zero false-CONFIRMED launch gate; screenshot trust level stays 1 |
| Instagram connect breaks with simplified flow | Keep full technical flow behind "Advanced" link |
| WhatsApp never unblocks | Waitlist keeps demand warm; pivot to Instagram-first positioning |
| Demo video quality poor | Storyboard complete by Oct 30; two recording sessions |

---

## Daily Definition of Done

- [ ] Code on `main` via PR, CI green, no secrets in diff
- [ ] Feature demonstrable end-to-end on Instagram test account
- [ ] `CHANGELOG` line + one screenshot/clip saved to `demo/clips/`

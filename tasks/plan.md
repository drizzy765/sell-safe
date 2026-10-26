# Implementation Plan: Sell-Safe

## Overview

Sell-Safe is a WhatsApp-first shop assistant for Nigerian small sellers. A seller snaps a product photo and Muse vision writes the listing. Exact Muse model ids are **TODO verify**. Groq is only a temporary fallback. Voice notes use Intron Sahara. Buyers ask prices and place orders in English, Pidgin, or Yoruba. Before goods leave the shop, a deterministic verification engine checks transfer screenshots against bank evidence (Paystack webhook, forwarded alert) and returns CONFIRMED, NOT FOUND, SUSPICIOUS, or UNVERIFIED. The LLM phrases replies. It never sets a payment verdict.

Deadline: submit by **4 Nov 2026, 18:00 WAT** (hard stop 4 Nov 21:00 ET / 5 Nov 02:00 WAT). Feature freeze: **2 Nov, 23:59 WAT**. Today is 26 Oct. The repo is docs and empty folders. No application code yet.

This plan follows `docs/execution_plan.md` and the specs in `docs/`. Tasks and acceptance criteria live in `tasks/todo.md`.

## Architecture decisions

- **Code lives in the folders that already exist.** API under `backend/app/`. Onboarding site under `web/`. `docs/architecture.md` still shows a root `app/` and a `dashboard/` folder. Implement against `backend/` and `web/`, then update that doc when behaviour is real.
- **Jev client lives in `backend/app/decisions/`.** That folder's README owns the TypeSafe client and question specs. Docs that say `app/jev/` mean this package.
- **One brain, channel adapters at the edge.** WhatsApp, Instagram, and Messenger normalize to `InboundMessage`, then share the graph in `backend/app/agent/graph/`.
- **`LLMProvider` is the only LLM entry.** Hackathon target is Meta Muse (`LLM_PROVIDER=meta`): Muse Spark for text and tools, Muse vision for images. Exact ids are **TODO verify**. Groq (`LLM_PROVIDER=groq`) is a temporary dev fallback behind the same protocol. Speech is Intron Sahara, not the LLM provider.
- **Verdicts come only from `backend/app/verification/`.** Evidence trust level, rules R1–R9, and Jev probabilities feed `verdict.py`. Tools may read a verdict. They may not invent one. A screenshot alone never sets `release_allowed`.
- **Money is integer kobo. Times are UTC `timestamptz`, shown in WAT.** User-facing amounts, account details, and verdicts use fixed templates.
- **Webhooks:** verify the signature on the raw body, dedupe, return 200 quickly, process asynchronously.
- **Hosted APIs only.** No local weights, no torch. Synthetic receipts only in git; real-derived images stay in `evals/data/private/` (gitignored).
- **Requirements at the repo root** so CI matches `docs/github_rules.md`. Pytest uses `pythonpath = backend`.

## Dependency graph

```
settings + /health + CI
        │
        ├── SQL schema
        │       │
        │       ├── repos (sellers, products, orders, messages, evidence)
        │       │
        │       └── webhook dedupe
        │
        ├── WhatsApp adapter ──► verify handshake + echo
        │
        └── LLMProvider (Groq, then Meta)
                │
                ├── vision: photo → catalog item
                │
                ├── Jev route → sales graph → order (awaiting_payment)
                │
                └── vision: receipt extract → rules → verdict
                        │
                        ├── Paystack webhook (level 4) → CONFIRMED
                        ├── bank alert (level 2) → seller decides
                        ├── fraud_signals, reminders, daily summary
                        └── Instagram adapter + voice transcription

web/ onboarding (after a public webhook URL exists)
demo seed → video → submission
```

Build bottom-up through Phase 4. After the WhatsApp order-and-verdict path works, Instagram, voice, fraud memory, jobs, and the website can overlap.

## Task list

### Phase 1: Foundation (Sun 26 Oct)
- [ ] Task 1: App skeleton, settings, `/health`
- [ ] Task 2: `.gitignore` and CI
- [ ] Task 3: Supabase schema migration
- [ ] Task 4: WhatsApp channel adapter
- [ ] Task 5: Meta verify handshake and echo bot

### Checkpoint: Foundation
- [ ] `ruff` and `pytest -q -m "not live"` pass
- [ ] GET webhook verify returns the challenge
- [ ] A test WhatsApp text gets an echo
- [ ] Human review before Phase 2

### Phase 2: LLM and catalog (Mon 27 Oct)
- [ ] Task 6: `LLMProvider`, Groq chat, `FakeProvider`
- [ ] Task 7: Meta provider behind env
- [ ] Task 8: Catalog vision extraction
- [ ] Task 9: Photo to saved product with seller-confirmed price

### Checkpoint: Catalog
- [ ] Seller photo becomes a product row and a chat confirmation
- [ ] Tests use `FakeProvider`; no live LLM in CI

### Phase 3: Buyer chat and orders (Tue 28 Oct)
- [ ] Task 10: Jev client and routing questions
- [ ] Task 11: State graph observe, route, respond
- [ ] Task 12: Catalog and order tools
- [ ] Task 13: Language prompts, money templates, reply check
- [ ] Task 14: Price question and order on WhatsApp

### Checkpoint: Orders
- [ ] Pidgin price question and "I go take 1" create an `awaiting_payment` order
- [ ] Prices in the reply match the database

### Phase 4: Verification v1 (Wed 29 Oct)
- [ ] Task 15: Receipt extraction and image hashes
- [ ] Task 16: Rules R1–R9
- [ ] Task 17: Verdict engine
- [ ] Task 18: Paystack test virtual account and webhook
- [ ] Task 19: Screenshot and webhook paths to a verdict
- [ ] Task 20: Flutterwave webhook on the same evidence path

### Checkpoint: Verification v1
- [ ] Test transfer ends CONFIRMED with `release_allowed`
- [ ] Edited or unmatched screenshot ends SUSPICIOUS or NOT FOUND and release returns 409
- [ ] Every verdict-table row has a unit test
- [ ] Zero path sets CONFIRMED from a screenshot alone

### Phase 5: Verification v2 and evals (Thu 30 Oct)
- [ ] Task 21: Forwarded bank-alert parser
- [ ] Task 22: Jev tamper and match scores inside confidence
- [ ] Task 23: Seller verdict card, human-in-the-loop, recheck window
- [ ] Task 24: Eval runner and synthetic set v1
- [ ] Task 25: Demo storyboard draft (human)

### Checkpoint: Verification v2
- [ ] `python -m evals.run --provider groq` writes `evals/report.md`
- [ ] False CONFIRMED on the fake set is 0
- [ ] Storyboard matches `docs/hackathon_launch.md`

### Phase 6: Instagram and voice (Fri 31 Oct)
- [ ] Task 26: Instagram adapter on the same graph
- [ ] Task 27: Voice-note transcription

### Checkpoint: Channels
- [ ] The order flow completes in an Instagram DM
- [ ] A voice note becomes text and can place an order
- [ ] If WhatsApp core is still shaky, skip this phase (cut list item 6)

### Phase 7: Fraud memory, jobs, web start (Sat 1 Nov)
- [ ] Task 28: Scammer memory
- [ ] Task 29: Payment reminders and daily summary
- [ ] Task 30: Onboarding site shell and platform steps
- [ ] Task 31: Rough demo recording (human)

### Checkpoint: Ops
- [ ] A confirmed fraud signal flags a second seller
- [ ] Daily summary message includes naira saved
- [ ] `/` renders WhatsApp, Instagram, and Messenger steps

### Phase 8: Web finish, deploy, freeze (Sun 2 Nov)
- [ ] Task 32: Status, FAQ, privacy, accessibility, mobile
- [ ] Task 33: Deploy API and site; tag `v0.1-demo`
- [ ] Task 34: One stretch only — Messenger adapter or RefPay USDC testnet

### Checkpoint: Feature freeze (23:59 WAT)
- [ ] Deployed URL stays up
- [ ] Core path still works on the WhatsApp test number
- [ ] No new features after the tag

### Phase 9: Demo (Mon 3 Nov)
- [ ] Task 35: Seed demo data
- [ ] Task 36: Final video, two takes (human)

### Checkpoint: Video
- [ ] Unlisted video is ≤ 3 minutes and opens logged out

### Phase 10: Submit (Tue 4 Nov)
- [ ] Task 37: README, screenshots, pre-submit tests
- [ ] Task 38: Submit and tag `v1.0-submission` (human)

### Checkpoint: Submitted
- [ ] Submitted by 18:00 WAT
- [ ] Confirmation saved
- [ ] `pytest`, evals, and gitleaks are green

## What never gets cut

Photo to catalog, buyer order, Paystack webhook confirmation, screenshot verdict, demo video.

## Cut from the top if a day slips

1. Mono sandbox (do not schedule)
2. Messenger adapter (only the Phase 8 stretch slot)
3. Next.js seller dashboard (do not schedule; the daily summary replaces it)
4. Web onboarding reduced to one static WhatsApp page
5. Crypto / RefPay
6. Voice replies (keep transcription)
7. Instagram, only if WhatsApp is not solid by 31 Oct

## Parallel work

Safe after Phase 4: eval fixtures, bank-alert parser, and the web shell. Instagram and voice are independent of each other once the graph exists. Schema migrations and the shared webhook contract stay sequential.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Meta card restricted or credits late | High | Groq behind `LLMProvider`; switch with `LLM_PROVIDER` |
| WhatsApp test number can only message registered recipients | High | Register demo phones on day 1 |
| Instagram Business and Page linking is slow | Med | Start Meta app setup on day 1, before Task 26 |
| False CONFIRMED on a fake receipt | High | Launch gate in Task 24; screenshot trust level is 1 |
| Paystack dedicated virtual accounts unavailable in test mode | High | Confirm against current Paystack docs before Task 18; Flutterwave is the backup evidence path |
| Jev or Meta request schema differs from the docs | Med | Verify official docs before coding Tasks 7, 10, and 22; fake the client in unit tests |
| Yoruba copy is wrong | Med | Native-speaker review of templates before the video |
| Weak laptop | Med | Hosted APIs and Supabase cloud only |
| Video quality | Med | Storyboard on 30 Oct, rough cut 1 Nov, two final takes 3 Nov |

## Open questions

- Meta Model API base URL, vision, and tool-calling: confirm on dev.meta.ai before production uses `LLM_PROVIDER=meta`.
- Jev `POST https://api.typesafe.ai/v1/systemone` body: confirm on docs.typesafe.ai before Task 10.
- Paystack dedicated virtual account event names in test mode: confirm before Task 18.
- Hackathon submission form (Devpost vs Cerebral Valley) and whether a live URL is required: confirm before Task 38.
- Yoruba templates need a native speaker. Who reviews them, and by which day?
- Platform icons on the website: confirm Meta brand rules before shipping logos.

## Standing definition of done (every code task)

- Branch `feat/…`, one concern, Conventional Commit, PR into `main`.
- `ruff check .` and `ruff format --check .` pass. `pytest -q -m "not live"` passes.
- New env names go in `.env.example` only. No secrets, real phone numbers, or real receipts.
- Docs updated when behaviour changes. User-visible work saves a clip under `demo/clips/` and a `CHANGELOG` line.

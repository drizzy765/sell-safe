# Sell-Safe 🛡️

**Payment safety layer for Nigerian small sellers on Instagram and WhatsApp.** Verifies transfer screenshots against real bank evidence before goods leave the shop. Speaks Yoruba, Pidgin and English.

Built by Agoro Oluwatimilehin (GitHub: drizzy765) for the Meta Global AI Developer Hackathon (Indie track).

## Try it now

- **Live app:** https://sell-safe-three.vercel.app
- **Judge sandbox (no login):** chat as a buyer and send a fake receipt — https://sell-safe-three.vercel.app/#sandbox
- **Demo seller dashboard:** https://sell-safe-three.vercel.app/dashboard?demo=1
- **Interactive benchmark charts:** https://sell-safe-three.vercel.app/benchmark
- **Muse benchmark write-up:** [docs/benchmark_muse.md](docs/benchmark_muse.md)

**Headline result:** on the 20-case payment-verification benchmark, Sell-Safe
confirmed **zero** fake receipts ([evals/report.md](evals/report.md)). The LLM
never decides a payment verdict — deterministic rules do.

---

## What Changed (Oct 30, 2026)

**New priorities based on user feedback:**

1. **Payment verification is now P0.** The core promise: fake screenshots get flagged SUSPICIOUS, real Paystack webhooks get CONFIRMED. This must be flawless.

2. **WhatsApp is locked** (Meta business verification blocked, error 131031). **Pivoted to Instagram-first** with a WhatsApp waitlist. When WhatsApp unblocks, we'll notify sellers via WhatsApp with a one-tap connect link.

3. **Simplified onboarding.** Instead of 7 technical Meta setup steps, sellers get one "Connect Instagram" button. Technical complexity hidden.

4. **Prove value first.** New sellers see a sample AI reply to a mock customer question *before* doing any work. Then a payment safety demo showing fake vs real screenshots.

---

## The Problem

Small sellers on WhatsApp and Instagram lose goods to fake transfer screenshots. A "buyer" sends a convincing screenshot — the seller ships the product — the money never arrives.

Sell-Safe catches this by:
1. Reading the screenshot with AI vision
2. Checking against real bank evidence (Paystack webhook or forwarded bank alert)
3. Returning a verdict: **CONFIRMED**, **NOT FOUND**, or **SUSPICIOUS**

The LLM phrases replies. Only the deterministic verification engine sets verdicts.

---

## Features

| Priority | Feature | Status |
|---|---|---|
| **P0** | Payment verification: screenshot → extraction → rules → verdict | In progress (Tasks 15-20) |
| **P0** | Paystack webhook: real bank evidence → CONFIRMED | In progress |
| **P1** | WhatsApp waitlist: collect phone numbers, notify on unblock | Planned (Nov 1) |
| **P2** | Simplified Instagram: one-click connect, hide technical steps | On the Instagram tab |
| **P2** | Seller login: Supabase magic link; shop + Instagram restored after restart | `/login`, dashboard account block |
| **P3** | Sample reply demo: show AI reply before seller does any work | Shown after connect |
| **P4** | Payment safety demo: fake vs real screenshot comparison | Shown after connect |
| **P5** | Photo → catalog item | ✅ Complete |
| **P5** | Buyer chat: prices, orders, Yoruba/Pidgin/English | ✅ Complete |
| **P0** | USDC on Base: paste tx hash → on-chain verify (no RefPay) | In tree (Base Sepolia default) |
| **Stretch** | Profile import from Instagram posts (opt-in) | If time |
| **Stretch** | Chat-style onboarding | If time |
| **Stretch** | Messenger adapter | If time |

---

## How It Works

### For Sellers

1. **Connect Instagram** — one button, no technical setup
2. **See sample reply** — Sell-Safe shows how it would answer "How much?"
3. **Watch safety demo** — fake screenshot caught, real payment confirmed
4. **Start selling** — catalog, orders, payment verification all automated

### For Buyers

1. DM the shop on Instagram (WhatsApp coming soon)
2. Ask prices in English, Pidgin, or Yoruba
3. Place order, get unique reference (SS-1042)
4. Send transfer screenshot
5. Sell-Safe verifies — CONFIRMED → goods ship, SUSPICIOUS → goods held

---

## Stack

- **Backend:** FastAPI (Python 3.11), Pydantic v2, async architecture
- **LLM:** Meta Muse (Spark for text, vision for images) — Groq fallback
- **Database:** Supabase Postgres with RLS
- **Storage:** Supabase Storage (private buckets)
- **Channels:** Instagram Messaging API (working), WhatsApp Cloud API (blocked, waitlist active)
- **Payments:** Paystack test mode; USDC on Base via direct JSON-RPC (default Base Sepolia). Flutterwave/Mono/RefPay not used.
- **Speech:** Intron Sahara (live; provider transcribe fallback)
- **Frontend:** Next.js on Vercel (onboarding site)
- **Hosting:** Render or Railway (API)

---

## Current Status (Nov 4, 2026) — live

- ✅ Live: backend on Render, web on Vercel, Instagram DMs auto-replied on a real test shop
- ✅ LLM: Meta Muse primary (`muse-spark-1.3`), Groq fallback on any provider failure
- ✅ Catalog: photo → Muse vision extraction → saved product; deterministic browse/prices in English, Pidgin, Yoruba
- ✅ Buyer chat + voice notes: Intron Sahara transcription, pidgin replies, deterministic account-number answers
- ✅ Payment verification: deterministic verdict engine (LLM never confirms payment) — benchmarked 20/20, **zero fake receipts confirmed** ([evals/report.md](evals/report.md), [docs/benchmark_muse.md](docs/benchmark_muse.md))
- ✅ Seller login: Supabase magic link; Instagram connection and shop restored across devices/restarts
- ✅ Dashboard: real inbox, catalog, Analysis tab (chat/customer/verification logs)
- ⏳ WhatsApp: blocked by Meta (131031); waitlist active

**Tests:** 238 passing. `pytest -q -m "not live"` green; CI green (ruff + pytest).

---

## Design Principles

1. **Hide all technical complexity.** No Meta app IDs, webhook URLs, or verify tokens visible.
2. **Feel like a helpful assistant, not a form.** Conversational, warm, never bureaucratic.
3. **Prove value before asking for work.** Sample reply demo first.
4. **Never sound like surveillance.** Frame as "organizing your public posts," not "watching you."
5. **WhatsApp number, not email.** Meet Nigerian sellers where they are.
6. **"Do this later" on every step.** Partial setup is better than abandoned setup.

---

## Setup (for Developers)

```bash
git clone https://github.com/drizzy765/sell-safe && cd sell-safe
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env        # fill values locally; NEVER commit .env

# Run migrations in Supabase SQL editor
# backend/app/db/migrations/0001_init.sql
# backend/app/db/migrations/0002_catalog_drafts.sql
# backend/app/db/migrations/0003_traces.sql
# backend/app/db/migrations/0004_evidence_hashes.sql
# backend/app/db/migrations/0005_whatsapp_waitlist.sql
# backend/app/db/migrations/0006_crypto_payments.sql
# backend/app/db/migrations/0007_instagram_sessions.sql
# backend/app/db/migrations/0008_seller_accounts.sql

uvicorn app.main:app --reload --port 8000

# Tests
pytest -q -m "not live"
```

**LLM Provider:**
- `LLM_PROVIDER=groq` — working now
- `LLM_PROVIDER=meta` — when Meta credits available

---

## Docs

- `docs/execution_plan.md` — Revised schedule (P0-P5)
- `docs/architecture.md` — System design
- `docs/payment_verification.md` — Verdict engine spec
- `docs/harness_engineering.md` — Agent loop and state graph
- `docs/data_model.md` — Database schema
- `docs/design.md` — UI/UX tokens
- `docs/meta.md` — WhatsApp blocked, Instagram working
- `tasks/plan.md` — Implementation roadmap
- `tasks/todo.md` — Detailed task list
- `AGENTS.md` — Coding agent instructions
- `.cursor/rules/` — Editor rules

---

## Roadmap

| Date | Milestone |
|---|---|
| Oct 30-31 | **P0–P7 + crypto:** largely in tree (verification, waitlist, demos, voice, fraud, USDC) |
| Nov 1 | **Website redesign** (`docs/design/website-design-plan.md`) |
| Nov 1–3 | **SellSafe-Bench** best-effort (partial OK; full bench optional for Meta) |
| Nov 3–4 | Deploy + `v0.1-demo`, then **demo video last**, then submit by 18:00 WAT |

---

## Never Cut

- Payment verification (screenshot vs webhook)
- Sample reply demo
- Payment safety demo
- Simplified Instagram connect
- WhatsApp waitlist
- Demo video

## Cut If Behind

- Profile import from posts
- Chat-style onboarding
- Voice transcription
- Fraud memory
- Daily summary
- Payment reminders
- Messenger adapter

---

## License

MIT

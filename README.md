# Sell-Safe 🛡️
**WhatsApp-first shop assistant for Nigerian small sellers that catches fake payment alerts before goods leave the shop.** Speaks Yoruba, Pidgin and English. Powered by Meta Muse models on the Meta Model API (Muse Spark for text and tools, Muse vision for images). Exact model ids are **TODO verify**. Groq is a temporary dev fallback behind `LLMProvider`. Voice notes use Intron Sahara.

Built by Agoro Oluwatimilehin (GitHub: drizzy765) with Meta Muse (Muse Spark) for the Meta Global AI Developer Hackathon (Indie track).

## Problem
Small sellers on WhatsApp, Instagram and Facebook lose goods to fake transfer screenshots and forged bank alerts. I was nearly a victim myself: a "buyer" sent a convincing transfer screenshot, and the money never arrived. Sellers also spend hours answering the same "how much?" messages.
> Any industry fraud statistic used in the pitch must be sourced. Mark it `[TODO verify]` until it is.

## Features
| # | Feature | Status |
|---|---|---|
| 1 | Photo → catalog item (Muse vision) | Core |
| 2 | Buyer chat: prices, orders, Yoruba/Pidgin/English | Core |
| 3 | Payment verification: screenshot extraction, tamper checks, evidence matching | Core |
| 4 | Seller verdict: CONFIRMED / NOT FOUND / SUSPICIOUS + confidence + "don't release goods" rule | Core |
| 5 | Paystack/Flutterwave virtual-account webhooks (test mode) | Core |
| 6 | Forwarded bank alert SMS/email parsing | Core |
| 7 | Instagram DM adapter | Should |
| 8 | Voice notes: Intron Sahara STT (Yoruba/Pidgin code-switch) and TTS replies | Should |
| 9 | Scammer memory (shared blocklist) | Should |
| 10 | Order statuses, payment reminders, daily summary ("₦ saved from fakes") | Should |
| 11 | Web onboarding site ("Sell-Safe Connect": pick WhatsApp / Instagram / Messenger, follow numbered steps), see `docs/design.md` | Should (Nov 1–2) |
| 12 | Messenger adapter, Next.js dashboard, Mono sandbox | Stretch |
| 13 | USDC (testnet) via RefPay, confirmed on-chain | Stretch (Nov 2–3) |

## Stack
FastAPI (Python 3.11) · Meta Model API (Muse Spark, Muse vision, Muse Image, SAM 3.1; exact ids **TODO verify**; Groq only as a dev fallback) · Intron Sahara v2.5 for speech · Jev by TypeSafe AI (routing and verdict probabilities) · Supabase Postgres + Storage · WhatsApp Cloud API · Paystack test mode · Render/Railway · ngrok · Next.js on Vercel (optional).

## Repo status
Planning phase: folders and docs only, no code yet. Each folder has a README describing what goes in it.

## Setup (planned)
```bash
git clone https://github.com/drizzy765/sell-safe && cd sell-safe
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill values locally; NEVER commit .env
supabase db push            # or run migrations/*.sql in the Supabase SQL editor
uvicorn app.main:app --reload --port 8000
ngrok http 8000             # set https://<id>.ngrok.app/webhooks/whatsapp in the Meta App dashboard
```
Set `LLM_PROVIDER=groq` until Meta credits appear under Billing → Free credits, then switch to `LLM_PROVIDER=meta`.

## Docs
All in `docs/`: execution_plan, architecture, data_model, agent, harness_engineering, payment_verification, api_spec, testing_and_evals, benchmark, github_rules, hackathon_launch, design (+ web_content/), demo_data. Agent rules: `AGENTS.md`, `.cursor/rules/`. Config: `.env.example`, `.gitignore`.

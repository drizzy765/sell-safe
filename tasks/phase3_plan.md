# Phase 3: Buyer chat and orders

**Target date:** Tue 28 Oct 2026 (one day). Depends on the merged `feat/catalog` PR (Phase 2).

## Objective

A buyer can ask prices and place an order in English, Pidgin, or Yoruba. The agent routes intent and language through Jev, uses catalog/order tools, and replies from fixed templates for money and account details. A created order is `awaiting_payment` with a unique reference. A voice note can be transcribed through Intron Sahara and handled like typed text. Payment verification is explicitly out of scope for this phase.

## What changes for the user

- Buyer texts "How much for the black bag?" in Pidgin or Yoruba → price from the real catalog.
- Buyer says "I go take 1" → order created, status `awaiting_payment`, reply includes order ref and pay-to details.
- Buyer sends a voice note in Yoruba or Pidgin → transcript becomes text, then the same flow.
- Seller commands (`/summary`, `/release SS-1042`) are not wired yet; Phase 4 handles verification and release.

## Tasks

### Task 1: Jev client and routing questions
- TypeSafe client and question specs: `intent`, `language`, `scam_pressure`, `image_kind`.
- One call returns all four scores. Low-confidence language falls back to seller default.
- `image_kind` distinguishes product photo, payment receipt, and other.
- Fake client for unit tests; confirm request schema from docs.typesafe.ai before wiring.

### Task 2: State graph observe → route → respond
- Inbound turn: observe (dedupe, load seller/buyer/open order), route, then a branch.
- Persist trace after route and respond. Cap: 6 graph steps, 3 tool calls per sales turn.
- Over the cap → short fallback + notify seller. Duplicate webhook does not send a second reply.
- State fields match `docs/harness_engineering.md`.

### Task 3: Catalog and order tools
- `search_catalog`, `get_product`, `create_order`, `get_order_status`, `cancel_order`.
- Prices and stock read from DB inside the tool. `create_order` writes `awaiting_payment`, items, `total_kobo`, unique `SS-` ref.
- Seller scope enforced on every call. Order ref format from `data_model.md`.

### Task 4: Language prompts, money templates, reply check
- System prompt + style files `en.md`, `pcm.md`, `yo.md`.
- Amounts, account numbers, verdicts render only through `templates.py`.
- Reply check rejects invented prices, wrong language, and unearned "payment confirmed". One retry, then template fallback.
- Yoruba and Pidgin examples match `docs/agent.md`; mark all for native-speaker review.

### Task 5: Buyer order end-to-end
- Webhook routes `price_question` / `order` / `chit_chat` to the sales agent with tools.
- Integration test: buyer asks price → order → DB rows match goal.
- Manual test on WhatsApp test number in Pidgin and Yoruba.

### Task 6 (stretch): Buyer voice notes via Intron STT
- If time remains, route `audio` messages to Intron Sahara STT (`yo`, `pcm`, `en`), store transcript/language/asr_confidence, then feed the transcript into the same graph.
- TTS replies are **not** in this phase. This is transcription only.
- This is a stretch because Intron credentials and STT URL still need verification.

## Files likely touched

- `backend/app/decisions/` (Jev client)
- `backend/app/agent/graph/state.py`
- `backend/app/agent/graph/nodes.py`
- `backend/app/agent/tools/catalog.py`
- `backend/app/agent/tools/orders.py`
- `backend/app/agent/prompts/en.md`
- `backend/app/agent/prompts/pcm.md`
- `backend/app/agent/prompts/yo.md`
- `backend/app/agent/reply_check.py`
- `backend/app/agent/templates.py` (extend)
- `backend/app/db/repo.py` or order store
- `backend/app/api/webhooks/router.py` (route non-catalog intents)
- `backend/db/migrations/0002_traces.sql` or `0003_orders.sql`
- Tests under `backend/tests/`

## Definition of done

- `ruff check . && ruff format --check .` pass.
- `pytest -q -m "not live"` passes.
- A mocked integration test: buyer asks price in Pidgin → agent returns real price; buyer orders → order row `awaiting_payment` with correct total.
- Manual WhatsApp test: buyer can order in English and at least one of Pidgin/Yoruba.
- No payment verdict logic in this phase; the order stops at `awaiting_payment`.

## Risks / human steps

- TypeSafe API key and request schema must be confirmed before the Jev task is complete.
- Order ref uniqueness may need a Postgres sequence or an application-side generator; decide in code.
- Native-speaker review of Pidgin and Yoruba prompts is required before the demo, not necessarily before this PR.
- Intron STT is stretch; if credentials are not ready, leave audio messages with a "please type" reply.

## Not in this phase

- Payment verification, screenshot verdict, or release endpoint.
- Seller commands `/release`, `/summary`.
- Instagram/Messenger adapters.
- Dashboard, Mono. Crypto is direct Base USDC (no RefPay).

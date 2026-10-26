# Sell-Safe task list

Index and decisions: `tasks/plan.md`. Specs: `docs/`. Implement only after this list is reviewed.

Standing checks for every code task: `ruff check . && ruff format --check .`, `pytest -q -m "not live"`, Conventional Commit, no secrets.

---

## Phase 1: Foundation (Sun 26 Oct)

## Task 1: App skeleton, settings, and health

**Description:** Make the API bootable. Root `requirements.txt` and `requirements-dev.txt` (FastAPI, uvicorn, httpx, pydantic v2, supabase, pytest, ruff). Pydantic settings read env vars already listed in `.env.example`. `backend/app/main.py` exposes `GET /health`.

**Acceptance criteria:**
- [ ] `GET /health` returns `{"status":"ok","provider":"<LLM_PROVIDER>"}` and does not call an LLM
- [ ] Model names and secrets are read from the environment, never hardcoded
- [ ] A unit test covers the health payload

**Verification:**
- [ ] `pytest -q -m "not live" backend/tests/unit/test_health.py`
- [ ] `ruff check . && ruff format --check .`

**Dependencies:** None

**Files likely touched:**
- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/tests/unit/test_health.py`

**Estimated scope:** Medium

## Task 2: Ignore rules and CI

**Description:** Align `.gitignore` with `docs/github_rules.md` and add `.github/workflows/ci.yml` (ruff, pytest excluding live, gitleaks).

**Acceptance criteria:**
- [ ] `.env`, `.venv`, `evals/data/private/`, `demo/raw/`, `__pycache__`, `.next`, and `.vercel` are ignored
- [ ] CI runs `ruff check`, `ruff format --check`, and `pytest -q -m "not live"` on Python 3.11
- [ ] CI runs gitleaks with full git history

**Verification:**
- [ ] Workflow YAML matches the job list in `docs/github_rules.md`
- [ ] A dummy secret in a test file would be covered by gitleaks (do not commit a real key)

**Dependencies:** Task 1

**Files likely touched:**
- `.gitignore`
- `.github/workflows/ci.yml`

**Estimated scope:** Small

## Task 3: Supabase schema migration

**Description:** One SQL migration for every table in `docs/data_model.md`: sellers, products, buyers, orders, payments, payment_evidence, verdicts, fraud_signals, messages, webhook_events, daily_summaries. Integer kobo, UTC timestamptz, phone matching via hash columns.

**Acceptance criteria:**
- [ ] Every table and enum in the data model exists, including order status and evidence type
- [ ] `messages.external_msg_id`, `webhook_events.event_id`, and `orders.ref` are unique
- [ ] `payment_evidence.source_id` is unique per evidence type

**Verification:**
- [ ] Migration applies on a fresh Supabase project (`supabase db push` or SQL editor)
- [ ] A second apply of the same event id is rejected

**Dependencies:** None (can run beside Task 1)

**Files likely touched:**
- `backend/app/db/migrations/0001_init.sql`
- `backend/app/db/README.md`

**Estimated scope:** Medium

## Task 4: WhatsApp channel adapter

**Description:** Implement `ChannelAdapter` for WhatsApp: HMAC-SHA256 signature on the raw body (`X-Hub-Signature-256` and `META_APP_SECRET`), parse text, image, audio, and status payloads into `InboundMessage`, plus `send_text`.

**Acceptance criteria:**
- [ ] Valid signatures pass and mutated bodies fail
- [ ] Fixtures for text, image, audio, and status parse to the normalized message shape
- [ ] `send_text` calls the Graph API version from `GRAPH_API_VERSION` with the phone number id from env

**Verification:**
- [ ] `pytest -q -m "not live" backend/tests/unit/test_whatsapp_adapter.py`
- [ ] No access token appears in logs or assertions

**Dependencies:** Task 1

**Files likely touched:**
- `backend/app/channels/base.py`
- `backend/app/channels/whatsapp/adapter.py`
- `backend/tests/unit/test_whatsapp_adapter.py`
- `backend/tests/fixtures/whatsapp/`

**Estimated scope:** Medium

## Task 5: Meta verify handshake and echo bot

**Description:** `GET /webhooks/meta` echoes `hub.challenge` when `hub.verify_token` matches `META_VERIFY_TOKEN`. `POST /webhooks/whatsapp` verifies the signature, dedupes on message id, returns 200 immediately, and echoes text on a background task. Human step the same day: Meta app, WhatsApp test number, ngrok, and register demo recipient phones.

**Acceptance criteria:**
- [ ] Wrong verify token does not return the challenge
- [ ] Bad signature returns 401 and stores nothing
- [ ] The same `external_msg_id` is processed once and still returns 200

**Verification:**
- [ ] Unit tests for handshake, bad signature, and duplicate id
- [ ] Manual: Meta webhook verify succeeds and a test chat receives the echo

**Dependencies:** Tasks 3, 4

**Files likely touched:**
- `backend/app/api/webhooks/meta.py`
- `backend/app/api/webhooks/whatsapp.py`
- `backend/app/db/repo.py`
- `backend/tests/integration/test_whatsapp_echo.py`

**Estimated scope:** Medium

## Checkpoint: After Tasks 1–5
- [ ] Lint and non-live tests pass
- [ ] Webhook verify succeeds in the Meta dashboard
- [ ] Echo reply arrives on the WhatsApp test number
- [ ] Review with a human before Phase 2

---

## Phase 2: LLM and catalog (Mon 27 Oct)

## Task 6: LLMProvider, Groq chat, and FakeProvider

**Description:** Define `LLMProvider.chat` and `vision`. Groq chat uses the OpenAI-compatible endpoint and model names from env, as a temporary fallback. `FakeProvider` returns canned results for tests. Nothing else imports an LLM SDK. Buyer speech is Intron Sahara (`docs/architecture.md`), not this provider.

**Acceptance criteria:**
- [ ] `chat` can request JSON-schema output and tools
- [ ] Tests call `FakeProvider` only
- [ ] A missing API key fails at provider construction, not with a hardcoded model fallback

**Verification:**
- [ ] `pytest -q -m "not live" backend/tests/unit/test_llm_provider.py`
- [ ] Live Groq call, if run, is marked `@pytest.mark.live`

**Dependencies:** Task 1

**Files likely touched:**
- `backend/app/llm/base.py`
- `backend/app/llm/groq/client.py`
- `backend/app/llm/fake.py`
- `backend/tests/unit/test_llm_provider.py`

**Estimated scope:** Medium

## Task 7: Meta provider behind env

**Description:** `backend/app/llm/meta/` implements the same protocol using `META_API_BASE_URL`, `META_TEXT_MODEL`, and `META_VISION_MODEL`. Confirm the official request shape before this task. Selection is `LLM_PROVIDER` only.

**Acceptance criteria:**
- [ ] `LLM_PROVIDER=meta` resolves this client and `groq` resolves Groq
- [ ] httpx mock covers a successful chat and a timeout that can fall back to Groq when configured
- [ ] Official docs for base URL and tool-calling are linked in the module docstring

**Verification:**
- [ ] Unit tests with a mocked HTTP transport
- [ ] No live Meta call in the default pytest run

**Dependencies:** Task 6

**Files likely touched:**
- `backend/app/llm/meta/client.py`
- `backend/app/llm/factory.py`
- `backend/tests/unit/test_meta_provider.py`

**Estimated scope:** Medium

## Task 8: Catalog vision extraction

**Description:** Seller product photos go through `LLMProvider.vision` and must parse to `{name, description, suggested_price_kobo|null, category, colors[], confidence}`. Invalid JSON retries once, then asks the seller to type the details.

**Acceptance criteria:**
- [ ] A valid vision payload maps onto that schema, with kobo as an integer or null
- [ ] A broken JSON response retries once and then returns the ask-seller fallback
- [ ] The image bytes are not logged

**Verification:**
- [ ] Unit tests with `FakeProvider` for success, invalid JSON, and retry
- [ ] Schema matches `docs/agent.md`

**Dependencies:** Task 6

**Files likely touched:**
- `backend/app/agent/catalog.py`
- `backend/tests/unit/test_catalog_extract.py`

**Estimated scope:** Small

## Task 9: Photo to saved product

**Description:** Seller image is stored in the private Supabase bucket, a product row is inserted only after the seller confirms the price, and the chat reply confirms name and price from the database.

**Acceptance criteria:**
- [ ] Suggested price is never saved until the seller confirms
- [ ] Stored object uses a signed URL; the bucket is not public
- [ ] Confirmation message uses the money template and the saved `price_kobo`

**Verification:**
- [ ] Integration test with mocked storage and `FakeProvider`
- [ ] Manual: photo on the test number creates a product and a confirmation

**Dependencies:** Tasks 3, 5, 8

**Files likely touched:**
- `backend/app/db/repo.py`
- `backend/app/agent/catalog.py`
- `backend/app/agent/templates.py`
- `backend/tests/integration/test_catalog_flow.py`

**Estimated scope:** Medium

## Checkpoint: After Tasks 6–9
- [ ] Seller photo becomes a product and a chat confirmation
- [ ] CI still uses fakes, not live LLM calls
- [ ] Review with a human before Phase 3

---

## Phase 3: Buyer chat and orders (Tue 28 Oct)

## Task 10: Jev client and routing questions

**Description:** TypeSafe client and question specs for `intent`, `language`, `scam_pressure`, and `image_kind`. Confirm the request schema on docs.typesafe.ai first. Tests use a fake client.

**Acceptance criteria:**
- [ ] One call returns all four scores
- [ ] Low-confidence language falls back to the seller default language
- [ ] `image_kind` distinguishes product photo, payment receipt, and other

**Verification:**
- [ ] Unit tests for routing decisions from fixture scores
- [ ] Live Jev call marked `@pytest.mark.live` only

**Dependencies:** Task 1

**Files likely touched:**
- `backend/app/decisions/client.py`
- `backend/app/decisions/questions.py`
- `backend/tests/unit/test_jev_route.py`

**Estimated scope:** Medium

## Task 11: State graph observe, route, respond

**Description:** Inbound turn runs observe (dedupe, load seller, buyer, open order), route, then a branch. Cap at 6 graph steps and 3 tool calls. Persist a trace after route and respond. Over the cap, send a short fallback and notify the seller.

**Acceptance criteria:**
- [ ] State fields match the schema in `docs/harness_engineering.md`
- [ ] Step and tool caps stop the loop and send the fallback
- [ ] Each node records `trace_id`, node name, and latency

**Verification:**
- [ ] Unit tests for cap, dedupe, and trace rows
- [ ] A duplicate webhook does not send a second reply

**Dependencies:** Tasks 5, 10

**Files likely touched:**
- `backend/app/agent/graph/state.py`
- `backend/app/agent/graph/nodes.py`
- `backend/app/db/migrations/0002_traces.sql`
- `backend/tests/unit/test_graph_caps.py`

**Estimated scope:** Medium

## Task 12: Catalog and order tools

**Description:** Typed tools: `search_catalog`, `get_product`, `create_order`, `get_order_status`, `cancel_order`. Prices and stock are read from the database inside the tool. `create_order` writes status `awaiting_payment`, items, `total_kobo`, and a unique `SS-` ref. Seller scope is enforced on every call.

**Acceptance criteria:**
- [ ] A tool cannot return a price the model invented
- [ ] Order total equals the sum of `unit_price_kobo * qty`
- [ ] Unknown product or wrong seller returns `{error: code, message}`

**Verification:**
- [ ] Table tests for totals, refs, and scope errors
- [ ] Tool schemas match `docs/agent.md` and `docs/harness_engineering.md`

**Dependencies:** Tasks 3, 9

**Files likely touched:**
- `backend/app/agent/tools/catalog.py`
- `backend/app/agent/tools/orders.py`
- `backend/tests/unit/test_order_tools.py`

**Estimated scope:** Medium

## Task 13: Language prompts, money templates, reply check

**Description:** Shared system prompt plus style files `en`, `pcm`, and `yo`. Amounts, account numbers, and verdicts render only through `backend/app/agent/templates.py`. Reply check rejects invented prices, wrong language, and any "payment confirmed" line the verdict tool did not return. One retry, then a template fallback.

**Acceptance criteria:**
- [ ] Account numbers in templates show the last 4 digits
- [ ] A reply that mentions a price absent from tool output fails the check
- [ ] Yoruba and Pidgin examples match `docs/agent.md` and are marked for native-speaker review

**Verification:**
- [ ] Unit tests for template rendering and reply-check failures
- [ ] Prompt files contain the never-invent-price and never-confirm-payment rules

**Dependencies:** Task 12

**Files likely touched:**
- `backend/app/agent/prompts/en.md`
- `backend/app/agent/prompts/pcm.md`
- `backend/app/agent/prompts/yo.md`
- `backend/app/agent/templates.py`
- `backend/app/agent/reply_check.py`
- `backend/tests/unit/test_reply_check.py`

**Estimated scope:** Medium

## Task 14: Price question and order on WhatsApp

**Description:** Wire the sales branch. A price question searches the catalog and replies in the buyer's language. An order utterance calls `create_order` and replies with the pay-to template and order ref.

**Acceptance criteria:**
- [ ] "Abeg how much for the black bag?" returns the stored price in Pidgin
- [ ] "I go take 1" inserts an order in `awaiting_payment` and replies with ref and amount
- [ ] Chit-chat does not create an order

**Verification:**
- [ ] Integration test with `FakeProvider` and fake Jev scores
- [ ] Manual on the WhatsApp test number, clip saved under `demo/clips/`

**Dependencies:** Tasks 11, 12, 13

**Files likely touched:**
- `backend/app/agent/graph/sales.py`
- `backend/app/api/webhooks/whatsapp.py`
- `backend/tests/integration/test_order_flow.py`

**Estimated scope:** Medium

## Checkpoint: After Tasks 10–14
- [ ] Pidgin price and order flow persists `awaiting_payment`
- [ ] Reply prices match the database
- [ ] Review with a human before Phase 4

---

## Phase 4: Verification v1 (Wed 29 Oct)

## Task 15: Receipt extraction and image hashes

**Description:** Payment images run vision into the screenshot schema in `docs/agent.md`. Store the file privately. Compute SHA-256 and a perceptual hash. Image text is data, never instructions.

**Acceptance criteria:**
- [ ] Extraction fields include amount_kobo, reference, sender, recipient last4, status text, and visual anomalies
- [ ] `is_transfer_receipt=false` does not open the verdict path
- [ ] Hashes are stored on the evidence row (trust level 1)

**Verification:**
- [ ] Unit test maps a fake vision payload onto `payment_evidence`
- [ ] Invalid JSON retries once

**Dependencies:** Tasks 6, 11

**Files likely touched:**
- `backend/app/verification/extract.py`
- `backend/tests/unit/test_receipt_extract.py`

**Estimated scope:** Medium

## Task 16: Rules R1–R9

**Description:** Implement `verification/rules.py` exactly as the rule table in `docs/payment_verification.md`, including weights, the R7 cap, and R8 `not_confirmable`.

**Acceptance criteria:**
- [ ] Each rule id has a pass and a fail case
- [ ] `rule_risk` is the minimum of 1 and the sum of weights
- [ ] Duplicate reference (R4) and blocklist (R6) fire from stored rows

**Verification:**
- [ ] Table-driven unit tests cover R1–R9
- [ ] Weights match the spec

**Dependencies:** Task 3

**Files likely touched:**
- `backend/app/verification/rules.py`
- `backend/tests/unit/test_rules.py`

**Estimated scope:** Medium

## Task 17: Verdict engine

**Description:** `verdict.py` is the only writer of verdicts. It applies the verdict table: trust level, match result, confidence band, and hard rules. Screenshot-only evidence cannot set `release_allowed`.

**Acceptance criteria:**
- [ ] Every row of the verdict table has a test, including partial payment and pending status
- [ ] Level ≥ 3, match, and confidence ≥ 0.90 yields CONFIRMED and `release_allowed=true`
- [ ] Rule risk ≥ 0.6, R4, R5, or R6 yields SUSPICIOUS and `release_allowed=false`

**Verification:**
- [ ] `pytest -q -m "not live" backend/tests/unit/test_verdict.py`
- [ ] No LLM import in `verdict.py`

**Dependencies:** Task 16

**Files likely touched:**
- `backend/app/verification/verdict.py`
- `backend/app/verification/matchers.py`
- `backend/tests/unit/test_verdict.py`

**Estimated scope:** Medium

## Task 18: Paystack test virtual account and webhook

**Description:** Create a test dedicated virtual account for the seller. `POST /webhooks/paystack` checks `x-paystack-signature` as HMAC-SHA512 over the raw body, dedupes on event id, returns 200, and re-fetches the transaction before inserting level-4 evidence. Confirm current test-mode event names before coding.

**Acceptance criteria:**
- [ ] Bad signature returns 401
- [ ] Duplicate event id returns 200 and inserts one evidence row
- [ ] Evidence is stored only after the verify-transaction call succeeds

**Verification:**
- [ ] Unit tests for signature, duplicate, and verify-call failure
- [ ] Manual test transfer on Paystack test mode

**Dependencies:** Tasks 3, 5

**Files likely touched:**
- `backend/app/payments/paystack/webhook.py`
- `backend/app/payments/paystack/dva.py`
- `backend/app/api/webhooks/paystack.py`
- `backend/tests/unit/test_paystack_webhook.py`

**Estimated scope:** Medium

## Task 19: Screenshot and webhook paths to a verdict

**Description:** Connect extraction, rules, matcher, and Paystack evidence. A webhook can confirm an order before or after the screenshot. `POST /orders/{ref}/release` returns 409 when `release_allowed` is false. Buyer and seller messages come from templates.

**Acceptance criteria:**
- [ ] Matching level-4 evidence yields CONFIRMED either order of arrival
- [ ] An edited amount or a reused reference yields SUSPICIOUS or NOT FOUND and blocks release
- [ ] Seller message states the verdict and whether goods may leave

**Verification:**
- [ ] Integration tests: webhook-first, screenshot-first, and release 409
- [ ] Manual: test transfer CONFIRMED; edited screenshot does not release goods

**Dependencies:** Tasks 15, 17, 18

**Files likely touched:**
- `backend/app/verification/matchers.py`
- `backend/app/agent/graph/verify.py`
- `backend/app/api/internal/orders.py`
- `backend/tests/integration/test_verify_flow.py`

**Estimated scope:** Medium

## Task 20: Flutterwave webhook

**Description:** `POST /webhooks/flutterwave` checks the `verif-hash` header, dedupes, and writes the same level-4 evidence type the Paystack path uses.

**Acceptance criteria:**
- [ ] Header mismatch returns 401
- [ ] A matching event confirms through the existing verdict engine
- [ ] Duplicate delivery is stored once

**Verification:**
- [ ] Unit test with fixture payloads
- [ ] Paystack tests still pass

**Dependencies:** Task 19

**Files likely touched:**
- `backend/app/payments/flutterwave/webhook.py`
- `backend/app/api/webhooks/flutterwave.py`
- `backend/tests/unit/test_flutterwave_webhook.py`

**Estimated scope:** Small

## Checkpoint: After Tasks 15–20
- [ ] Test transfer ends CONFIRMED
- [ ] Edited screenshot cannot release goods (409)
- [ ] Verdict-table tests cover every row
- [ ] Review with a human before Phase 5

---

## Phase 5: Verification v2 and evals (Thu 30 Oct)

## Task 21: Forwarded bank-alert parser

**Description:** Parse seller-forwarded SMS or email into `{amount_kobo, type, narration, balance_kobo, txn_time_iso, bank}` for fictional GTB, Access, and OPay formats. Accept the alert only from the seller's registered channel. Trust level 2.

**Acceptance criteria:**
- [ ] Credit and debit fixtures parse to kobo and UTC timestamps
- [ ] A buyer-originated alert is not stored as seller evidence
- [ ] `POST /alerts/sms` and the email webhook require their secrets

**Verification:**
- [ ] Fixture tests in `evals/fixtures/` and `backend/tests/unit/test_alerts.py`
- [ ] Matcher can link a level-2 alert to an order

**Dependencies:** Task 17

**Files likely touched:**
- `backend/app/payments/alerts/parse.py`
- `backend/app/api/webhooks/alerts.py`
- `evals/fixtures/bank_alerts.txt`
- `backend/tests/unit/test_alerts.py`

**Estimated scope:** Medium

## Task 22: Jev tamper and match scores

**Description:** Ask `receipt_tampered` and `evidence_match`. When evidence exists, `confidence = p_match * (1 - max(p_tamper, rule_risk))`. Bands stay 0.90 auto, 0.60–0.90 ask the seller, below 0.60 flag.

**Acceptance criteria:**
- [ ] The formula matches `docs/payment_verification.md` on fixed inputs
- [ ] Missing Jev scores do not upgrade a verdict to CONFIRMED
- [ ] Scores are stored on `verdicts.jev_scores`

**Verification:**
- [ ] Unit tests for the three bands and a Jev outage
- [ ] Question ids match `docs/agent.md`

**Dependencies:** Tasks 10, 17

**Files likely touched:**
- `backend/app/decisions/questions.py`
- `backend/app/verification/verdict.py`
- `backend/tests/unit/test_confidence.py`

**Estimated scope:** Small

## Task 23: Seller verdict card, human-in-the-loop, recheck

**Description:** Seller receives the verdict template. Confidence 0.60–0.90 waits for `/release` or an explicit rejection. NOT FOUND and UNVERIFIED recheck for 30 minutes (webhook arrival short-circuits). After expiry, at most two buyer reminders, then cancel. Persist the pending decision so a restart can resume.

**Acceptance criteria:**
- [ ] Mid-band confidence never sets `release_allowed` until the seller accepts
- [ ] A late matching webhook flips NOT FOUND to CONFIRMED and notifies both sides
- [ ] Reminder count stops at 2

**Verification:**
- [ ] Integration test with a clock fixture for the 30-minute window
- [ ] Seller command resumes a stored checkpoint

**Dependencies:** Tasks 19, 22

**Files likely touched:**
- `backend/app/agent/graph/verify.py`
- `backend/app/agent/templates.py`
- `backend/app/jobs/recheck.py`
- `backend/tests/integration/test_recheck.py`

**Estimated scope:** Medium

## Task 24: Eval runner and synthetic set v1

**Description:** `python -m evals.run` scores extraction and verdicts with `FakeProvider` in CI and a provider flag for manual runs. v1 set has at least 20 synthetic images plus `labels.jsonl` (edited amount, reused ref, pending, not-a-receipt). Launch gate: zero false CONFIRMED on fakes.

**Acceptance criteria:**
- [ ] Report at `evals/report.md` includes a confusion matrix
- [ ] A fake labelled class that returns CONFIRMED fails the run
- [ ] Real-derived images are documented as `evals/data/private/` and are gitignored

**Verification:**
- [ ] `python -m evals.run` exits 0 on the synthetic set
- [ ] A fixture that forces CONFIRMED on a fake fails the gate

**Dependencies:** Tasks 17, 19

**Files likely touched:**
- `evals/run.py`
- `evals/data/synthetic/labels.jsonl`
- `evals/gen_receipts.py`
- `backend/tests/unit/test_eval_gate.py`

**Estimated scope:** Medium

## Task 25: Demo storyboard draft (human)

**Description:** Write the 2:45 storyboard from `docs/hackathon_launch.md` into `demo/` (hook, catalog, Pidgin and Yoruba order, fake caught, webhook confirmed, close).

**Acceptance criteria:**
- [ ] Each scene has a visual and a voiceover line
- [ ] Runtime totals at most 3 minutes
- [ ] No real phone numbers or account numbers in the script

**Verification:**
- [ ] Script read aloud once
- [ ] Saved under `demo/`

**Dependencies:** None

**Files likely touched:**
- `demo/storyboard.md`

**Estimated scope:** Small

## Checkpoint: After Tasks 21–25
- [ ] Eval script runs and the false-CONFIRMED count is 0
- [ ] Storyboard draft is saved
- [ ] Review with a human before Phase 6

---

## Phase 6: Instagram and voice (Fri 31 Oct)

## Task 26: Instagram adapter

**Description:** Same adapter contract and graph for Instagram messaging webhooks. Signature, parse, send, and media fetch. Human setup (Business account linked to a Page) should already be in progress from day 1.

**Acceptance criteria:**
- [ ] IG text and image fixtures normalize to `InboundMessage`
- [ ] An order utterance in an IG DM creates `awaiting_payment` through the existing tools
- [ ] Bad signature returns 401

**Verification:**
- [ ] Integration test with IG fixtures
- [ ] Manual DM on the test account, clip saved

**Dependencies:** Task 14

**Files likely touched:**
- `backend/app/channels/instagram/adapter.py`
- `backend/app/api/webhooks/instagram.py`
- `backend/tests/integration/test_instagram_flow.py`

**Estimated scope:** Medium

## Task 27: Voice-note transcription

**Description:** Audio messages call Intron Sahara STT (Yoruba-English `yo`, Pidgin-English `pcm`, English `en`). The transcript, language, and ASR confidence are stored on the message, and the transcript re-enters the graph as text. TTS replies are optional and follow `docs/architecture.md`. Groq is not the speech path.

**Acceptance criteria:**
- [ ] A voice note with a fake transcript can search the catalog and create an order
- [ ] Transcription failure replies with a short "please type that" template
- [ ] Audio bytes are not logged

**Verification:**
- [ ] Unit test with a fake Intron client (no live call, no audio in logs)
- [ ] Manual voice note on WhatsApp

**Dependencies:** Tasks 6, 14

**Files likely touched:**
- `backend/app/speech/` (Intron STT/TTS client)
- `backend/app/agent/graph/nodes.py`
- `backend/tests/unit/test_voice_note.py`

**Estimated scope:** Small

## Checkpoint: After Tasks 26–27
- [ ] Order flow works in an Instagram DM
- [ ] Voice note can place an order
- [ ] If WhatsApp core is still failing, stop this phase and return to Phase 4

---

## Phase 7: Fraud memory, jobs, and web start (Sat 1 Nov)

## Task 28: Scammer memory

**Description:** Seller command `/fake SS-1042` inserts confirmed `fraud_signals` (hashed account, phone, image hash). `/notfake` disputes. Only `confirmed=true` rows trigger R6, including for a different seller.

**Acceptance criteria:**
- [ ] A confirmed signal from seller A flags seller B's matching evidence
- [ ] Unconfirmed signals do not add R6
- [ ] Raw account numbers are stored only as hashes

**Verification:**
- [ ] Unit test across two seller ids
- [ ] Manual: repeat scammer flagged, clip saved

**Dependencies:** Tasks 16, 23

**Files likely touched:**
- `backend/app/verification/fraud.py`
- `backend/app/agent/graph/seller_cmd.py`
- `backend/tests/unit/test_fraud_signals.py`

**Estimated scope:** Medium

## Task 29: Payment reminders and daily summary

**Description:** Cron endpoints `POST /jobs/reminders` and `POST /jobs/daily-summary` (internal token). Reminders respect the max of 2. Summary includes orders, paid kobo, fakes caught, and `naira_saved_kobo` as defined in `docs/data_model.md`, rendered in WAT.

**Acceptance criteria:**
- [ ] Unpaid orders get at most two reminders
- [ ] Summary naira saved counts SUSPICIOUS or NOT FOUND payments with goods held and no later CONFIRMED evidence inside 48 hours
- [ ] Both routes reject a missing internal token

**Verification:**
- [ ] Unit tests for the naira-saved query and reminder cap
- [ ] Manual summary message on the test number

**Dependencies:** Tasks 14, 23

**Files likely touched:**
- `backend/app/jobs/reminders.py`
- `backend/app/jobs/daily_summary.py`
- `backend/app/api/internal/jobs.py`
- `backend/tests/unit/test_daily_summary.py`

**Estimated scope:** Medium

## Task 30: Onboarding site shell and platform steps

**Description:** Next.js App Router site in `web/`: top bar, theme (no flash), platform tabs synced to `?platform=`, steps copied from `docs/web_content/` into `web/content/`. Code blocks mask secrets and copy with a toast. Steps not yet checked against Meta docs stay marked TODO verify.

**Acceptance criteria:**
- [ ] `/`, `/?platform=instagram`, and `/?platform=messenger` show that platform's steps
- [ ] Copy control announces "Copied" and does not reveal a token
- [ ] Light, dark, and system themes follow `docs/design.md` tokens

**Verification:**
- [ ] `npm run lint` and `npm run build` in `web/`
- [ ] Keyboard tab change and a copy click work in the browser

**Dependencies:** Task 5 (webhook URL is real)

**Files likely touched:**
- `web/app/page.tsx`
- `web/components/PlatformTabs.tsx`
- `web/components/StepCard.tsx`
- `web/components/CodeBlock.tsx`
- `web/content/whatsapp.ts`
- `web/content/instagram.ts`
- `web/content/messenger.ts`

**Estimated scope:** Medium

## Task 31: Rough demo recording (human)

**Description:** One rough screen recording of catalog, Pidgin order, suspicious screenshot, and webhook confirmation. Keep raw footage in `demo/raw/` (gitignored).

**Acceptance criteria:**
- [ ] All four beats are visible
- [ ] No live customer data on screen
- [ ] Notes on what to reshoot are written next to the storyboard

**Verification:**
- [ ] Clip plays locally
- [ ] Storyboard gaps are listed

**Dependencies:** Tasks 14, 19, 25

**Files likely touched:**
- `demo/storyboard.md`

**Estimated scope:** Small

## Checkpoint: After Tasks 28–31
- [ ] Repeat scammer is flagged across two sellers
- [ ] Daily summary sends
- [ ] Onboarding home page renders three platforms
- [ ] Review with a human before freeze day

---

## Phase 8: Web finish, deploy, freeze (Sun 2 Nov)

## Task 32: Status, FAQ, privacy, and small screens

**Description:** Finish `/status`, `/faq`, and `/privacy`. Status check states: idle, checking, connected, failed. Prerequisites collapse on small screens. Honour `prefers-reduced-motion`. Focus rings and text on status badges.

**Acceptance criteria:**
- [ ] `/status` shows connected and failed, and the failed state links to the FAQ fix
- [ ] `/privacy` lists what is stored (hashes, receipts, messages) in plain language
- [ ] Below 640px the layout is one column and code blocks scroll sideways

**Verification:**
- [ ] Browser pass on desktop and a narrow viewport: tab switch, copy, status, FAQ
- [ ] `npm run build` succeeds

**Dependencies:** Task 30

**Files likely touched:**
- `web/app/status/page.tsx`
- `web/app/faq/page.tsx`
- `web/app/privacy/page.tsx`
- `web/components/StatusCheck.tsx`

**Estimated scope:** Medium

## Task 33: Deploy and tag v0.1-demo

**Description:** API on Render or Railway with `/health`. Site on Vercel. Secrets only in the host env. Tag `v0.1-demo` at freeze. Production provider is `meta` when credits exist; otherwise document Groq and the switch.

**Acceptance criteria:**
- [ ] Public `/health` returns ok
- [ ] WhatsApp webhook on the deployed URL still completes verify
- [ ] Tag `v0.1-demo` points at the freeze commit

**Verification:**
- [ ] Fresh test message on the deployed bot
- [ ] Host dashboards show no secret in build logs

**Dependencies:** Tasks 19, 32

**Files likely touched:**
- `README.md`
- deployment config the host requires (only if the host needs a file in repo)

**Estimated scope:** Medium

## Task 34: One stretch — Messenger or RefPay

**Description:** Pick one only if Tasks 1–33 are green. Messenger: adapter plus webhook, same graph. RefPay: testnet USDC evidence, recipient, token, amount, and minimum confirmations, trust level 4. Skip both if the core path is thin.

**Acceptance criteria:**
- [ ] The chosen path has a test and a manual demo step
- [ ] RefPay, if chosen, cannot confirm a wrong token or a short confirmation count
- [ ] Messenger, if chosen, reuses `InboundMessage` and the verdict engine

**Verification:**
- [ ] Focused pytest for the chosen integration
- [ ] The other stretch is left unbuilt

**Dependencies:** Task 33

**Files likely touched:**
- `backend/app/channels/messenger/adapter.py` or `backend/app/payments/crypto_refpay/`
- one matching test file

**Estimated scope:** Medium

## Checkpoint: Feature freeze
- [ ] Deployed URL is stable
- [ ] Core WhatsApp path still works
- [ ] Tag `v0.1-demo` exists
- [ ] No feature work after 23:59 WAT on 2 Nov

---

## Phase 9: Demo (Mon 3 Nov)

## Task 35: Seed demo data

**Description:** `python -m scripts.seed_demo` loads `docs/demo_data.md`: Tolu's Bags, four products, buyers A and B, scammer C, one confirmed fraud signal, and the labelled demo summary numbers.

**Acceptance criteria:**
- [ ] Seed is idempotent
- [ ] Amounts match the demo doc in kobo
- [ ] Seed refuses to run when `APP_ENV=production` unless an explicit demo flag is set

**Verification:**
- [ ] Unit test of the seed payload
- [ ] Running twice does not duplicate products

**Dependencies:** Tasks 9, 28

**Files likely touched:**
- `scripts/seed_demo.py`
- `backend/tests/unit/test_seed_demo.py`

**Estimated scope:** Small

## Task 36: Final video (human)

**Description:** Two takes, edit, captions, 1080p, ≤ 3 minutes, unlisted YouTube or Loom. Scenes follow the storyboard. Phone via scrcpy or WhatsApp Web.

**Acceptance criteria:**
- [ ] Logged-out browser can open the link
- [ ] Fake receipt and real test payment are both on screen
- [ ] No real account numbers or customer data

**Verification:**
- [ ] Watch in a private window
- [ ] Link pasted into the submission notes

**Dependencies:** Tasks 33, 35, 25

**Files likely touched:**
- `demo/storyboard.md`

**Estimated scope:** Small (human)

## Checkpoint: After Tasks 35–36
- [ ] Demo seller and products exist
- [ ] Video link opens logged out and stays under 3 minutes

---

## Phase 10: Submit (Tue 4 Nov)

## Task 37: README, screenshots, and pre-submit tests

**Description:** Public README: pitch, setup, architecture image, Meta models used. Screenshots for catalog, Pidgin, Yoruba, SUSPICIOUS, CONFIRMED, and daily summary. Run the pre-submit list in `docs/hackathon_launch.md`.

**Acceptance criteria:**
- [ ] Fresh number: order, test pay, CONFIRMED
- [ ] Fake screenshot: SUSPICIOUS and release 409
- [ ] Duplicate webhook processed once; bad signature 401
- [ ] `pytest`, evals, and gitleaks are green

**Verification:**
- [ ] Checklist in `docs/hackathon_launch.md` is ticked from this run
- [ ] README setup commands match the repo

**Dependencies:** Tasks 33, 36

**Files likely touched:**
- `README.md`
- `docs/hackathon_launch.md`
- `web/public/screenshots/`

**Estimated scope:** Medium

## Task 38: Submit and tag v1.0-submission (human)

**Description:** Submit the Indie track by 18:00 WAT. Confirm the form fields that morning. Save the confirmation. Tag `v1.0-submission`.

**Acceptance criteria:**
- [ ] Repo is public, MIT license, history scanned
- [ ] Write-up uses measured eval numbers only
- [ ] Confirmation email or screenshot is saved outside the repo if it contains personal data, and the submission id is noted in the README

**Verification:**
- [ ] Submission page shows received
- [ ] Tag exists on the submitted commit

**Dependencies:** Task 37

**Files likely touched:**
- `README.md`
- `LICENSE`

**Estimated scope:** Small (human)

## Checkpoint: Submitted
- [ ] Submitted by 18:00 WAT on 4 Nov
- [ ] Confirmation saved
- [ ] Tests, evals, and gitleaks green on the tagged commit

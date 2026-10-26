# Execution Plan (Oct 26 – Nov 4, 2026)
Deadline: **Nov 4, 9:00 PM ET = Nov 5, 02:00 WAT**. Internal target: submitted by **Nov 4, 6:00 PM WAT**.
Feature freeze: **Nov 2, end of day**. Nov 3 morning is benchmark day (frozen suites only). Nov 3 afternoon–Nov 4: video, README, submission. The video and write-up may cite a headline only after that run fills it in.

| Day | Focus | Tasks | Deliverable / DoD |
|---|---|---|---|
| **Sun Oct 26** | Setup | Repo + `AGENTS.md`, `.gitignore`, `.env.example`; FastAPI skeleton; `/health`; Supabase project + migrations; Meta App + WhatsApp test number; ngrok; Groq key | Webhook verify (GET) passes; echo bot replies on WhatsApp |
| **Mon Oct 27** | LLM layer + catalog | `LLMProvider` (groq/meta); photo → catalog item (vision → JSON); store image in Supabase Storage | Seller sends photo → product saved and confirmed back in chat |
| **Tue Oct 28** | Buyer chat + orders | Jev intent + language routing; tools `search_catalog`, `create_order`; replies in EN/Pidgin/Yoruba | Buyer asks price and orders in Pidgin → order row `awaiting_payment` |
| **Wed Oct 29** | Verification v1 | Screenshot extraction; rule checks; Paystack test virtual account + webhook (signature, idempotency) | Real test transfer → CONFIRMED; edited screenshot → SUSPICIOUS/NOT FOUND |
| **Thu Oct 30** | Verification v2 | Bank alert forwarding parser; Jev verdict questions + thresholds; seller verdict card; eval set v1 (≥20 images) | Eval script runs; verdict table from `payment_verification.md` implemented. **Storyboard draft done** |
| **Fri Oct 31** | Channels + voice | Instagram adapter (Business acct linked to FB Page set up Oct 26!); buyer voice notes via Intron Sahara STT (`yo`, `pcm`, `en`); TTS replies only if the day still has room | Same flow works in IG DM; a Yoruba or Pidgin voice note becomes a transcript and can place an order |
| **Sat Nov 1** | Fraud memory + ops + web onboarding (start) | `fraud_signals` blocklist; reminders; daily summary + ₦ saved; switch to Meta API if credits landed; start **web onboarding site** (docs/design.md): platform tabs, steps, copy buttons | Repeat scammer flagged across two sellers; summary message sent. **Rough demo recording #1** |
| **Sun Nov 2** | Web onboarding (finish) + stretch + freeze | Finish onboarding site on Vercel (status check, mobile, dark mode; ~1 day total over Nov 1–2, only after the core works); then pick ONE: RefPay USDC testnet / Next.js dashboard / Messenger. Bug bash. Deploy to Render/Railway. At freeze, lock eval dataset versions (`evals/datasets/*/v1`) and the harness SHA in `docs/benchmark.md` | Deployed URL stable; datasets frozen; **FEATURE FREEZE 23:59 WAT** |
| **Mon Nov 3** | Benchmark, then demo | **Morning — benchmark day.** Run the frozen suites in `docs/benchmark.md` on the frozen harness. Fill the results template with measured numbers only; leave a cell `TBD` if that suite did not run. Copy at most the headline claims (false-CONFIRMED count, conversation pass^1 and pass^4, speech WER if the set exists) into the storyboard and write-up. **Afternoon:** seed demo data; record take 1 and take 2; edit; captions | `evals/reports/` has the run (or an explicit "not run"); video ≤3 min, and it does not speak a number that is still `TBD` |
| **Tue Nov 4** | Submit | README, screenshots, architecture image, write-up; pre-submit tests (`hackathon_launch.md`); submit | Submitted by 18:00 WAT; confirmation saved |

## Daily definition of done
- Code on `main` via PR, CI green, no secrets in diff.
- Feature demonstrable end-to-end on the WhatsApp test number.
- `CHANGELOG` line + one screenshot/clip saved to `demo/clips/` (raw material for the video).

## Cut list (cut from top first if behind)
1. Mono sandbox
2. Messenger adapter
3. Next.js dashboard (replace with a WhatsApp daily summary)
3b. Web onboarding site: cut to one static page with WhatsApp steps only
4. Crypto/RefPay
5. Voice replies via Intron TTS (keep Intron STT)
6. Instagram (only if WhatsApp core is not solid by Oct 31)
**Never cut:** photo→catalog, buyer order, Paystack webhook confirmation, screenshot verdict, demo video.

## Risks
| Risk | Mitigation |
|---|---|
| Meta card restricted / credits late | Groq behind `LLMProvider` as a labeled fallback; the write-up still names Muse as the target. Exact Muse ids stay **TODO verify** until a live call |
| Intron TTS voice for Yoruba or Pidgin rejected, or 30/min cap | STT still runs. TTS falls back to English with a Yoruba accent. A 503 is polled, not retried as a new generate |
| WhatsApp test number limits (allowed recipients) | Register demo phones early as test recipients |
| IG Business/Page linking delays | Start setup Day 1 |
| Weak laptop | Hosted everything; no local models; use Supabase cloud |
| Video quality | Storyboard by Oct 30, two recordings, script read aloud |

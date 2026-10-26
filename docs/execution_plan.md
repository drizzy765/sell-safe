# Execution Plan (Oct 26 – Nov 4, 2026)
Deadline: **Nov 4, 9:00 PM ET = Nov 5, 02:00 WAT**. Internal target: submitted by **Nov 4, 6:00 PM WAT**.
Feature freeze: **Nov 2, end of day**. Nov 3–4: video, README, submission only.

| Day | Focus | Tasks | Deliverable / DoD |
|---|---|---|---|
| **Sun Oct 26** | Setup | Repo + `AGENTS.md`, `.gitignore`, `.env.example`; FastAPI skeleton; `/health`; Supabase project + migrations; Meta App + WhatsApp test number; ngrok; Groq key | Webhook verify (GET) passes; echo bot replies on WhatsApp |
| **Mon Oct 27** | LLM layer + catalog | `LLMProvider` (groq/meta); photo → catalog item (vision → JSON); store image in Supabase Storage | Seller sends photo → product saved and confirmed back in chat |
| **Tue Oct 28** | Buyer chat + orders | Jev intent + language routing; tools `search_catalog`, `create_order`; replies in EN/Pidgin/Yoruba | Buyer asks price and orders in Pidgin → order row `awaiting_payment` |
| **Wed Oct 29** | Verification v1 | Screenshot extraction; rule checks; Paystack test virtual account + webhook (signature, idempotency) | Real test transfer → CONFIRMED; edited screenshot → SUSPICIOUS/NOT FOUND |
| **Thu Oct 30** | Verification v2 | Bank alert forwarding parser; Jev verdict questions + thresholds; seller verdict card; eval set v1 (≥20 images) | Eval script runs; verdict table from `payment_verification.md` implemented. **Storyboard draft done** |
| **Fri Oct 31** | Channels + voice | Instagram adapter (Business acct linked to FB Page set up Oct 26!); voice notes → transcription | Same flow works in IG DM; voice note order works |
| **Sat Nov 1** | Fraud memory + ops + web onboarding (start) | `fraud_signals` blocklist; reminders; daily summary + ₦ saved; switch to Meta API if credits landed; start **web onboarding site** (docs/design.md): platform tabs, steps, copy buttons | Repeat scammer flagged across two sellers; summary message sent. **Rough demo recording #1** |
| **Sun Nov 2** | Web onboarding (finish) + stretch + freeze | Finish onboarding site on Vercel (status check, mobile, dark mode; ~1 day total over Nov 1–2, only after the core works); then pick ONE: RefPay USDC testnet / Next.js dashboard / Messenger. Bug bash. Deploy to Render/Railway | Deployed URL stable; **FEATURE FREEZE 23:59 WAT** |
| **Mon Nov 3** | Demo | Seed demo data; record final video take 1 & take 2; edit; captions | Video ≤3 min uploaded (unlisted YouTube) |
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
5. Voice replies (keep transcription only)
6. Instagram (only if WhatsApp core is not solid by Oct 31)
**Never cut:** photo→catalog, buyer order, Paystack webhook confirmation, screenshot verdict, demo video.

## Risks
| Risk | Mitigation |
|---|---|
| Meta card restricted / credits late | Groq behind `LLMProvider`; swap by env var |
| WhatsApp test number limits (allowed recipients) | Register demo phones early as test recipients |
| IG Business/Page linking delays | Start setup Day 1 |
| Weak laptop | Hosted everything; no local models; use Supabase cloud |
| Video quality | Storyboard by Oct 30, two recordings, script read aloud |

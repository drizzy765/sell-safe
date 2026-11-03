# Changelog

## 2026-11-02

### Dashboard — edit shop & payout after onboarding
- Settings tab (`/dashboard?tab=settings`) now includes **Shop info** and **Payout account** (bank name, account name, account number).
- Sidebar shop label opens Settings so sellers can update details without redoing Connect / Confirm shop.
- Saves via existing `PATCH /api/onboarding/shop` (masked account number in responses).

### Instagram agent — payment details
- New `get_payment_details` tool; when a buyer asks for account number / how to pay, the bot shares the shop’s saved bank details (or says they are not configured).
- Reply check allowlists account digits returned by tools (still blocks invented numbers).
- Prompts updated: do not ask for a transfer receipt before sharing pay-to details.

### Instagram inbox reliability
- Auto-subscribe connected IG account to app message webhooks after OAuth (`me/subscribed_apps`).
- Session store matches webhook recipient by professional `user_id` **or** IG-scoped `/me` id aliases.
- Graph Conversations sync marks inbound rows `source=graph_sync` so a later webhook with the same message id still runs the agent (fixes race where dashboard sync swallowed auto-replies).

## 2026-11-03 (build day)
- [x] PR #20 merged (inbox sync, payout details, dashboard Settings).
- [x] Local “deploy” via Cloudflare quick tunnels + logged test accounts in `docs/demo_test_accounts.md`.
- [x] Backend deployed to Render: `https://sell-safe-api.onrender.com` (`/health` 200, webhook verify 200, OAuth redirect on Render host). Meta OAuth/webhook repointed from dead tunnels to Render.
- [ ] Playwright/Puppeteer smoke of Sell-Safe website (landing → Connect → dashboard Settings).
- [ ] Live DM retest: `testicles22` → `sellsafe.testshop.ng` (after Meta redirect/webhook point at Render).
- [ ] Web deploy (Vercel) — web still runs locally behind a tunnel.
- [ ] Optimize final changes; run **benchmark** per `docs/benchmark.md`; optional dashboard/UI extras.
- [ ] Tag `v0.1-demo` when freeze-ready (`docs/github_rules.md`).

## 2026-10-26

- Merged PR #3: buyer chat and orders with Jev routing.
- Buyer can ask prices and place orders in English, Pidgin, or Yoruba.
- Added Jev client, state graph, catalog/order tools, reply check, Intron STT for voice notes, and trace/speech migrations.
- Docs retargeted to Meta Muse models and Intron Sahara speech.
- Added benchmark plan (`docs/benchmark.md`) with all results left as `TBD`.
- Tests: 51 passing. Lint/format clean.
- Remaining before live demo: apply Supabase migrations `0002` and `0003`, create private storage bucket, confirm TypeSafe schema and Intron STT URL.

## 2026-10-26 (earlier)

- Merged PR #2: catalog photo flow.
- Merged PR #1: foundation (webhook verify, echo, CI, branch protection).

# Demo / QA test accounts (local + Meta Dev mode)

Use these for live Instagram Login + DM proof. App is **Sell-Safe** (Development / Testers).

## Roles

| Role | Instagram handle | Notes |
|------|------------------|--------|
| **Connected shop (seller)** | `sellsafe.testshop.ng` | Connect via website OAuth. Catalog + payment automation runs here. |
| **Buyer (primary)** | `testicles22` | Must be an accepted **Instagram Tester** on the Meta app or webhooks/replies may not fire in Dev mode. |
| **Buyer (worked previously)** | `divine_yg` | Cousin account — received auto-reply after webhook subscribe. |
| **Official Sell-Safe page** | `sellsafe.ng` (ids in `SELLSAFE_OFFICIAL_IG_ACCOUNT_IDS`) | Connect/marketing reply only — no catalog prices or payment flow. |

## Seller checklist before DM retest

1. Open Connect URL (public web tunnel) → Connect as **`sellsafe.testshop.ng`**.
2. Dashboard → **Settings** (`/dashboard?tab=settings`) → save **bank name, account name, account number**.
3. Meta App → Instagram Login:
   - OAuth redirect + deauthorize + privacy URLs → current **API** tunnel host.
   - Webhook callback → `https://<API_TUNNEL>/webhooks/instagram` + `META_VERIFY_TOKEN`.
   - Confirm shop account is **subscribed** to message webhooks (`me/subscribed_apps`).
4. Buyer DMs shop → expect auto-reply; “account number” → payout details from Settings.

## Local stack (tunnel demo “deploy”) — 2026-11-03 session

| Process | Port | Public (this session) |
|---------|------|--------|
| FastAPI | `127.0.0.1:8002` | `https://spam-thorough-chosen-puts.trycloudflare.com` |
| Next.js `web/` | `127.0.0.1:3000` | `https://telephony-carrier-occupations-matters.trycloudflare.com` |
| Next → API | `web/.env.local` | `API_BASE_URL=http://127.0.0.1:8002` |

**Connect:** `https://telephony-carrier-occupations-matters.trycloudflare.com/?platform=instagram`  
**Meta redirect:** `https://spam-thorough-chosen-puts.trycloudflare.com/api/instagram/oauth/callback`  
**Meta webhook:** `https://spam-thorough-chosen-puts.trycloudflare.com/webhooks/instagram`

Stable host deploy (Render/Railway API + Vercel web) is still open — see `docs/architecture.md` and CHANGELOG 2026-11-03.

## Playwright / browser smoke (agent)

- Landing `/` and `/?platform=instagram`
- Connect CTA → OAuth start (307 to Instagram)
- After Connect: `/dashboard`, Settings shop + payout fields visible
- Inbox Refresh does not invent stub buyers

Do **not** commit tokens, cookies, or `.tmp/ig_sessions.json`.

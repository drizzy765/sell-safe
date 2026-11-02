# backend/app/api/internal

Internal routes (require `X-Internal-Token` unless noted):

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/jobs/recheck` | Payment recheck + cancel after reminders |
| POST | `/jobs/reminders` | Buyer reminders (max 2) |
| POST | `/jobs/daily-summary` | Seller daily summary push |
| GET | `/sellers/{id}/summary?date=` | Summary JSON for a WAT date |
| POST | `/api/waitlist` | Add phone to WhatsApp waitlist (public, 201 or 409) |
| POST | `/api/waitlist/notify` | Notify waitlist entry (501 stub) |
| GET | `/api/instagram/status` | Seller session status (`connected`, `username`). Header `X-IG-Session` or cookie. No tokens |
| GET | `/api/instagram/oauth/start` | Returns Instagram authorize URL (+ CSRF state). `force_reauth` default true |
| POST | `/api/instagram/oauth/exchange` | Exchange `{code,state}` → opaque `session_id` (server holds token) |
| GET | `/api/instagram/oauth/callback` | Optional FastAPI redirect callback (needs `WEB_BASE_URL`) |
| POST | `/api/instagram/disconnect` | Drop seller Instagram session |
| GET | `/api/onboarding/shop` | Feature 1: fetch/create shop from IG session (`X-IG-Session`) |
| PATCH | `/api/onboarding/shop` | Feature 1: save shop fields; `confirm=true` → catalog next |
| GET | `/api/onboarding/catalog/media` | Feature 2A: recent IG posts for import |
| POST | `/api/onboarding/catalog/import/instagram` | Feature 2A: draft selected media ids |
| POST | `/api/onboarding/catalog/import/upload` | Feature 2B: draft uploaded images (base64) |
| POST | `/api/onboarding/catalog/import/drive` | Drive folder import (`GOOGLE_DRIVE_API_KEY`; `Name - NGN price.jpg`) |
| GET | `/api/onboarding/catalog/drafts` | Feature 2 review list |
| PATCH/DELETE | `/api/onboarding/catalog/drafts/{id}` | Edit or delete a draft |
| POST | `/api/onboarding/catalog/drafts/approve` | Approve drafts into buyer catalog |
| GET | `/api/onboarding/catalog/products` | Approved products for the shop |
| GET | `/api/onboarding/catalog/shelf` | Shop media shelf |
| GET | `/api/dashboard/summary` | Dashboard v2 summary (real inbox; demo opt-in) |
| GET | `/api/dashboard/inbox` | Real Instagram conversations |
| GET | `/api/dashboard/inbox/{buyer_id}` | Thread messages + drafts |
| POST | `/api/dashboard/inbox/{buyer_id}/takeover` | Pause / hand back AI |
| POST | `/api/dashboard/inbox/{buyer_id}/send` | Seller manual reply |
| POST | `/api/dashboard/drafts/{id}/approve\|reject\|edit` | APPROVE-mode draft actions |
| PATCH | `/api/dashboard/settings` | reply_mode, demo_mode, threshold |
| POST | `/api/sellers/crypto-wallet` | Save checksummed seller USDC wallet (optional onboarding) |
| GET | `/api/demo/crypto` | Live Base Sepolia: real / reused / fake hash verdicts (`DEMO_REAL_TX_HASH`) |
| * | `/orders/...` | Order release helpers |

Seller chat `/fake` / `/notfake` writes `fraud_signals` (hashed only); verify loads confirmed signals for R6.

## WhatsApp Waitlist

### POST /api/waitlist (Public)

Add a seller's WhatsApp number to the waitlist. We'll notify them when WhatsApp becomes available.

**Request:**
```json
{
  "phone_number": "+2348012345678"
}
```

**Response (201):**
```json
{
  "message": "We'll message you on WhatsApp when ready",
  "phone_number": "+2348012345678"
}
```

**Validation:**
- Must be Nigerian format: `+234XXXXXXXXXX`
- Must be unique (returns 409 if already registered)
- Stored in `whatsapp_waitlist`

### POST /api/waitlist/notify (501 Not Implemented)

Send WhatsApp notification to a waitlist entry. Stub for when WhatsApp unblocks.

**Status:** 501 - Will be implemented when WhatsApp becomes available.

## Why WhatsApp Number Not Email

Nigerian sellers live on WhatsApp. When WhatsApp unblocks, we message them where they already are, with a one-tap connect link.

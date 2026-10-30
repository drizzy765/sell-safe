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
| GET | `/api/instagram/status` | Public boolean: Instagram Login is configured. No token or id |
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

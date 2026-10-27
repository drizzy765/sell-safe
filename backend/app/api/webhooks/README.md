# backend/app/api/webhooks

Webhook routes. Verify signature on raw body, dedupe on `external_msg_id`, return 200 fast, process async. See `docs/api_spec.md`.

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/webhooks/meta` | Shared Meta verify handshake (`hub.verify_token`) |
| POST | `/webhooks/whatsapp` | WhatsApp Cloud → `WhatsAppAdapter` → graph / listing / voice / verify |
| POST | `/webhooks/instagram` | IG Messaging → `InstagramAdapter` → same handlers, `channel="instagram"` |
| POST | `/webhooks/paystack` | Virtual-account / transfer webhooks |
| POST | `/webhooks/flutterwave` | Same payment path |
| POST | `/webhooks/alerts/email` | Forwarded bank-alert email → match open orders |

Messenger adapter is not wired yet (Phase 8 stretch).

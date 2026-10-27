# backend/app/channels/instagram

Instagram Messaging adapter (IG Business/Professional account linked to a Facebook Page).

## Contract

`InstagramAdapter` implements `ChannelAdapter`:

- `verify_signature` — HMAC-SHA256 of the raw body with `META_APP_SECRET` (`X-Hub-Signature-256`)
- `parse` — Messenger-style `object: "instagram"` / `entry[].messaging[]` into `InboundMessage`
- `send_text` — Graph API `POST /{FB_PAGE_ID}/messages` with `FB_PAGE_ACCESS_TOKEN`
- `fetch_media` — GET attachment CDN URL (or Graph media id when present)

## Env

| Variable | Role |
| --- | --- |
| `META_APP_SECRET` | Webhook signature |
| `META_VERIFY_TOKEN` | Shared with `GET /webhooks/meta` |
| `INSTAGRAM_ACCOUNT_ID` | Seller channel id for `ensure_seller` |
| `FB_PAGE_ID` | Send endpoint page id (falls back to IG account id) |
| `FB_PAGE_ACCESS_TOKEN` | Graph send + media download |
| `GRAPH_API_VERSION` | e.g. `v21.0` |

Live Page ↔ IG linking is a human setup step; CI uses fixtures + `httpx.MockTransport`.

## Audio

Inbound `attachments[].type == "audio"` becomes `InboundMessage(type="audio")`. The webhook routes those through `handle_voice_note` (Intron STT → graph), same as WhatsApp. TTS replies are out of scope.

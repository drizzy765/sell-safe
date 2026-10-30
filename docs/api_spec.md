# API Spec
Base: `https://<host>`. JSON. Internal endpoints require `Authorization: Bearer $INTERNAL_API_TOKEN` (dashboard uses Supabase session → server checks seller).

## Webhooks (public)
| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/webhooks/meta` | Meta verify handshake: echo `hub.challenge` if `hub.verify_token == META_VERIFY_TOKEN` | token |
| POST | `/webhooks/whatsapp` | WhatsApp Cloud API messages/statuses | `X-Hub-Signature-256` |
| POST | `/webhooks/instagram` | IG messaging | same |
| POST | `/webhooks/messenger` | Messenger | same |
| POST | `/webhooks/paystack` | `charge.success`, DVA events | `x-paystack-signature` |
| POST | `/webhooks/flutterwave` | `charge.completed` | `verif-hash` |
| (DM text) | Instagram / WhatsApp inbound | Buyer pastes `0x` tx hash → on-chain USDC check | channel signature |
| POST | `/webhooks/alerts/email` | inbound email of forwarded bank alerts (e.g. via email-forwarding service) | shared secret |
Rules: respond `200` within 2 s, process async (background task/queue); dedupe by event/message id.

## Internal
| Method | Path | Body / Query | Response |
|---|---|---|---|
| GET | `/health` | – | `{status:"ok", provider:"groq"}` |
| GET | `/privacy` | – | HTML privacy policy |
| POST | `/sellers` | `{name, business_name, whatsapp_id, language}` | seller |
| GET | `/sellers/{id}/products` | `?q=` | products[] |
| POST | `/sellers/{id}/products` | product | product |
| PATCH | `/products/{id}` | partial | product |
| GET | `/sellers/{id}/orders` | `?status=` | orders[] |
| GET | `/orders/{ref}` | – | order + payments + latest verdict |
| POST | `/orders/{ref}/release` | `{confirm:true}` | order (status released) – 409 if verdict not release_allowed and no override |
| POST | `/payments/{id}/verify` | `{evidence_id?}` | verdict |
| POST | `/api/sellers/crypto-wallet` | `{address}` checksummed EVM | `{address, network}` (optional onboarding; "Do this later" allowed) |
| GET | `/api/demo/crypto` | – | live `{ready, cases:[real, reused, fake]}` from `DEMO_REAL_TX_HASH` (or a clear message if unset) |
| POST | `/alerts/sms` | `{seller_id, text, received_at}` (from Android forwarder) | evidence |
| POST | `/fraud/report` | `{evidence_id, kind}` | signal |
| GET | `/sellers/{id}/summary` | `?date=` | `{orders, paid_kobo, fakes_caught, naira_saved_kobo}` |
| POST | `/jobs/daily-summary` | cron | `{sent}` |
| POST | `/jobs/reminders` | cron | `{sent}` |

## Speech (outbound, not a public route)
Buyer audio is transcribed inside the webhook worker. There is no inbound Intron webhook.

| Call | URL | Auth | Notes |
|---|---|---|---|
| STT | **TODO verify** against the Intron STT reference | `Authorization: Bearer $INTRON_API_KEY` | Sahara v2.5. Language `yo`, `pcm`, `en`; stretch `ig`, `ha`. Codes: [supported languages](https://docs.voice.intron.io/docs/stt/supported-languages). |
| TTS | `POST https://infer.voice.intron.io/tts/v1/generate` | same | JSON `text`, `voice_language`, `voice_accent`, `voice_gender`, optional `output_audio_format` (`wav` or `opus`). Max 4096 characters. 30 requests/minute. `503` returns a text id to poll ([TTS status](https://docs.voice.intron.io/docs/tts/tts-status)), not a second generate. Spec: [TTS generate](https://docs.voice.intron.io/docs/tts/tts-generate). |

The accents list includes Yoruba and Pidgin (checked 2026-10-26). Treat that as unverified until a live call succeeds (**TODO verify**). On rejection, retry the same text with `voice_language=en` and `voice_accent=yoruba`. Persisted message fields: `transcript`, `language`, `asr_confidence` (`data_model.md`).

## Verdict object
```json
{"payment_id":"…","order_ref":"SS-1042","verdict":"SUSPICIOUS","confidence":0.12,
 "release_allowed":false,"reasons":["Amount on receipt ₦25,000 but order is ₦15,000","Reference used before"],
 "rule_hits":["R1","R4"],"evidence":[{"type":"screenshot","trust_level":1}],
 "jev_scores":{"p_match":0.08,"p_tamper":0.87}}
```
Errors: `{error:{code, message}}` with 400/401/404/409/422/500.

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
| POST | `/webhooks/alerts/email` | inbound email of forwarded bank alerts (e.g. via email-forwarding service) | shared secret |
Rules: respond `200` within 2 s, process async (background task/queue); dedupe by event/message id.

## Internal
| Method | Path | Body / Query | Response |
|---|---|---|---|
| GET | `/health` | – | `{status:"ok", provider:"groq"}` |
| POST | `/sellers` | `{name, business_name, whatsapp_id, language}` | seller |
| GET | `/sellers/{id}/products` | `?q=` | products[] |
| POST | `/sellers/{id}/products` | product | product |
| PATCH | `/products/{id}` | partial | product |
| GET | `/sellers/{id}/orders` | `?status=` | orders[] |
| GET | `/orders/{ref}` | – | order + payments + latest verdict |
| POST | `/orders/{ref}/release` | `{confirm:true}` | order (status released) – 409 if verdict not release_allowed and no override |
| POST | `/payments/{id}/verify` | `{evidence_id?}` | verdict |
| POST | `/payments/{id}/crypto` | `{tx_hash, chain}` | verdict |
| POST | `/alerts/sms` | `{seller_id, text, received_at}` (from Android forwarder) | evidence |
| POST | `/fraud/report` | `{evidence_id, kind}` | signal |
| GET | `/sellers/{id}/summary` | `?date=` | `{orders, paid_kobo, fakes_caught, naira_saved_kobo}` |
| POST | `/jobs/daily-summary` | cron | `{sent}` |
| POST | `/jobs/reminders` | cron | `{sent}` |

## Verdict object
```json
{"payment_id":"…","order_ref":"SS-1042","verdict":"SUSPICIOUS","confidence":0.12,
 "release_allowed":false,"reasons":["Amount on receipt ₦25,000 but order is ₦15,000","Reference used before"],
 "rule_hits":["R1","R4"],"evidence":[{"type":"screenshot","trust_level":1}],
 "jev_scores":{"p_match":0.08,"p_tamper":0.87}}
```
Errors: `{error:{code, message}}` with 400/401/404/409/422/500.

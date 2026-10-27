# backend/app/jobs

Scheduled jobs (internal token via `X-Internal-Token`):

| Route | Module | Role |
| --- | --- | --- |
| `POST /jobs/recheck` | `recheck.py` | Re-evaluate pending payments; cancel after max reminders |
| `POST /jobs/reminders` | `reminders.py` | Buyer payment reminders (max 2, spaced after the recheck window) |
| `POST /jobs/daily-summary` | `daily_summary.py` | WAT-day rollup + WhatsApp seller summary (`naira_saved_kobo`) |

Fraud memory lookups are passed into recheck via `FraudStore` so R6 applies during re-evaluation.

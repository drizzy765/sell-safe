# backend/app/api/internal

Internal routes (require `X-Internal-Token` unless noted):

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/jobs/recheck` | Payment recheck + cancel after reminders |
| POST | `/jobs/reminders` | Buyer reminders (max 2) |
| POST | `/jobs/daily-summary` | Seller daily summary push |
| GET | `/sellers/{id}/summary?date=` | Summary JSON for a WAT date |
| * | `/orders/...` | Order release helpers |

Seller chat `/fake` / `/notfake` writes `fraud_signals` (hashed only); verify loads confirmed signals for R6.

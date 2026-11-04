# Benchmark — Meta-facing summary

Measured results for the Meta submission. Depth lives in
[`benchmark_muse.md`](benchmark_muse.md) (Muse model bench, today's
submission) and [`benchmark_micro1.md`](benchmark_micro1.md) (full eval
plan + results pack for the micro1 hackathon, with LaTeX twin
`benchmark_micro1.tex`).

**Headline:** on the 20-case payment-verification suite, Sell-Safe
confirmed **zero** fake receipts. The LLM never decides a payment
verdict — deterministic rules + evidence matching do
(`backend/app/verification/verdict.py`).

## Measured (2026-11-04, git `c851352`)

- Payments v1 (`python -m evals.run --suite payments --dataset v1`):
  **20/20 passed, false CONFIRMED = 0**; confusion matrix diagonal
  (CONFIRMED 5, NOT_FOUND 4, SUSPICIOUS 7, UNVERIFIED 4). Report:
  `evals/reports/2026-11-04-payments-c851352.md`.
- Chat-path unit bench: 14 tests (price flow, pidgin catalog browse,
  payment-details bypass, Groq fallback, receipt extraction, dashboard
  verdict stats).
- Live Instagram (test shop, Render): pidgin voice note transcribed and
  answered in pidgin; pidgin catalog browse returned real prices;
  account-number ask returned saved payout deterministically; generated
  fake receipt was not confirmed.

## Claims

| ID | Claim | Status |
|---|---|---|
| C1 | Fake/edited payment never `CONFIRMED` | **PASS** — 20/20, false CONFIRMED 0 |
| C2 | Matched webhook evidence is `CONFIRMED` | PASS (synthetic); live webhook pending |
| C3 | Screenshot alone never sets `release_allowed` | **PASS** — measured |
| C4 | Pidgin/Yoruba code-switching in chat + voice | Pidgin live PASS; Yoruba unit PASS, live pending |
| C5 | Full buyer journey, DB rows match goal | Live flow PASS; unit journey PASS |
| C6 | Prompt injection cannot force policy violation | **PASS** — 6/6 blocked |
| C7 | Muse vision catalog fields match labels | PARTIAL — 1/4 exact, 0 confident-wrong (n=4) |
| C8 | Routing by intent + language | PASS (unit, 3 languages) |

## Method in brief

Tiered data (A real consented / B public / C synthetic), never pooled.
Headline failures reported next to accuracy: false-confirm rate (vision),
amount-error rate (voice), unverified-confirm rate (chat). "Can't
confirm, check your bank app" is a safe abstention; a false confirm is
catastrophic. Full methodology: [`benchmark_micro1.md`](benchmark_micro1.md).

## Not in this submission

Tier A consented datasets, 50+ case expansion, C7 at scale, calibration —
all scoped in the micro1 plan. No number in this file is a target
presented as a result.

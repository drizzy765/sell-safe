# Testing & Evals

## Unit tests (`tests/unit`)
- Signature verification: Meta (SHA-256), Paystack (SHA-512), Flutterwave hash – valid/invalid/raw-body edge cases.
- Channel `parse()` for each fixture payload (text, image, audio, status update).
- Rules R1–R9 with table-driven cases; matcher tolerance and time windows.
- Verdict table: every row in `payment_verification.md` has a test.
- Kobo math, order totals, order-ref generation.

## Integration tests (`tests/integration`, mocked LLM/Jev via `FakeProvider`)
- Webhook → message stored → reply sent (httpx mock).
- Order flow end-to-end; duplicate message id processed once.
- Paystack webhook before/after screenshot → CONFIRMED either way.
- Release endpoint returns 409 without release_allowed.
Live tests marked `@pytest.mark.live` (real Groq/Meta/Jev), run manually.

## Eval sets (`evals/`)
### 1. Fake-vs-real screenshot set (synthetic only)
| Class | Count (target) | How to make |
|---|---|---|
| real | 20 | Own small test transfers between own accounts; redact names/acct to fake values before saving |
| edited_amount | 10 | Change amount in an image editor |
| edited_name/recipient | 10 | Swap recipient name/last4 |
| reused | 5 | Same real image reused for a second order |
| generated_fake | 5 | Mock "fake alert app"-style receipts made from HTML templates (`evals/gen_receipts.py`) |
| pending_status | 5 | Receipts showing "pending" |
| not_a_receipt | 5 | Product photos, memes |
Each has `labels.jsonl`: `{file, class, expected_verdict, amount_kobo, reference, order_fixture}`. Keep any real-derived images in `evals/data/private/` (gitignored).

### 2. Message set
100 messages (≈35 en, 35 pcm, 30 yo) labelled intent + language; include scam-pressure lines ("send goods first, I'm in traffic").

### 3. Mock evidence
`evals/fixtures/paystack_events/*.json`, `bank_alerts.txt` (GTB/Access/Opay-style formats, fictional), `chain_txs.json`.

## Metrics & gates
| Metric | Gate |
|---|---|
| False CONFIRMED on any fake | **0 (launch blocker)** |
| Fake caught (SUSPICIOUS/NOT FOUND/UNVERIFIED) | 100% |
| Real with webhook → CONFIRMED | ≥ 95% |
| Extraction amount accuracy | ≥ 95% |
| Intent accuracy | ≥ 90% |
| Language accuracy | ≥ 90% |
| p50 reply latency | < 4 s |
Run: `python -m evals.run --provider groq` and `--provider meta`; output `evals/report.md` (confusion matrix) – include a screenshot in the write-up. Report numbers as measured on this synthetic set only; don't generalize.

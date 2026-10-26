# evals

Claim-level evaluation for Sell-Safe. The plan, metrics, and the empty results template are in `docs/benchmark.md`. Fixture construction and unit-test gates are in `docs/testing_and_evals.md`.

No suite has been run. Every number in the benchmark stays `TBD` until a report under `reports/` exists. Do not commit customer receipts, real account numbers, or voice notes from people. Those files belong in `data/private/`, which is gitignored.

## Layout

```
evals/
  README.md
  run.py                      # entry point: python -m evals.run (not written yet)
  prompts/VERSION             # bumped when a prompt used by a suite changes
  datasets/
    payments/v1/              # screenshots, alert and webhook cases; labels.jsonl
    conversations/v1/         # tau-bench-style buyer goals; tasks.jsonl
    routing/v1/               # intent and language labels; messages.jsonl
    speech/v1/                # manifest.jsonl only; audio in data/private/
    catalog/v1/               # photo field labels; labels.jsonl
    safety/v1/                # injection, social-engineering, scam patterns
  fixtures/                   # Paystack events, fictional bank alerts, chain txs
  data/synthetic/             # generated receipts safe to commit
  data/private/               # gitignored
  reports/                    # one file per run: YYYY-MM-DD-<suite>-<sha>.md
```

`v1` is locked at the 2 Nov feature freeze. A later edit is `v2`. Reports name the folder they used.

## Suites

| Folder | What it measures | Grader |
|---|---|---|
| `datasets/payments` | Verdict precision and recall, false-`CONFIRMED` (target 0), Jev calibration, escalation rate | expected verdict and `release_allowed` |
| `datasets/conversations` | Buyer goals in English, Pidgin, and Yoruba. Report pass^1 and pass^4, not pass@k | final order and payment rows, plus policy checks |
| `datasets/routing` | Jev intent and language | accuracy, macro-F1, confusion matrix |
| `datasets/speech` | Intron Sahara STT on recorded Yoruba-English and Pidgin-English notes | WER, CER, latency |
| `datasets/catalog` | Muse vision fields on product photos | exact field match |
| `datasets/safety` | Prompt injection, "release goods first", scam pressure | end state must not release or confirm |

## Rerun

```
python -m evals.run --suite payments --dataset v1 --seed <seed>
python -m evals.run --suite conversations --dataset v1 --seed <seed> --trials 4
```

The command is the contract. The runner is not in the tree yet. A citable run records the git SHA, dataset version, seed, model ids, and prompt version in the report header, using the system card in `docs/benchmark.md`.

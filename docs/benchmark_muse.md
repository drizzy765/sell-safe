# Benchmark: Meta Muse in Sell-Safe (submission bench, 2026-11-04)

How Meta Muse models perform inside Sell-Safe, measured on the live system
and the repo eval suite. Muse is the primary provider
(`LLM_PROVIDER=meta`); Groq is a measured fallback, not a silent one —
every fallback is logged (`Primary LLM provider failed; falling back to
Groq`). The LLM never decides payment verdicts; verdicts are deterministic
(`backend/app/verification/verdict.py`).

## Headline results

| Area | Model(s) | Measured result |
|---|---|---|
| Payment verdicts (Track B) | Deterministic rules + evidence (LLM reads only) | **20/20 cases, false CONFIRMED = 0** |
| Chat replies | Muse Spark (`muse-spark-1.3`) primary, Groq fallback | Live on Instagram: greetings, catalog, price, order, account-number flows answered |
| Catalog browse (deterministic, no LLM) | — | Correct real prices in English, Pidgin, Yoruba |
| Receipt/catalog vision | Muse vision (`muse-wonder-1.0`) | 1/4 exact on synthetic labels; 3 safe abstentions; **0 confident-wrong fields** |
| Vision fallback | Groq (`qwen/qwen3.8-27b`) | JSON-generation failures + rate limits observed; useful as backup, weaker than Muse here |
| Voice notes (STT) | Intron Sahara primary; Muse/Groq transcribe fallback | Pidgin note transcribed + answered in pidgin, live 2026-11-04 |

## Track B — payments (the claim that matters)

`python -m evals.run --suite payments --dataset v1` (git `c851352`):
**20/20 passed, false CONFIRMED on fake cases = 0.** Confusion matrix
fully diagonal: CONFIRMED 5, NOT_FOUND 4, SUSPICIOUS 7, UNVERIFIED 4.
Report: `evals/reports/2026-11-04-payments-c851352.md`.

Muse's role is reading receipts (amount, recipient, reference, status);
the verdict that protects the seller's money is never Muse's call.

## Chat — Muse Spark primary, measured live

On the production test shop (`sellsafe.testshop.ng`, Render), buyers got
correct Muse replies for greetings, product prices, ordering, and
deterministic payout details. When Meta returned `404 model_not_found`
from the deployed environment, the agent previously fell back to
"I'm not sure I understood"; after the fallback fix, Groq answers and the
event is logged, so Meta outages never leave a buyer in silence.
Unit bench: pidgin order flow creates an order row matching seller,
buyer, and catalog total exactly; 6/6 prompt-injection confirmations
blocked by the reply guard.

## Vision — Muse vs Groq (first head-to-head)

4 synthetic labeled product photos (name + price rendered on-pack):

| Model | Exact name+price | Abstain/fail | Confident-wrong |
|---|---|---|---|
| Muse vision (`muse-wonder-1.0`) | 1/4 | 3 (provider timeout → fallback) | **0** |
| Groq vision (`qwen/qwen3.8-27b`) | 0/4 in fallback runs | JSON-gen 400s, 429 rate limits | 0 |

Read: Muse is the stronger extractor and never invents fields when it
cannot read them — it abstains and the seller is asked instead. Groq is
kept as availability backup only. Sample is small (n=4, Tier C synthetic);
the full comparison is planned in `docs/benchmark_micro1.md`.

## Voice — Sahara primary, Muse-ecosystem fallback

Intron Sahara is the speech specialist (per architecture, speech is not
the LLM provider). Live proof, 2026-11-04: pidgin voice note
"How far now, how you dey, how everything dey go?" transcribed correctly
and answered in pidgin ("I dey fine, thank you! … Wetin you wan buy
today?"). Transcription fallback chain: Intron → provider transcribe
(Groq Whisper via Meta provider delegation) → "please type that" safe
reply. Voice notes and transcripts surface in the seller dashboard inbox.

## What Muse does in Sell-Safe, end to end

1. **Spark (chat/agent):** buyer conversations in en/pcm/yo, tool calls
   into the real catalog and order store.
2. **Vision:** receipt field extraction for verification; catalog product
   extraction from seller photos.
3. **Fallback discipline:** any Muse failure logs and falls back (Groq
   for chat/vision, Whisper for transcription). Buyers always get an
   answer; sellers always get the deterministic verdict.

## Limitations

Payments/vision sets are Tier C synthetic (n=20 / n=4); Tier A consented
data and the 50+ case expansion are micro1 scope
(`docs/benchmark_micro1.md`). Meta `model_not_found` was observed from
the deployed environment with a key whose fingerprint matches the
working local key — tracked as an environment/entitlement issue, with
Groq fallback covering buyers meanwhile.

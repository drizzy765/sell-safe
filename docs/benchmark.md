# Benchmark and Evaluation Plan

**Last Updated:** 31 Oct 2026  
**Version:** 2.0 (SautiCivic-inspired improvements)

## Overall Plan

1. **Website redesign next** (`docs/design/website-design-plan.md`). Don't break payments/chat.
2. **SellSafe-Bench in parallel / after redesign starts** — best-effort for Meta. **Partial is OK.** If time is short, do **not** ship a full bench for Meta submit; keep using measured `evals/report.md` headlines only. Full bench remains the main path for **micro1** (after Meta deadline if needed).
3. **Demo video is last** before Meta Indie submit (after redesign + deploy).
4. **TrustLock (AI escrow on NEAR)** is a different repo. Don't touch it here.

**Priority vs Meta deadline:** redesign + demo video required before submit; full SellSafe-Bench is optional for Meta.

---

## Lessons from SautiCivic Bridge (Spyder Team, Intron Sahara CodeSwitch Challenge 2026)

SautiCivic taught us that **accuracy hides headline failures**. Their model achieved good WER but catastrophically failed on "don" vs "don't" in civic contexts. We apply these lessons:

### Lesson 1: Report the Headline Failure Rate
Accuracy metrics can mask catastrophic errors. We report the specific failure mode that matters for fraud prevention:

- **Track B (Vision):** The **FALSE-CONFIRM RATE** — a model reads every field correctly but still calls an edited/fake receipt genuine. Reported next to field accuracy.
- **Track C (Voice):** The **AMOUNT-ERROR RATE** — naira amounts misheard ("25k" vs "2.5k", "fifteen" vs "fifty"). Reported next to WER.
- **Track A (Chat):** The **UNVERIFIED-CONFIRM RATE** — the agent confirms a payment it hasn't actually verified.

### Lesson 2: Tiered Data, Reported Separately, Never Pooled
SautiCivic's tiered approach prevents confounding real-world performance with synthetic benchmarks. We follow this strictly:

| Tier | Description | Examples |
|------|-------------|----------|
| **Tier A** | Real consented in-domain data | Genuine transfer receipts donated by vendors and friends; WhatsApp/Instagram vendor chats exported with both sides' consent; consented voice recordings of vendor-style orders |
| **Tier B** | Public out-of-domain data | AfriSpeech-200, AfriSwitch, FLEURS (Hausa/Yoruba) for voice; public receipt templates if any |
| **Tier C** | Synthetic and adversarial | Fakes made by editing copies of donated receipts; scam chats; 10+ trap cases based on public fake-alert patterns (EFCC/CBN warnings, news reports, paraphrased public posts) |

**Critical:** Report metrics per tier. Never pool Tier A (real) with Tier C (synthetic).  
**Replication:** Test Track B on banks/apps that are NOT in the dev set.

### Lesson 3: Ethics for Real Data
SautiCivic pioneered consented-speaker datasets. We adopt their method:

- **DATA_CONSENT_LOG.md** documenting purpose, retention, and right to withdraw for every Tier A item
- **Redaction:** Names, account numbers, phone numbers replaced with fake values in the same font
- **Pseudonymization:** VENDOR-01, CUST-07, SPK-xx
- **Repository hygiene:** Raw files private and out of git; publish only fully redacted data

### Lesson 4: Safety Scoring
"Can't confirm, check your bank app" is a **SAFE abstention**. A false confirm is **CATASTROPHIC**. We report:
- Unsafe-confirm escape rate (false confirm)
- Correct abstentions (legitimate uncertainty)
- False abstentions (unnecessary uncertainty)

### Lesson 5: Better Than SautiCivic
We improve on their methodology:

| Improvement | SautiCivic | SellSafe-Bench |
|-------------|------------|----------------|
| Labellers | Single labeller | **2+ labellers with Cohen's kappa** |
| Visualizations | Tables only | **Tables + charts** (leaderboard bars, confusion matrices, cost vs accuracy plots) |
| Calibration | ECE 30.9% reported | **ECE measured + improvement target** |
| Balance | Uncontrolled | **Balanced across banks/speakers** |
| Cost tracking | Not reported | **₦ or $ per 1,000 receipts** per model |

### Lesson 6: Reproducibility Standards
- SHA-256 manifests for all inputs
- Identical inputs for every model
- Raw outputs never edited
- Frozen results hash
- pytest suite
- One-command rerun
- Explicit Limitations section

### Lesson 7: Voice Track Reuse
We reuse the SautiCivic runners and consented-speaker method for Sahara and Whisper baselines, using the published dataset: [drizzy765/sauticivic-tier-a-recorded](https://huggingface.co/datasets/drizzy765/sauticivic-tier-a-recorded)

---

## micro1 Eval Hackathon Instructions

- **Platform:** Run by micro1, powered by HackerRank. Everything is done through one HackerRank test link.
- **Window:** Oct 30, 2026 12:15 AM PDT to Nov 8, 2026 9:15 PM PST (Nov 9, 6:15 AM Lagos time).
- **Process:** You can log in any time during the window and upload responses with the same link.
- **Critical:** Upload ALL responses before pressing Submit. Submit is FINAL and locks the test link.
- **Plan:** Target finishing by Nov 7, and Timi presses Submit himself after review.
- **Official Task Brief:** (To be pasted from HackerRank test page when available)

---

## Meta Deadline

- **Sell-Safe submission due:** Nov 5, 02:00 WAT
- **Benchmark report must be ready by:** Nov 4

---

## Benchmark Tracks

### A. Chat Agent

**Scope:** 60–100 realistic Nigerian commerce chats in English and Pidgin, covering:
- Haggling and negotiation
- Stock inquiries
- Policy questions
- Payment-confirmation traps

**Grading:**
- Rubric-based evaluation
- LLM judge for consistency
- **2+ human labellers with Cohen's kappa** on subset

**Metrics:**
- Task completion rate (pass@1 and pass@4)
- Policy adherence rate
- Language appropriateness
- Response relevance
- **UNVERIFIED-CONFIRM RATE** (headline failure: agent confirms without verification)

### B. Fake Receipt Vision (HEADLINE Track)

**Scope:** Synthetic dataset of genuine and edited/fake Nigerian bank transfer receipts and alerts. **No real people's data.**

**Labels per receipt:**
- Amount
- Sender
- Recipient
- Bank
- Reference
- Date
- Real/fake classification

**Systems Compared:**
1. **Muse vision** (Meta Model API) - primary
2. **OCR + Rules:** Tesseract, PaddleOCR or EasyOCR (optionally Google Vision)
3. **Vision LLM:** Gemma or Llama vision

**Metrics:**
- Field exact match (amount, sender, recipient, bank, reference, date)
- Fake-detection precision/recall/F1
- **FALSE-CONFIRM RATE** (headline failure: correct fields, wrong verdict)
- Latency (p50, p95)
- **Cost per 1,000 receipts** (₦ or $)
- **Calibration (ECE)**

**Safety Scoring:**
- Unsafe-confirm escape rate
- Correct abstentions
- False abstentions

### C. Voice (Bonus Pilot)

**Scope:** Nigerian-accented speech using AfriSpeech-200 or team recordings. Reuse SautiCivic method and [drizzy765/sauticivic-tier-a-recorded](https://huggingface.co/datasets/drizzy765/sauticivic-tier-a-recorded) for baselines.

**Systems Compared:**
1. **Muse voice** (if Meta Model API supports speech-to-text)
2. **Intron Sahara** (Sahara API)
3. **Whisper**

**Metrics:**
- Word Error Rate (WER)
- **AMOUNT-ERROR RATE** (headline failure: "25k" vs "2.5k", "fifteen" vs "fifty")
- Character Error Rate (CER)
- Latency (p50, p95)

**Note:** First confirm the Meta Model API has speech-to-text. If it doesn't, mark this as future work and don't fake results.

---

## Project Structure

```
bench/
├── datasets/                    # JSONL format
│   ├── tier-a/                  # Real consented data
│   ├── tier-b/                  # Public out-of-domain
│   ├── tier-c/                  # Synthetic and adversarial
│   ├── chat_agent/
│   ├── fake_receipt/
│   └── voice/
├── runners/                     # Execution scripts
├── graders/                     # Evaluation logic
├── results/                     # Raw outputs
├── report/                      # Final deliverables
│   ├── figures/                 # Charts and visualizations
│   └── tables/                  # Leaderboards and metrics
└── DATA_CONSENT_LOG.md          # Ethics documentation
```

---

## Schedule

| Dates | Focus | Deliverables |
|-------|-------|--------------|
| **Nov 1** | Website redesign first | Landing T1–T11; don't break product |
| **Nov 1–3** | SellSafe-Bench (best-effort) | Partial datasets/runners OK; full tiers/charts/kappa only if ahead |
| **Nov 3–4** | Deploy + README, then **demo video last**, then Meta submit | `v0.1-demo` → video link → `v1.0-submission` |
| **Nov 5–7** | micro1 / full bench if Meta used partial | HackerRank responses; expand bench after Meta if needed |
| **Nov 8** | Buffer | Final micro1 review before Submit |

---

## Team Split

| Person | Responsibility |
|--------|---------------|
| **Timi** | AI/eval design, model selection, rubric design, calibration analysis |
| **David** | Backend, runners, infrastructure, SHA-256 manifests |
| **Paul** | Data collection, 2+ labeller coordination, metrics, charts (leaderboard bars, confusion matrices, cost vs accuracy), report writing |

---

## Report Outline

1. **Executive Summary** - Key findings at a glance
2. **Headline Failure Rates** - The metrics accuracy hides
3. **Leaderboard Tables** - Per-tier, never pooled
4. **Visualizations**
   - Leaderboard bar charts
   - Confusion matrices
   - Cost vs accuracy plots
   - Calibration curves (ECE)
5. **Detailed Metrics** - Per-track breakdowns
6. **Failure Examples** - Qualitative analysis of catastrophic errors
7. **Safety Scoring** - Abstention analysis
8. **Limitations** - Explicit threats to validity
9. **Conclusions** - Takeaways and recommendations

---

## Ethics and Privacy

### Data Tiers and Handling

| Tier | Handling | Repository Status |
|------|----------|-------------------|
| Tier A | DATA_CONSENT_LOG.md with purpose, retention, withdrawal rights | `evals/data/private/` (gitignored) |
| Tier B | Proper attribution per dataset license | `evals/data/synthetic/` with attribution |
| Tier C | Synthetic only, no PII | `evals/data/synthetic/` safe to commit |

### Redaction Standards
- Names → fake values in same font
- Account numbers → fake values
- Phone numbers → fake values
- Chat participants → VENDOR-01, CUST-07
- Speakers → SPK-xx

### Consent Documentation
Every Tier A item requires:
- Purpose of collection
- Retention period
- Right to withdraw procedure
- Contact for withdrawal

---

## Risks and Fallbacks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Meta Model API doesn't support speech-to-text | Medium | Mark voice track as future work; focus on chat and vision |
| Dataset creation takes longer than expected | Medium | Start with 60 chats minimum; expand if time allows |
| Human labelling delays | Low | Have 2+ raters identified before Nov 3; use LLM judge as backup |
| Rate limiting on APIs | Low | Cache responses; plan runs during off-peak hours |
| HackerRank brief differs from plan | Medium | Keep Nov 5–7 as adaptation buffer |
| ECE calibration poor | Low | Target < 15% ECE; report actual value honestly |

---

## Rules

1. **Keys only from `.env`** - Never commit `.env` or print secrets
2. **Honest numbers only** - No fabricated results
3. **Version everything** - Dataset versions, git SHAs, model IDs, SHA-256 manifests in system card
4. **Reproducible** - Every result must be reproducible from the codebase
5. **Tier separation** - Never pool Tier A with Tier C metrics
6. **Safety first** - False confirm is catastrophic; report headline failures prominently

---

## Reproducibility Checklist

- [ ] SHA-256 manifests for all inputs
- [ ] Identical inputs for every model
- [ ] Raw outputs never edited
- [ ] Frozen results hash
- [ ] pytest suite passes
- [ ] One-command rerun works: `python -m bench.run --suite all --tier a,b,c`
- [ ] System card complete with git SHA, model IDs, dataset versions
- [ ] Limitations section explicitly states threats to validity

---

## Original Benchmark Documentation

The detailed benchmark methodology from the original plan is preserved below for reference:

### How to Read a Result

- State the claim in one sentence a reader could falsify.
- Report `n`, the numerator, and the denominator next to any rate.
- Attach a 95% bootstrap percentile interval. Record the resample count in the system card.
- For conversation tasks, the reliability numbers are **pass^1** and **pass^k** with **k = 4**.
- Keep the harness, tools, prompts, and budgets identical when the only contrast is the model.
- Grade by the final database rows and the policy checks, not by whether the reply sounds helpful.

### Claims Table

| ID | Claim | Suite | What would falsify it | Status |
|---|---|---|---|---|
| C1 | Sell-Safe never marks a fake or edited payment `CONFIRMED` | payments | Any fake, edited, reused, generated, or non-receipt item with verdict `CONFIRMED` | TBD |
| C2 | A signature-checked Paystack webhook that matches the order is `CONFIRMED` | payments | A matched webhook case that is not `CONFIRMED` | TBD |
| C3 | A screenshot alone never sets `release_allowed` | payments | Any screenshot-only case with `release_allowed` true | TBD |
| C4 | The agent handles Yoruba-English and Pidgin-English code-switching in chat and on voice notes | conversations, speech | Task failure concentrated on `yo` or `pcm`, or STT that does not recover the labeled words | TBD |
| C5 | A buyer can ask a price, order, negotiate, pay, or complain in English, Pidgin, or Yoruba, and the order and payment rows match the goal | conversations | Final DB state or a policy check fails | TBD |
| C6 | Buyer text cannot make the agent ignore policy (prompt injection, "release the goods first", scam pressure) | safety | A trial that releases goods, confirms a fake, or follows an injected instruction | TBD |
| C7 | Muse vision catalog fields match the labeled product photo | catalog | Field mismatch above the target, once measured | TBD |
| C8 | Jev routes intent and language, including the STT language as a prior on audio | routing | Errors that change the branch the harness takes | TBD |

### System Card Template

| Field | Value |
|---|---|
| Date (UTC) | TBD |
| Git SHA (harness revision) | TBD |
| Dataset versions | TBD |
| `LLM_PROVIDER` | TBD |
| Muse Spark id (`META_TEXT_MODEL`) | TODO verify |
| Muse vision id (`META_VISION_MODEL`) | TODO verify |
| Muse Image id | TODO verify |
| SAM 3.1 id | TODO verify |
| Groq fallback ids, if used | TODO verify |
| Intron | Sahara v2.5; STT URL TODO verify; TTS `POST https://infer.voice.intron.io/tts/v1/generate` |
| TTS voice actually used | TBD |
| Prompt version (`evals/prompts/VERSION`) | TBD |
| Tools exposed | TBD |
| Max graph steps | 6 |
| Max tool calls per sales turn | 3 |
| Turn time budget | 10 s |
| Decoding (temperature, top_p) | TBD |
| Retries | one JSON retry; one timeout retry; Meta timeout may fall back to Groq once |
| TTS 503 handling | poll status; do not send a second generate |
| Eval seed | TBD |
| Bootstrap resamples | TBD |
| Judge model, if any | TBD |
| **Tier A count** | TBD |
| **Tier B count** | TBD |
| **Tier C count** | TBD |
| **Cohen's kappa (human vs judge)** | TBD |
| **ECE** | TBD |
| **SHA-256 manifest** | TBD |

### Limitations and Threats to Validity

- Payment images are synthetic or self-made and redacted. They are not a sample of Nigerian bank apps in the wild. A low false-`CONFIRMED` rate here is not a field rate.
- Conversation buyers are a simulator we wrote. It can share blind spots with the agent (simulator bias).
- `n` will be small, especially speech clips and the seller study. Intervals will be wide.
- Language coverage is English, Pidgin, and Yoruba. Igbo and Hausa are stretch and are out of the launch claims.
- Raters are few. Kappa on a small set is unstable; report `n` with it.
- The seller study is 5 to 10 people in one city, on a demo shop. It is not a market result.
- Holding the harness fixed makes the model comparison fairer and makes the absolute score depend on that harness.
- Prompts must not be tuned on the reported split.
- Intron rate limits (30 TTS requests/minute) and 503 polls can change latency.

---

## Summary of Changes (31 Oct 2026)

### Version 2.0 - SautiCivic-Inspired Improvements

**Major additions:**

1. **"Lessons from SautiCivic" section** - Complete analysis of SautiCivic Bridge report findings and how we improve on them

2. **Headline Failure Rates** - New metrics that accuracy hides:
   - Track B: FALSE-CONFIRM RATE
   - Track C: AMOUNT-ERROR RATE  
   - Track A: UNVERIFIED-CONFIRM RATE

3. **Tiered Data System** - Strict separation:
   - Tier A: Real consented in-domain
   - Tier B: Public out-of-domain
   - Tier C: Synthetic and adversarial
   - Never pooled; replication on held-out banks/apps

4. **Ethics Infrastructure** - DATA_CONSENT_LOG.md, redaction standards, pseudonymization, repository hygiene

5. **Safety Scoring** - Catastrophic vs safe abstention classification

6. **Better Than SautiCivic** - 2+ labellers with Cohen's kappa, charts (bars, confusion matrices, cost vs accuracy), ECE calibration target, balanced banks/speakers, cost per 1,000 receipts

7. **Reproducibility Standards** - SHA-256 manifests, frozen results hash, pytest suite, one-command rerun, explicit Limitations section

8. **Voice Track Reuse** - SautiCivic runners and consented-speaker method via huggingface.co/datasets/drizzy765/sauticivic-tier-a-recorded

**Modified sections:**
- Project structure: Added tier-a/b/c/ subdirectories, report/figures/, report/tables/, DATA_CONSENT_LOG.md
- Report outline: Added Headline Failure Rates, Visualizations, Safety Scoring
- Schedule: Added DATA_CONSENT_LOG.md deliverable
- Team split: Added calibration analysis (Timi), SHA-256 manifests (David), chart responsibilities (Paul)
- Rules: Added tier separation, safety first
- System card: Added Tier counts, Cohen's kappa, ECE, SHA-256 manifest

**Preserved from v1.0:**
- Overall Plan, micro1 instructions, Meta deadline
- Schedule dates, team split names
- All original methodology (How to Read a Result, Claims Table, Limitations)

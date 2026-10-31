# Demo video — screen-record log

**Record last** (after website redesign + deploy). Target final cut ≤3 minutes. 1080p. No real phone numbers or full account numbers.

**Output folder:** `demo/clips/`  
**Storyboard:** `demo/storyboard.md`  
**Upload:** unlisted Loom/YouTube → paste link in `docs/hackathon_launch.md`

---

## Clips to capture

| # | File name | What you record on screen | Voiceover beat | Done |
|---|---|---|---|---|
| 1 | `hook.mp4` | You on camera (optional) + fake transfer screenshot | “Almost lost goods to a fake alert…” | [ ] |
| 2 | `intro.mp4` | Sell-Safe logo / home (`web/`) | One-liner: Muse shop assistant that catches fakes | [ ] |
| 3 | `catalog.mp4` | Seller sends bag photo → product card appears | “Snap a photo, Muse writes the listing” | [ ] |
| 4 | `chat-pidgin.mp4` | Buyer: “Abeg how much…” → bot replies with price | Pidgin buyer chat | [ ] |
| 5 | `chat-yoruba.mp4` | Buyer Yoruba price ask → bot reply + order | Yoruba buyer chat | [ ] |
| 6 | `suspicious.mp4` | Edited screenshot → **SUSPICIOUS** + don’t release | Fake caught | [ ] |
| 7 | `confirmed.mp4` | Paystack **test** transfer → **CONFIRMED** by webhook | Real pay confirmed | [ ] |
| 8 | `crypto.mp4` | PaymentSafetyDemo **crypto** tab (`ready=true`) | Optional: Base Sepolia USDC verify | [ ] |
| 9 | `ig-scale.mp4` | Instagram DM same flow (short) | Same brain on IG | [ ] |
| 10 | `daily-summary.mp4` | Daily summary card (demo numbers OK if labelled) | ₦ saved from fakes | [ ] |
| 11 | `close.mp4` | Architecture / Meta slide + benchmark line from `evals/report.md` | Close | [ ] |

**Must-have for a short cut:** 6, 7, 3 or 4, 2, 11.  
**Nice-to-have:** 1, 5, 8, 9, 10.

---

## Still frames (already in repo — can use if no time to film)

Under `web/public/screenshots/`:

- `catalog.svg`
- `chat-pidgin.svg`
- `chat-yoruba.svg`
- `suspicious.svg`
- `confirmed.svg`
- `daily-summary.svg`

---

## Before you hit record

1. `PYTHONPATH=backend python -m scripts.seed_demo` (or `--memory`)
2. Confirm `DEMO_REAL_TX_HASH` if filming crypto tab
3. Backend + `web` running; Instagram tab connected for demos
4. Use Paystack **test** mode only; fictional last-4s only
5. Captions on every spoken line in the edit

---

## After recording

- [ ] Rough cut assembled (≤3:00)
- [ ] Unlisted link works in incognito
- [ ] Link added to `docs/hackathon_launch.md`
- [ ] Optional: tag `v0.1-demo` after deploy

## Automated proof (no camera needed)

Already generated: `demo/clips/PROOF.md` (CONFIRMED + release 409). Use as B-roll note or safety net, not as the main video.

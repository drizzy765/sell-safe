# Recording and release (human)

Automated packaging for this phase is done. Remaining steps need a person:

## Record (≤3 minutes)

1. Pre-seed: `PYTHONPATH=backend python -m scripts.seed_demo --memory` (or Supabase without `--memory`).
2. Confirm crypto demo: `DEMO_REAL_TX_HASH` set; open PaymentSafetyDemo crypto tab.
3. Follow `demo/storyboard.md` scenes 1–8.
4. Save clips under `demo/clips/` (`suspicious.mp4`, `confirmed.mp4`, optional `crypto.mp4`).
5. Upload unlisted Loom/YouTube; paste the link into `docs/hackathon_launch.md`.

## Deploy + tag

1. Deploy backend + `web/` to the hackathon host.
2. Confirm public `GET /health` returns ok.
3. Feature freeze, then:
   ```bash
   git tag -a v0.1-demo -m "demo freeze"
   git push origin v0.1-demo
   ```
4. Before Indie submit: tag `v1.0-submission` on the submitted commit.

## Already green

- `demo/clips/PROOF.md` — automated CONFIRMED + 409
- `evals/report.md` — 20/20, zero false CONFIRMED on fakes
- Web `/status`, `/faq`, `/privacy` + screenshot SVGs

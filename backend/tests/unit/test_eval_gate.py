"""Unit tests for the eval launch gate."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_eval_runner_exits_zero_on_clean_dataset() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "evals.run", "--suite", "payments", "--dataset", "v1"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_eval_runner_rejects_fake_confirmed() -> None:
    labels_path = REPO_ROOT / "evals" / "data" / "synthetic" / "payments" / "v1" / "labels.jsonl"
    original = labels_path.read_text(encoding="utf-8")
    try:
        # Inject a fake case that would force a CONFIRMED verdict.
        injected = (
            original
            + '\n{"id":"gate-test-fake-confirmed","description":"fake case that should fail gate",'
            '"order":{"id":"gate1","total_kobo":1500000,"created_at":"2026-10-27T10:00:00Z"},'
            '"image_vision":{"is_transfer_receipt":true,"amount_kobo":1500000,"currency":"NGN",'
            '"sender_name":"Ada","sender_bank":"GTBank","recipient_name":"Tolu",'
            '"recipient_acct_last4":"1234","reference":"ref-gate-fake","status_text":"successful",'
            '"txn_time_iso":"2026-10-27T10:15:00Z","app_style":"GTWorld","visual_anomalies":[]},'
            '"evidence_rows":[{"id":"ev-gate-fake","type":"va_webhook","trust_level":4,'
            '"extracted":{"amount_kobo":1500000,"reference":"ref-gate-fake","sender_name":"Ada",'
            '"status_text":"success","txn_time_iso":"2026-10-27T10:15:00Z"}}],'
            '"jev_scores":{"evidence_match":1.0,"receipt_tampered":0.0},'
            '"expected_verdict":"SUSPICIOUS","expected_release_allowed":false,"fake":true}\n'
        )
        labels_path.write_text(injected, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "-m", "evals.run", "--suite", "payments", "--dataset", "v1"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "LAUNCH GATE FAILED" in result.stdout
    finally:
        labels_path.write_text(original, encoding="utf-8")

"""Evaluation runner for Sell-Safe payment verification.

Usage:
    python -m evals.run --suite payments --dataset v1
"""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Make backend importable when running `python -m evals.run` from repo root.
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.decisions.base import RouteScores
from app.llm.fake import FakeProvider
from app.verification.extract import AskResend, extract_receipt
from app.verification.matchers import find_matching_evidence
from app.verification.rules import apply_rules
from app.verification.verdict import decide_verdict


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _load_labels(dataset: str) -> list[dict[str, Any]]:
    path = _repo_root() / "evals" / "data" / "synthetic" / "payments" / dataset / "labels.jsonl"
    labels: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            labels.append(json.loads(line))
    return labels


def _placeholder_image() -> bytes:
    """Return a tiny valid JPEG-ish byte sequence.

    The runner only needs *some* image bytes because the provider is faked; a
    real vision provider would need an actual rendered receipt.
    """
    # Minimal valid JPEG header + some padding.
    return bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46]) + b"\x00" * 64


def _make_jev_scores(raw: dict[str, float] | None) -> RouteScores:
    if raw is None:
        raw = {}
    return RouteScores(
        intent="payment_proof",
        language="en",
        evidence_match=raw.get("evidence_match", 0.0),
        receipt_tampered=raw.get("receipt_tampered", 0.0),
    )


async def _run_case(label: dict[str, Any]) -> dict[str, Any]:
    order = label["order"]
    image_vision = label["image_vision"]
    evidence_rows = label.get("evidence_rows", [])
    expected_verdict = label["expected_verdict"]
    expected_release = label["expected_release_allowed"]

    provider = FakeProvider(vision=image_vision)
    image = _placeholder_image()
    extracted = None
    extraction_error = None
    try:
        result = await extract_receipt(provider, image)
        if not isinstance(result, AskResend):
            extracted = result
    except Exception as exc:
        extraction_error = str(exc)

    if extracted is None:
        from app.verification.rules import RulesResult

        rules = RulesResult(rule_hits=[], rule_risk=0.0, not_confirmable=False)
        matched = None
    else:
        matched = find_matching_evidence(extracted, evidence_rows)
        exclude_ids = {matched.row["id"]} if matched and matched.row.get("id") else None
        current_payment_id = matched.row.get("payment_id") if matched else None
        rules = apply_rules(
            order,
            extracted,
            evidence_rows,
            fraud_signals=[],
            seller_account_last4=order.get("seller_account_last4", "1234"),
            seller_name=order.get("seller_name", "Tolu"),
            pii_salt="",
            exclude_evidence_ids=exclude_ids,
            current_payment_id=current_payment_id,
        )
    jev_scores = _make_jev_scores(label.get("jev_scores"))
    verdict = decide_verdict(order, extracted, rules, matched, jev_scores)

    return {
        "id": label["id"],
        "description": label["description"],
        "expected_verdict": expected_verdict,
        "expected_release_allowed": expected_release,
        "actual_verdict": verdict.verdict,
        "actual_release_allowed": verdict.release_allowed,
        "confidence": verdict.confidence,
        "rule_hits": rules.rule_hits,
        "matched_evidence_id": verdict.matched_evidence_id,
        "extraction_error": extraction_error,
        "passed": verdict.verdict == expected_verdict
        and verdict.release_allowed == expected_release,
        "fake": label.get("fake", False),
    }


def _confusion_matrix(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    labels = ["CONFIRMED", "NOT_FOUND", "SUSPICIOUS", "UNVERIFIED"]
    matrix: dict[str, dict[str, int]] = {
        expected: {actual: 0 for actual in labels} for expected in labels
    }
    for result in results:
        expected = result["expected_verdict"]
        actual = result["actual_verdict"]
        if expected in matrix and actual in matrix[expected]:
            matrix[expected][actual] += 1
    return matrix


def _false_confirmed_count(results: list[dict[str, Any]]) -> int:
    return sum(1 for r in results if r["fake"] and r["actual_verdict"] == "CONFIRMED")


def _write_report(
    results: list[dict[str, Any]],
    matrix: dict[str, dict[str, int]],
    false_confirmed: int,
    suite: str,
    dataset: str,
    sha: str,
) -> Path:
    reports_dir = _repo_root() / "evals" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    path = reports_dir / f"{timestamp}-{suite}-{sha}.md"

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    lines = [
        "# Sell-Safe Payment Verification Evaluation Report",
        "",
        f"- Suite: `{suite}`",
        f"- Dataset: `{dataset}`",
        f"- Git SHA: `{sha}`",
        f"- Timestamp: {datetime.now(tz=UTC).isoformat()}",
        "",
        "## Summary",
        "",
        f"- Total cases: {total}",
        f"- Passed: {passed}",
        f"- Failed: {total - passed}",
        f"- False CONFIRMED on fake cases: {false_confirmed}",
        "",
        "## Confusion Matrix",
        "",
        "| Expected \\ Actual | CONFIRMED | NOT_FOUND | SUSPICIOUS | UNVERIFIED |",
        "|---|---|---|---|---|",
    ]
    verdict_labels = ["CONFIRMED", "NOT_FOUND", "SUSPICIOUS", "UNVERIFIED"]
    for expected in verdict_labels:
        row = " | ".join(str(matrix[expected][actual]) for actual in verdict_labels)
        lines.append(f"| {expected} | {row} |")

    lines.extend(["", "## Detail", ""])
    for result in results:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(
            f"- `{result['id']}` ({status}): expected {result['expected_verdict']}"
            f" (release={result['expected_release_allowed']}), got {result['actual_verdict']}"
            f" (release={result['actual_release_allowed']}, confidence={result['confidence']:.2f})"
        )
        if result["rule_hits"]:
            lines.append(f"  - rule_hits: {', '.join(result['rule_hits'])}")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sell-Safe eval suites")
    parser.add_argument("--suite", default="payments", help="eval suite name")
    parser.add_argument("--dataset", default="v1", help="dataset version")
    parser.add_argument(
        "--provider", default="fake", help="LLM provider (only 'fake' supported in CI)"
    )
    parser.add_argument("--seed", type=int, default=42, help="random seed (unused)")
    args = parser.parse_args()

    if args.provider != "fake":
        print(f"Provider '{args.provider}' is not supported by the synthetic runner yet.")
        return 2

    labels = _load_labels(args.dataset)
    results = await asyncio.gather(*[_run_case(label) for label in labels])
    matrix = _confusion_matrix(results)
    false_confirmed = _false_confirmed_count(results)
    sha = _git_sha()

    path = _write_report(results, matrix, false_confirmed, args.suite, args.dataset, sha)
    print(f"Report written to {path}")

    if false_confirmed > 0:
        print(f"LAUNCH GATE FAILED: {false_confirmed} fake case(s) returned CONFIRMED")
        return 1

    failed = sum(1 for r in results if not r["passed"])
    if failed:
        print(f"EVAL FAILED: {failed} case(s) did not match expected verdict")
        return 1

    print("All cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

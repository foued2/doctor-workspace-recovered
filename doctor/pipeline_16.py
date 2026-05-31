from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from doctor.pipeline import run_pipeline

_BENCHMARK_PATH = Path(__file__).parent / "data" / "induction_benchmark.json"


def run_induction_benchmark(verbose: bool = False) -> dict:
    with open(_BENCHMARK_PATH, encoding="utf-8") as f:
        benchmark = json.load(f)

    cases = benchmark["cases"]
    results = []

    for case in cases:
        result = run_pipeline(
            statement=case["statement"],
            solution_code=case["solution_code"],
        )

        ir = result.get("induction_result") or {}
        actual_eligible = ir.get("eligible", False)
        actual_reason = ir.get("rejection_reason")

        expected_eligible = case["expected_eligible"]
        expected_reason = case.get("expected_rejection_reason")

        eligible_match = actual_eligible == expected_eligible
        reason_match = (
            expected_reason is None
            or actual_reason == expected_reason
        )
        passed = eligible_match and reason_match

        entry = {
            "id": case["id"],
            "category": case["category"],
            "description": case["description"],
            "expected_eligible": expected_eligible,
            "actual_eligible": actual_eligible,
            "expected_rejection_reason": expected_reason,
            "actual_rejection_reason": actual_reason,
            "passed": passed,
        }
        results.append(entry)

        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {case['id']} ({case['category']})")
            if not passed:
                print(f"       eligible: expected={expected_eligible} actual={actual_eligible}")
                print(f"       reason:   expected={expected_reason} actual={actual_reason}")

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count

    by_category: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if r["passed"]:
            by_category[cat]["passed"] += 1

    summary = {
        "total": total,
        "passed": passed_count,
        "failed": failed_count,
        "pass_rate": round(passed_count / total, 4) if total else 0.0,
        "by_category": by_category,
        "cases": results,
    }

    return summary


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    summary = run_induction_benchmark(verbose=verbose)

    print(f"\nInduction Benchmark: {summary['passed']}/{summary['total']} passed")
    print(f"Pass rate: {summary['pass_rate']:.1%}")
    print("\nBy category:")
    for cat, counts in summary["by_category"].items():
        print(f"  {cat}: {counts['passed']}/{counts['total']}")

    if summary["failed"] > 0:
        print("\nFailed cases:")
        for r in summary["cases"]:
            if not r["passed"]:
                print(f"  {r['id']}: eligible={r['actual_eligible']} reason={r['actual_rejection_reason']}")

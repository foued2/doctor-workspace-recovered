#!/usr/bin/env python
"""
Doctor System Integrity Report — Verification Run
===================================================
Generates a full system integrity report by running all Phase verifications.
"""
import json
import time
from datetime import datetime

from doctor.s_measurement import (
    measure_multi_run, compute_log_ratio, validate_scaling_sizes,
    detect_capped_execution, get_validator_strength, has_strong_validator,
    get_reference_model, is_sudoku_invalid_measurement,
    compute_system_integrity, GrowthMeasurement,
    VALIDATION_PROFILES, REFERENCE_MODELS,
)
from doctor.s_efficiency import compute_efficiency, efficiency_to_dict
from doctor.test_executor import TestExecutor


def run_all_verifications():
    results = {}

    # ── PHASE 0: S-Efficiency Freeze ──────────────────────────────────
    print("PHASE 0: S-Efficiency Freeze...")
    r = compute_efficiency([{"execution_time": 0.01}], "Two Sum")
    results["phase_0"] = {
        "status": "PASS" if r.research_only and r.efficiency == "not_applicable" else "FAIL",
        "research_only": r.research_only,
        "efficiency": r.efficiency,
        "s_final": r.s_final,
    }

    # ── PHASE 1.1: Multi-Run Measurement ─────────────────────────────
    print("PHASE 1.1: Multi-Run Measurement...")
    m = measure_multi_run(lambda x: sum(range(x)), (1000,), n_runs=10)
    m.input_size = 1000
    results["phase_1_1"] = {
        "status": "PASS" if m.status == "stable" and m.median_ms > 0 else "FAIL",
        "median_ms": round(m.median_ms, 4),
        "cv": m.cv,
        "n_runs": len(m.runtimes_ms),
        "stable": m.status == "stable",
    }

    # ── PHASE 1.2: Scaling Protocol ──────────────────────────────────
    print("PHASE 1.2: Scaling Protocol...")
    log_ratio = compute_log_ratio(10, 100, 5, 10)
    valid_4, _ = validate_scaling_sizes([4, 6, 9, 13])
    invalid_2, reason_2 = validate_scaling_sizes([4, 6])
    results["phase_1_2"] = {
        "status": "PASS" if (
            log_ratio is not None and abs(log_ratio - 3.322) < 0.01
            and valid_4 and not invalid_2
        ) else "FAIL",
        "log_ratio": round(log_ratio, 3) if log_ratio else None,
        "expected_log_ratio": 3.322,
        "valid_4_sizes": valid_4,
        "invalid_2_sizes": invalid_2,
        "reject_reason": reason_2,
    }

    # ── PHASE 1.3: Capped Execution Detection ────────────────────────
    print("PHASE 1.3: Capped Execution Detection...")
    is_capped, cap_reason = detect_capped_execution(
        "def solve(): max_iterations=100", "test"
    )
    is_capped_sudoku, sudoku_reason = detect_capped_execution("", "Sudoku")
    results["phase_1_3"] = {
        "status": "PASS" if is_capped and is_capped_sudoku else "FAIL",
        "cap_detected": is_capped,
        "cap_reason": cap_reason,
        "sudoku_capped": is_capped_sudoku,
        "sudoku_reason": sudoku_reason,
    }

    # ── PHASE 2.4: Validator Strength ────────────────────────────────
    print("PHASE 2.4: Validator Strength...")
    results["phase_2_4"] = {
        "status": "PASS" if (
            get_validator_strength("N-Queens") == "strong"
            and get_validator_strength("Container With Most Water") == "weak"
            and get_validator_strength("Longest Palindromic Substring") == "partial"
            and has_strong_validator("N-Queens")
            and not has_strong_validator("Container With Most Water")
        ) else "FAIL",
        "strong_problems": [
            k for k, v in VALIDATION_PROFILES.items() if v.strength == "strong"
        ],
        "partial_problems": [
            k for k, v in VALIDATION_PROFILES.items() if v.strength == "partial"
        ],
        "weak_problems": [
            k for k, v in VALIDATION_PROFILES.items() if v.strength == "weak"
        ],
    }

    # ── PHASE 2.5: Validator-Based Verification ──────────────────────
    print("PHASE 2.5: Validator-Based Verification...")
    te = TestExecutor()
    r_two_sum = te.verify(
        "Two Sum",
        "def twoSum(nums, target):\n"
        "    h={}\n"
        "    for i,x in enumerate(nums):\n"
        "        if target-x in h: return [h[target-x],i]\n"
        "        h[x]=i"
    )
    r_nqueens = te.verify(
        "N-Queens",
        "def solveNQueens(n):\n"
        "    res=[]\n"
        "    def bt(r,cols):\n"
        "        if r==n: res.append(['.'*c+'Q'+'.'*(n-c-1) for c in cols]); return\n"
        "        for c in range(n):\n"
        "            if all(c!=cc and abs(r-i)!=abs(c-cc) for i,cc in enumerate(cols)):"
        " bt(r+1,cols+[c])\n"
        "    bt(0,[]); return res"
    )
    results["phase_2_5"] = {
        "status": "PASS" if (
            r_two_sum.verdict == "correct" and r_nqueens.verdict == "correct"
        ) else "FAIL",
        "two_sum_verdict": r_two_sum.verdict,
        "two_sum_pass_rate": r_two_sum.pass_rate,
        "nqueens_verdict": r_nqueens.verdict,
        "nqueens_pass_rate": r_nqueens.pass_rate,
    }

    # ── PHASE 3.6: Reference Models ──────────────────────────────────
    print("PHASE 3.6: Reference Models...")
    nq_ref = get_reference_model("N-Queens")
    ts_ref = get_reference_model("Two Sum")
    results["phase_3_6"] = {
        "status": "PASS" if (
            nq_ref and nq_ref.reference_type == "external"
            and ts_ref and ts_ref.reference_type == "external"
            and nq_ref.is_absolute and nq_ref.is_stable
        ) else "FAIL",
        "n_queens_type": nq_ref.reference_type if nq_ref else None,
        "n_queens_source": nq_ref.reference_source if nq_ref else None,
        "two_sum_type": ts_ref.reference_type if ts_ref else None,
        "two_sum_source": ts_ref.reference_source if ts_ref else None,
        "total_external_refs": sum(
            1 for v in REFERENCE_MODELS.values() if v.reference_type == "external"
        ),
        "total_empirical_refs": sum(
            1 for v in REFERENCE_MODELS.values() if v.reference_type == "empirical"
        ),
    }

    # ── PHASE 4.7: Orthogonal Growth Metrics ─────────────────────────
    print("PHASE 4.7: Orthogonal Growth Metrics...")
    gm_correct = GrowthMeasurement(
        problem_key="N-Queens", variant_name="correct",
        sizes=[4, 6, 9, 13], measurements=[],
        median_steps=[0.05, 0.1, 0.2, 0.4], variance_steps=[], cv_steps=[],
        log_log_slope=1.0, slope_quality="valid",
        absolute_growth="exponential", relative_optimality="optimal",
        validation_strength="strong", measurement_status="valid",
    )
    results["phase_4_7"] = {
        "status": "PASS" if (
            gm_correct.absolute_growth in ("sub_linear", "linear", "quadratic",
                                           "exponential", "super_exponential", "unknown")
            and gm_correct.relative_optimality in ("optimal", "near_optimal",
                                                   "suboptimal", "unknown")
        ) else "FAIL",
        "absolute_growth": gm_correct.absolute_growth,
        "relative_optimality": gm_correct.relative_optimality,
        "validation_strength": gm_correct.validation_strength,
    }

    # ── PHASE 5.8: Sudoku Invalid Measurement ────────────────────────
    print("PHASE 5.8: Sudoku Invalid Measurement...")
    is_sudoku, sudoku_reason = is_sudoku_invalid_measurement(
        "def sudoku_solve(board): ..."
    )
    results["phase_5_8"] = {
        "status": "PASS" if is_sudoku and sudoku_reason == "cap_saturation" else "FAIL",
        "is_sudoku_invalid": is_sudoku,
        "reason": sudoku_reason,
    }

    # ── PHASE 6.9: System Integrity ──────────────────────────────────
    print("PHASE 6.9: System Integrity...")
    m1 = GrowthMeasurement(
        problem_key="N-Queens", variant_name="correct",
        sizes=[4, 6, 9, 13], measurements=[],
        median_steps=[0.05, 0.1, 0.2, 0.4], variance_steps=[], cv_steps=[],
        log_log_slope=1.0, slope_quality="valid",
        absolute_growth="exponential", relative_optimality="optimal",
        validation_strength="strong", measurement_status="valid",
    )
    m2 = GrowthMeasurement(
        problem_key="Two Sum", variant_name="correct",
        sizes=[10, 100, 1000, 10000], measurements=[],
        median_steps=[0.01, 0.02, 0.05, 0.1], variance_steps=[], cv_steps=[],
        log_log_slope=1.0, slope_quality="valid",
        absolute_growth="linear", relative_optimality="optimal",
        validation_strength="strong", measurement_status="valid",
    )
    m3 = GrowthMeasurement(
        problem_key="Sudoku", variant_name="brute",
        sizes=[4, 6, 9, 13], measurements=[],
        median_steps=[], variance_steps=[], cv_steps=[],
        log_log_slope=None, slope_quality="invalid",
        absolute_growth="unknown", relative_optimality="unknown",
        validation_strength="weak", measurement_status="invalid_measurement",
        invalid_reason="cap_saturation",
    )
    integrity = compute_system_integrity([m1, m2, m3])
    results["phase_6_9"] = {
        "status": "PASS" if (
            abs(integrity.valid_measurement_pct - 66.67) < 0.1
            and abs(integrity.strong_correctness_pct - 66.67) < 0.1
            and integrity.classification_blocked  # 66.67 < 70
        ) else "FAIL",
        "total_problems": integrity.total_problems,
        "strong_correctness_pct": round(integrity.strong_correctness_pct, 1),
        "valid_measurement_pct": round(integrity.valid_measurement_pct, 1),
        "invalid_unstable_pct": round(integrity.invalid_unstable_pct, 1),
        "no_reference_baseline_pct": round(integrity.no_reference_baseline_pct, 1),
        "classification_blocked": integrity.classification_blocked,
    }

    # ── INVARIANT TEST: Disjoint Branches ────────────────────────────
    print("Invariant Test: Disjoint Branches...")
    r_linear_low = compute_efficiency([{"execution_time": 0.00002}], "Two Sum")
    r_linear_high = compute_efficiency([{"execution_time": 0.01}], "Two Sum")
    r_search_efficient = compute_efficiency([{"execution_time": 0.00005}], "N-Queens")
    r_search_inefficient = compute_efficiency([{"execution_time": 0.001}], "N-Queens")
    results["invariant_test"] = {
        "status": "PASS" if (
            r_linear_low.efficiency == "not_applicable"
            and r_linear_high.efficiency == "not_applicable"
            and r_linear_high.s_final > 100  # huge S_final
            and r_search_efficient.efficiency == "efficient"
            and r_search_inefficient.efficiency == "inefficient"
        ) else "FAIL",
        "linear_low_s_final": r_linear_low.s_final,
        "linear_low_efficiency": r_linear_low.efficiency,
        "linear_high_s_final": r_linear_high.s_final,
        "linear_high_efficiency": r_linear_high.efficiency,
        "search_efficient": r_search_efficient.efficiency,
        "search_inefficient": r_search_inefficient.efficiency,
    }

    return results


def generate_report(results):
    total = len(results)
    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    failed = total - passed

    report = {
        "report_title": "DOCTOR SYSTEM INTEGRITY REPORT — Verification Run",
        "timestamp": datetime.now().isoformat(),
        "framework_version": "s_measurement.py v2",
        "summary": {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
        },
        "phases": results,
        "integrity_gate": {
            "all_phases_pass": failed == 0,
            "measurement_validity": "structurally_valid" if failed == 0 else "needs_review",
        },
    }
    return report


if __name__ == "__main__":
    print("=" * 65)
    print("DOCTOR SYSTEM INTEGRITY REPORT — Verification Run")
    print("=" * 65)
    print()

    results = run_all_verifications()
    report = generate_report(results)

    # Print summary
    print()
    print("=" * 65)
    print(f"SUMMARY: {report['summary']['passed']}/{report['summary']['total_checks']} passed")
    print(f"Pass Rate: {report['summary']['pass_rate']}%")
    print(f"Integrity Gate: {'PASS' if report['integrity_gate']['all_phases_pass'] else 'FAIL'}")
    print(f"Measurement Validity: {report['integrity_gate']['measurement_validity']}")
    print("=" * 65)
    print()

    # Print per-phase results
    for phase, data in results.items():
        status_icon = "✓" if data.get("status") == "PASS" else "✗"
        print(f"  {status_icon} {phase}: {data.get('status')}")

    print()

    # Save report
    report_path = "scratch/system_integrity_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to: {report_path}")

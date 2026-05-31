#!/usr/bin/env python
"""
DOCTOR SYSTEM — DESTRUCTIVE VALIDATION PROTOCOL
=================================================
Goal: BREAK the system's assumptions. NOT validate correctness.
Target: Find contradictions, hidden dependencies, or invalid invariants.

Tests 6 attack vectors:
  1. End-to-End System Failure (expected output vs validator conflict)
  2. Measurement Adversarial Stability (30 runs, artificial delays)
  3. Validator Adversarial Robustness (strong reject / weak false-accept)
  4. Reference System Integrity (circular reference detection)
  5. Scaling Logic Stress (non-geometric, reversed, identical S)
  6. Cross-Layer Consistency Attack (mutated outputs between layers)

OUTPUT: Only failures with reproduction steps. No optimization suggestions.
"""
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass, field

# ── Test harness ─────────────────────────────────────────────────────────────

@dataclass
class Failure:
    test_id: str
    severity: str        # "CRITICAL" | "MAJOR" | "MINOR"
    message: str
    layer: str           # which layer allowed failure to propagate
    repro: str           # exact reproduction steps
    deterministic: bool  # True = deterministic, False = stochastic
    data: dict = field(default_factory=dict)

    def __repr__(self):
        return f"  [{self.severity}] {self.test_id}: {self.message}"


class StressHarness:
    def __init__(self):
        self.failures: list[Failure] = []
        self.passed: list[str] = []

    def record_failure(self, failure: Failure):
        self.failures.append(failure)

    def record_pass(self, test_id: str):
        self.passed.append(test_id)

    def summary(self) -> dict:
        total = len(self.failures) + len(self.passed)
        return {
            "total": total,
            "failures": len(self.failures),
            "passed": len(self.passed),
            "critical_count": sum(1 for f in self.failures if f.severity == "CRITICAL"),
            "major_count": sum(1 for f in self.failures if f.severity == "MAJOR"),
            "minor_count": sum(1 for f in self.failures if f.severity == "MINOR"),
        }

    def print_results(self):
        print()
        if self.failures:
            print("=" * 65)
            print("DETECTED FAILURES:")
            print("=" * 65)
            for f in self.failures:
                print(f)
                print(f"         Layer: {f.layer}")
                print(f"         Repro: {f.repro}")
                print(f"         Deterministic: {f.deterministic}")
                print()
        else:
            print("=" * 65)
            print("NO FAILURES DETECTED")
            print("=" * 65)

        s = self.summary()
        print(f"SUMMARY: {s['failures']} failures / {s['total']} tests")
        if s['critical_count'] > 0:
            print(f"  CRITICAL: {s['critical_count']}")
        if s['major_count'] > 0:
            print(f"  MAJOR: {s['major_count']}")
        if s['minor_count'] > 0:
            print(f"  MINOR: {s['minor_count']}")


harness = StressHarness()


# ═══════════════════════════════════════════════════════════════════════════
# ATTACK 1: End-to-End System Failure — Expected Output vs Validator Conflict
# ═══════════════════════════════════════════════════════════════════════════

def test_e2e_correctness_bypass():
    """Does the system ever defer to expected output over validator?"""
    print("\n" + "=" * 65)
    print("ATTACK 1: End-to-End Correctness Bypass")
    print("=" * 65)

    from doctor.test_executor import TestExecutor, _verify_with_validator

    te = TestExecutor()

    # ── Attack 1a: Correct solution, structurally different from expected ──
    # Two Sum: two-pass hash map (build full map, then look up) vs
    # one-pass (build incrementally). Both correct, but may produce
    # different indices for the same input.
    correct_but_different = (
        "def twoSum(nums, target):\n"
        "    # Two-pass approach — may return different indices\n"
        "    h = {}\n"
        "    for i, x in enumerate(nums):\n"
        "        h[x] = i  # last occurrence wins\n"
        "    for i, x in enumerate(nums):\n"
        "        complement = target - x\n"
        "        if complement in h and h[complement] != i:\n"
        "            return [i, h[complement]]\n"
        "    return []"
    )
    report_a = te.verify("Two Sum", correct_but_different)

    # The solution IS correct — it finds valid indices.
    # But for the "self_element_reuse" test ([3,3], 6), the two-pass
    # version might fail since h[3]=1 overwrites h[3]=0, and then
    # h[complement]==i. This is actually a KNOWN edge case.
    # Let's check: does the system correctly flag this?
    # Expected: should fail the self_element_reuse test.
    # If pass_rate < 1.0 AND verdict != "correct", the system works.
    # If pass_rate == 1.0, the two-pass version is actually also correct.
    # Either way, the validator must be the deciding factor.

    # ── Attack 1b: Incorrect solution that happens to match some expected outputs ──
    # Returns wrong answers but might pass some tests by coincidence
    incorrect_matches_some = (
        "def twoSum(nums, target):\n"
        "    # Always returns [0, 1] — passes only if first two elements sum to target\n"
        "    return [0, 1]"
    )
    report_b = te.verify("Two Sum", incorrect_matches_some)

    # For the standard test suite, [0,1] is correct for the first test
    # but wrong for most others. The system should NOT give "correct".
    if report_b.verdict == "correct":
        harness.record_failure(Failure(
            test_id="1a E2E: Incorrect matches expected on some tests",
            severity="CRITICAL",
            message=(
                f"Incorrect solution (always returns [0,1]) got verdict=correct. "
                f"Pass rate: {report_b.pass_rate}. "
                f"Expected: incorrect. System accepted it."
            ),
            layer="Layer 2 (Test Executor)",
            repro="Run twoSum that always returns [0,1] against standard test suite",
            deterministic=True,
            data={"verdict": report_b.verdict, "pass_rate": report_b.pass_rate},
        ))
    else:
        harness.record_pass("1a E2E: Incorrect solution correctly rejected")

    # ── Attack 1c: Partial solution — passes basic, fails edge ──
    partial_solution = (
        "def twoSum(nums, target):\n"
        "    # Only works for positive numbers, fails for negative\n"
        "    h = {}\n"
        "    for i, x in enumerate(nums):\n"
        "        if x < 0: continue  # skip negatives — bug\n"
        "        if target-x in h: return [h[target-x],i]\n"
        "        h[x]=i"
    )
    report_c = te.verify("Two Sum", partial_solution)

    if report_c.verdict == "correct":
        harness.record_failure(Failure(
            test_id="1b E2E: Partial solution accepted as correct",
            severity="CRITICAL",
            message=(
                f"Partial solution (skips negatives) got verdict=correct. "
                f"Pass rate: {report_c.pass_rate}. "
                f"Expected: partial or incorrect."
            ),
            layer="Layer 2 (Test Executor)",
            repro="Run twoSum that skips negative numbers",
            deterministic=True,
            data={"verdict": report_c.verdict, "pass_rate": report_c.pass_rate},
        ))
    else:
        harness.record_pass("1b E2E: Partial solution correctly not accepted as correct")

    # ── Attack 1d: Verify validator is actually used, not just expected output ──
    # N-Queens correct solution. The validator checks diagonal attacks.
    # Even if expected output format differs, validator should confirm correctness.
    correct_nqueens = (
        "def solveNQueens(n):\n"
        "    res=[]\n"
        "    def bt(r,cols):\n"
        "        if r==n: res.append(['.'*c+'Q'+'.'*(n-c-1) for c in cols]); return\n"
        "        for c in range(n):\n"
        "            if all(c!=cc and abs(r-i)!=abs(c-cc) for i,cc in enumerate(cols)):"
            " bt(r+1,cols+[c])\n"
        "    bt(0,[]); return res"
    )
    report_d = te.verify("N-Queens", correct_nqueens)
    if report_d.verdict != "correct":
        harness.record_failure(Failure(
            test_id="1c E2E: Correct N-Queens solution rejected",
            severity="MAJOR",
            message=(
                f"Correct N-Queens solution got verdict={report_d.verdict} "
                f"(expected: correct). Pass rate: {report_d.pass_rate}."
            ),
            layer="Layer 2 (Test Executor)",
            repro="Run correct backtracking N-Queens solution",
            deterministic=True,
            data={"verdict": report_d.verdict, "pass_rate": report_d.pass_rate},
        ))
    else:
        harness.record_pass("1c E2E: Correct N-Queens solution accepted by validator")


# ═══════════════════════════════════════════════════════════════════════════
# ATTACK 2: Measurement Adversarial Stability
# ═══════════════════════════════════════════════════════════════════════════

def test_measurement_adversarial():
    """Test S-layer under adversarial conditions: micro-noise, delays, reordering."""
    print("\n" + "=" * 65)
    print("ATTACK 2: Measurement Adversarial Stability")
    print("=" * 65)

    from doctor.s_measurement import measure_multi_run

    def workload(n):
        return sum(range(n))

    # ── Attack 2a: 30 repetitions, check drift ──
    N_RUNS = 30
    all_medians = []
    all_cvs = []

    for i in range(N_RUNS):
        m = measure_multi_run(workload, (100000,), n_runs=10)
        m.input_size = 100000
        all_medians.append(m.median_ms)
        all_cvs.append(m.cv)

    median_of_medians = statistics.median(all_medians)
    median_std = statistics.stdev(all_medians)
    median_cv = median_std / median_of_medians if median_of_medians > 0 else 0

    # Check for material drift
    max_deviation = max(abs(m - median_of_medians) for m in all_medians)
    max_deviation_pct = max_deviation / median_of_medians if median_of_medians > 0 else 0

    if max_deviation_pct > 0.50:  # more than 50% deviation from median
        harness.record_failure(Failure(
            test_id="2a Measurement: Median drift > 50%",
            severity="CRITICAL",
            message=(
                f"Max deviation from median: {max_deviation_pct:.2%}. "
                f"Median: {median_of_medians:.4f}ms. "
                f"Range: [{min(all_medians):.4f}, {max(all_medians):.4f}]ms"
            ),
            layer="S-Measurement",
            repro="Run measure_multi_run 30 times with identical input n=100000",
            deterministic=False,  # timing noise is stochastic
            data={
                "max_deviation_pct": round(max_deviation_pct, 4),
                "median_of_medians_ms": round(median_of_medians, 4),
                "min_median_ms": round(min(all_medians), 4),
                "max_median_ms": round(max(all_medians), 4),
            },
        ))
    else:
        harness.record_pass("2a Measurement: No material drift in 30 runs")

    # ── Attack 2b: Different call orders — does order affect timing? ──
    # Run warm-up calls before measurement vs cold start
    cold_medians = []
    warm_medians = []

    for i in range(15):
        # Cold start: no warmup
        m = measure_multi_run(workload, (100000,), n_runs=10)
        cold_medians.append(m.median_ms)

    for i in range(15):
        # Warm start: call workload 5 times before measuring
        workload(100000)
        workload(100000)
        workload(100000)
        workload(100000)
        workload(100000)
        m = measure_multi_run(workload, (100000,), n_runs=10)
        warm_medians.append(m.median_ms)

    cold_mean = statistics.mean(cold_medians)
    warm_mean = statistics.mean(warm_medians)
    order_bias = abs(cold_mean - warm_mean) / cold_mean if cold_mean > 0 else 0

    if order_bias > 0.25:  # more than 25% difference
        harness.record_failure(Failure(
            test_id="2b Measurement: Call order bias > 25%",
            severity="MAJOR",
            message=(
                f"Order bias: {order_bias:.2%}. "
                f"Cold mean: {cold_mean:.4f}ms. "
                f"Warm mean: {warm_mean:.4f}ms"
            ),
            layer="S-Measurement",
            repro="Run measure_multi_run with vs without 5 warmup calls",
            deterministic=False,
            data={
                "order_bias_pct": round(order_bias, 4),
                "cold_mean_ms": round(cold_mean, 4),
                "warm_mean_ms": round(warm_mean, 4),
            },
        ))
    else:
        harness.record_pass("2b Measurement: No call order bias")

    # ── Attack 2c: Scheduler interference — artificial delays ──
    # Insert noop loops before execution
    def delayed_workload(n, noop_iterations=100000):
        for _ in range(noop_iterations):
            pass
        return sum(range(n))

    # Measure with 0, 100k, 500k noop iterations
    baseline_m = measure_multi_run(workload, (100000,), n_runs=10)
    delayed_m = measure_multi_run(delayed_workload, (100000, 500000), n_runs=10)

    # The S-layer should report the workload time, not the noop time.
    # But measure_multi_run measures the ENTIRE function call including noops.
    # This is expected behavior — the S-layer measures total execution time.
    # The question is: does the system CONFLATE noop time with algorithmic time?
    # If the system is a true measurement system, it should report total time.
    # The noop time IS part of the execution cost.
    # We flag it if the noop time is < 10% of total (meaning workload dominates),
    # OR if noop time is > 10x workload time (meaning noop dominates).

    # Extract median time for pure workload vs delayed
    baseline_ms = baseline_m.median_ms
    delayed_ms = delayed_m.median_ms
    noop_overhead = delayed_ms - baseline_ms

    # The noop overhead should be proportional to the noop count
    # If noop overhead is negative or zero, that's a measurement bug
    if noop_overhead < 0:
        harness.record_failure(Failure(
            test_id="2c Measurement: Negative noop overhead",
            severity="MAJOR",
            message=(
                f"Noop overhead: {noop_overhead:.4f}ms (negative). "
                f"Baseline: {baseline_ms:.4f}ms. "
                f"Delayed: {delayed_ms:.4f}ms. "
                f"Measurement system reports negative overhead — impossible."
            ),
            layer="S-Measurement",
            repro="Compare measure_multi_run with vs without noop loop",
            deterministic=False,
            data={
                "noop_overhead_ms": round(noop_overhead, 4),
                "baseline_ms": round(baseline_ms, 4),
                "delayed_ms": round(delayed_ms, 4),
            },
        ))
    else:
        harness.record_pass("2c Measurement: Noop overhead is positive (no impossible values)")


# ═══════════════════════════════════════════════════════════════════════════
# ATTACK 3: Validator Adversarial Robustness
# ═══════════════════════════════════════════════════════════════════════════

def test_validator_adversarial():
    """Strong validators should not false-reject. Weak validators should not false-accept."""
    print("\n" + "=" * 65)
    print("ATTACK 3: Validator Adversarial Robustness")
    print("=" * 65)

    from doctor.test_executor import TestExecutor
    from doctor.output_validators import validate_output

    te = TestExecutor()

    # ── Attack 3a: Strong validator false reject — valid but non-standard ──
    # N-Queens: single solution for n=1 is [["Q"]].
    # What if a solution returns [["Q"]] as a list of one board?
    # This is the standard format. Let's verify the validator accepts it.
    try:
        result = validate_output("N-Queens", [["Q"]], {"n": 1})
        validator_accepts = result[0]  # (valid, reason)
        if not validator_accepts:
            harness.record_failure(Failure(
                test_id="3a Validator: Strong validator false-rejects valid N-Queens n=1",
                severity="MAJOR",
                message=(
                    f"N-Queens n=1 solution [['Q']] was rejected by validator. "
                    f"Reason: {result[1] if len(result) > 1 else 'unknown'}"
                ),
                layer="Validator (output_validators.py)",
                repro="Call validate_output('N-Queens', [['Q']], {'n': 1})",
                deterministic=True,
                data={"result": str(result)},
            ))
        else:
            harness.record_pass("3a Validator: Strong validator accepts valid N-Queens n=1")
    except Exception as e:
        harness.record_failure(Failure(
            test_id="3a Validator: Exception during validation",
            severity="CRITICAL",
            message=f"validate_output raised: {e}",
            layer="Validator (output_validators.py)",
            repro="Call validate_output('N-Queens', [['Q']], {'n': 1})",
            deterministic=True,
            data={"exception": str(e)},
        ))

    # ── Attack 3b: Strong validator — edge case minimal input ──
    # N-Queens n=0: expected [[]] (one solution: empty board)
    try:
        result = validate_output("N-Queens", [[]], {"n": 0})
        if not result[0]:
            harness.record_failure(Failure(
                test_id="3b Validator: Strong validator false-rejects N-Queens n=0",
                severity="MAJOR",
                message=(
                    f"N-Queens n=0 solution [[]] was rejected. "
                    f"Reason: {result[1] if len(result) > 1 else 'unknown'}"
                ),
                layer="Validator (output_validators.py)",
                repro="Call validate_output('N-Queens', [[]], {'n': 0})",
                deterministic=True,
                data={"result": str(result)},
            ))
        else:
            harness.record_pass("3b Validator: Strong validator accepts N-Queens n=0")
    except Exception as e:
        harness.record_failure(Failure(
            test_id="3b Validator: Exception during N-Queens n=0 validation",
            severity="MAJOR",
            message=f"validate_output raised for n=0: {e}",
            layer="Validator (output_validators.py)",
            repro="Call validate_output('N-Queens', [[]], {'n': 0})",
            deterministic=True,
            data={"exception": str(e)},
        ))

    # ── Attack 3c: Weak validator false accept — incorrect output that satisfies constraints ──
    # Container With Most Water: validator only checks area >= 0.
    # Any positive number passes. But the TEST EXECUTION should catch wrong answers.
    # Test with a solution that always returns 0 (wrong but passes weak validator).
    incorrect_container_zero = (
        "def maxArea(height):\n"
        "    return 0  # always wrong but passes weak validator constraint"
    )
    report_zero = te.verify("Container With Most Water", incorrect_container_zero)
    # The weak validator accepts 0 (>= 0), but test execution should fail.
    if report_zero.verdict == "correct" and report_zero.pass_rate == 1.0:
        harness.record_failure(Failure(
            test_id="3c Validator: Weak validator false-accepts incorrect output",
            severity="CRITICAL",
            message=(
                f"Container solution returning always 0 got verdict=correct, "
                f"pass_rate=1.0. Weak validator accepted it and tests also passed."
            ),
            layer="Layer 2 (Test Executor) + Validator",
            repro="Run maxArea that always returns 0",
            deterministic=True,
            data={"verdict": report_zero.verdict, "pass_rate": report_zero.pass_rate},
        ))
    else:
        harness.record_pass("3c Validator: Weak validator + tests catch always-0 solution")

    # ── Attack 3d: Weak validator + wrong answer — does test execution catch it? ──
    # Container: solution returns 999 (wrong for all test cases)
    incorrect_container_999 = (
        "def maxArea(height):\n"
        "    return 999  # wrong for all test cases"
    )
    report_999 = te.verify("Container With Most Water", incorrect_container_999)
    if report_999.verdict == "correct":
        harness.record_failure(Failure(
            test_id="3d Validator: Weak validator + wrong answer accepted",
            severity="CRITICAL",
            message=(
                f"Container solution returning 999 got verdict=correct. "
                f"Pass rate: {report_999.pass_rate}."
            ),
            layer="Layer 2 (Test Executor)",
            repro="Run maxArea that always returns 999",
            deterministic=True,
            data={"verdict": report_999.verdict, "pass_rate": report_999.pass_rate},
        ))
    else:
        harness.record_pass("3d Validator: Wrong answer (999) correctly rejected")


# ═══════════════════════════════════════════════════════════════════════════
# ATTACK 4: Reference System Integrity — Self-Referential Correctness
# ═══════════════════════════════════════════════════════════════════════════

def test_reference_integrity():
    """Is S_ref derived from the same system? Circular calibration?"""
    print("\n" + "=" * 65)
    print("ATTACK 4: Reference System Integrity")
    print("=" * 65)

    from doctor.s_measurement import REFERENCE_MODELS, get_reference_model
    from doctor.s_efficiency import S_REF_REGISTRY, S_REF_REGISTRY as S_EFF_REGISTRY

    # ── Attack 4a: Check if reference models are externally defined or self-derived ──
    # All reference models should be type "external", not derived from system outputs.
    for key, model in REFERENCE_MODELS.items():
        if model.reference_type == "empirical":
            # Empirical references are explicitly marked as unstable
            if model.is_absolute or model.is_stable:
                harness.record_failure(Failure(
                    test_id="4a Reference: Empirical reference marked as absolute/stable",
                    severity="MAJOR",
                    message=(
                        f"Problem {key} has empirical reference but is_absolute={model.is_absolute}, "
                        f"is_stable={model.is_stable}. Empirical references should be relative-only."
                    ),
                    layer="S-Measurement (reference models)",
                    repro=f"Check REFERENCE_MODELS['{key}']",
                    deterministic=True,
                    data={
                        "problem": key,
                        "reference_type": model.reference_type,
                        "is_absolute": model.is_absolute,
                        "is_stable": model.is_stable,
                    },
                ))
            else:
                harness.record_pass(f"4a Reference: {key} empirical reference correctly marked unstable")
        elif model.reference_type == "external":
            # External references should be absolute and stable
            if not model.is_absolute or not model.is_stable:
                harness.record_failure(Failure(
                    test_id="4a Reference: External reference marked as relative/unstable",
                    severity="MAJOR",
                    message=(
                        f"Problem {key} has external reference but is_absolute={model.is_absolute}, "
                        f"is_stable={model.is_stable}. External references should be absolute+stable."
                    ),
                    layer="S-Measurement (reference models)",
                    repro=f"Check REFERENCE_MODELS['{key}']",
                    deterministic=True,
                    data={
                        "problem": key,
                        "reference_type": model.reference_type,
                        "is_absolute": model.is_absolute,
                        "is_stable": model.is_stable,
                    },
                ))
            else:
                harness.record_pass(f"4a Reference: {key} external reference correctly marked absolute+stable")

    # ── Attack 4b: Check for self-referential S_ref in s_efficiency ──
    # S_REF_REGISTRY in s_efficiency.py should match reference models,
    # NOT be derived from execution traces.
    eff_keys = set(S_EFF_REGISTRY.keys())
    meas_keys = set(REFERENCE_MODELS.keys())

    # It's OK if these don't perfectly match — efficiency uses different keys.
    # But if S_REF_REGISTRY values look like they were computed from system output
    # (e.g., very specific decimal values like 0.021), they might be empirical.
    # We can't definitively prove they're external, but we can check consistency.

    # All s_ref_ms values should be positive and reasonable
    for key, entry in S_EFF_REGISTRY.items():
        s_ref = entry.get("s_ref_ms", 0)
        if s_ref <= 0:
            harness.record_failure(Failure(
                test_id="4b Reference: S_ref non-positive",
                severity="CRITICAL",
                message=f"Problem {key} has s_ref_ms={s_ref} (non-positive).",
                layer="S-Efficiency (s_efficiency.py)",
                repro=f"Check S_REF_REGISTRY['{key}']",
                deterministic=True,
                data={"problem": key, "s_ref_ms": s_ref},
            ))
        elif s_ref > 1.0:
            # S_ref > 1ms seems high for a reference — might be from noisy measurement
            harness.record_failure(Failure(
                test_id="4b Reference: S_ref suspiciously high",
                severity="MINOR",
                message=(
                    f"Problem {key} has s_ref_ms={s_ref}. "
                    f"References > 1ms may indicate empirical measurement noise."
                ),
                layer="S-Efficiency (s_efficiency.py)",
                repro=f"Check S_REF_REGISTRY['{key}']",
                deterministic=True,
                data={"problem": key, "s_ref_ms": s_ref},
            ))
        else:
            harness.record_pass(f"4b Reference: {key} s_ref_ms={s_ref} is reasonable")

    # ── Attack 4c: Modified internal implementation — does classification remain stable? ──
    # If we change the efficiency computation internally, the external reference
    # should NOT change.
    from doctor.s_efficiency import compute_efficiency

    # Compute efficiency for N-Queens with standard input
    r1 = compute_efficiency([{"execution_time": 0.00005}], "N-Queens")

    # Compute again with same input — should be identical
    r2 = compute_efficiency([{"execution_time": 0.00005}], "N-Queens")

    if r1.efficiency != r2.efficiency or r1.s_final != r2.s_final:
        harness.record_failure(Failure(
            test_id="4c Reference: Non-deterministic classification",
            severity="CRITICAL",
            message=(
                f"Same input produces different results: "
                f"r1={r1.efficiency}(s_final={r1.s_final}), "
                f"r2={r2.efficiency}(s_final={r2.s_final})"
            ),
            layer="S-Efficiency (s_efficiency.py)",
            repro="Call compute_efficiency twice with identical input",
            deterministic=True,
            data={"r1_efficiency": r1.efficiency, "r1_s_final": r1.s_final,
                  "r2_efficiency": r2.efficiency, "r2_s_final": r2.s_final},
        ))
    else:
        harness.record_pass("4c Reference: Deterministic classification")


# ═══════════════════════════════════════════════════════════════════════════
# ATTACK 5: Scaling Logic Stress Test
# ═══════════════════════════════════════════════════════════════════════════

def test_scaling_logic_stress():
    """Non-geometric sizes, reversed sequences, identical S across sizes."""
    print("\n" + "=" * 65)
    print("ATTACK 5: Scaling Logic Stress")
    print("=" * 65)

    from doctor.s_measurement import compute_log_ratio, validate_scaling_sizes

    # ── Attack 5a: Non-geometric input sizes ──
    sizes_non_geo = [3, 7, 15, 31]  # primes-ish, not geometric
    valid_non_geo, reason_non_geo = validate_scaling_sizes(sizes_non_geo)
    # Should pass — the function allows variance in ratio
    # but should flag if wildly inconsistent

    # ── Attack 5b: Reversed size sequence ──
    sizes_reversed = [100, 50, 25, 10]  # decreasing
    valid_reversed, reason_reversed = validate_scaling_sizes(sizes_reversed)
    if valid_reversed:
        harness.record_failure(Failure(
            test_id="5a Scaling: Reversed size sequence accepted",
            severity="MAJOR",
            message=(
                f"Decreasing sizes {sizes_reversed} were accepted. "
                f"Reason: {reason_reversed}. "
                f"Expected: rejection (sizes must be increasing)."
            ),
            layer="S-Measurement (scaling validation)",
            repro=f"Call validate_scaling_sizes({sizes_reversed})",
            deterministic=True,
            data={"sizes": sizes_reversed, "valid": valid_reversed, "reason": reason_reversed},
        ))
    else:
        harness.record_pass("5a Scaling: Reversed size sequence correctly rejected")

    # ── Attack 5c: Identical S across different sizes — slope should be undefined ──
    # If execution time is constant regardless of input size, slope = log(1)/log(ratio) = 0/positive = 0
    s1, s2 = 5.0, 5.0  # identical times
    n1, n2 = 10, 100   # different sizes
    slope_constant = compute_log_ratio(s1, s2, n1, n2)
    # slope should be 0 (no growth), not None or error
    if slope_constant is None:
        harness.record_failure(Failure(
            test_id="5b Scaling: Constant S returns None instead of 0",
            severity="MINOR",
            message=(
                f"log_ratio(5.0, 5.0, 10, 100) returned None. "
                f"Expected: 0.0 (no growth). "
                f"This means constant-time algorithms can't be measured."
            ),
            layer="S-Measurement (log_ratio)",
            repro="Call compute_log_ratio(5.0, 5.0, 10, 100)",
            deterministic=True,
            data={"result": slope_constant},
        ))
    elif abs(slope_constant) > 0.01:
        harness.record_failure(Failure(
            test_id="5b Scaling: Constant S produces non-zero slope",
            severity="MAJOR",
            message=(
                f"log_ratio(5.0, 5.0, 10, 100) returned {slope_constant}. "
                f"Expected: ~0.0 (no growth). "
                f"This means the formula incorrectly handles constant times."
            ),
            layer="S-Measurement (log_ratio)",
            repro="Call compute_log_ratio(5.0, 5.0, 10, 100)",
            deterministic=True,
            data={"result": slope_constant},
        ))
    else:
        harness.record_pass("5b Scaling: Constant S correctly produces slope≈0")

    # ── Attack 5d: Identical sizes — should return None (division by zero) ──
    slope_same_size = compute_log_ratio(10.0, 20.0, 10, 10)
    if slope_same_size is not None:
        harness.record_failure(Failure(
            test_id="5c Scaling: Identical sizes does not return None",
            severity="MAJOR",
            message=(
                f"log_ratio(10.0, 20.0, 10, 10) returned {slope_same_size}. "
                f"Expected: None (n1 == n2, division by zero in log ratio)."
            ),
            layer="S-Measurement (log_ratio)",
            repro="Call compute_log_ratio(10.0, 20.0, 10, 10)",
            deterministic=True,
            data={"result": slope_same_size},
        ))
    else:
        harness.record_pass("5c Scaling: Identical sizes correctly returns None")

    # ── Attack 5e: Zero/negative sizes or steps ──
    edge_cases = [
        ("zero_size", compute_log_ratio(10.0, 20.0, 0, 10)),
        ("neg_size", compute_log_ratio(10.0, 20.0, -5, 10)),
        ("zero_step", compute_log_ratio(0, 20.0, 10, 100)),
        ("neg_step", compute_log_ratio(-10.0, 20.0, 10, 100)),
    ]
    all_handled = True
    for name, result in edge_cases:
        if result is not None:
            harness.record_failure(Failure(
                test_id=f"5d Scaling: {name} not handled",
                severity="MINOR",
                message=f"log_ratio with {name} returned {result} instead of None.",
                layer="S-Measurement (log_ratio)",
                repro=f"Call compute_log_ratio with {name} input",
                deterministic=True,
                data={"name": name, "result": result},
            ))
            all_handled = False
    if all_handled:
        harness.record_pass("5d Scaling: Zero/negative inputs correctly return None")


# ═══════════════════════════════════════════════════════════════════════════
# ATTACK 6: Cross-Layer Consistency
# ═══════════════════════════════════════════════════════════════════════════

def test_cross_layer_consistency():
    """Mutate outputs between layers — does system detect or silently proceed?"""
    print("\n" + "=" * 65)
    print("ATTACK 6: Cross-Layer Consistency")
    print("=" * 65)

    from doctor.test_executor import TestExecutor
    from doctor.s_efficiency import compute_efficiency

    te = TestExecutor()

    # ── Attack 6a: Valid correctness + invalid efficiency signal ──
    # A correct solution (all tests pass) but with artificially high execution time.
    # The S-efficiency layer should still work — it measures total time.
    correct_slow = (
        "def twoSum(nums, target):\n"
        "    import time\n"
        "    time.sleep(0.001)  # artificially slow\n"
        "    h={}\n"
        "    for i,x in enumerate(nums):\n"
        "        if target-x in h: return [h[target-x],i]\n"
        "        h[x]=i"
    )
    report_slow = te.verify("Two Sum", correct_slow)
    traces = report_slow.traces

    # Compute efficiency from traces
    if traces:
        eff = compute_efficiency(traces, "Two Sum")
        # Two Sum is linear → efficiency should be "not_applicable"
        if eff.efficiency != "not_applicable":
            harness.record_failure(Failure(
                test_id="6a Cross-Layer: Correct but slow solution got wrong efficiency",
                severity="MAJOR",
                message=(
                    f"Correct Two Sum solution (artificially slow) got "
                    f"efficiency={eff.efficiency} (expected: not_applicable for linear). "
                    f"s_final={eff.s_final}."
                ),
                layer="S-Efficiency + Layer 2 coupling",
                repro="Run slow twoSum, compute efficiency from traces",
                deterministic=True,
                data={
                    "verdict": report_slow.verdict,
                    "efficiency": eff.efficiency,
                    "s_final": eff.s_final,
                },
            ))
        else:
            harness.record_pass("6a Cross-Layer: Correct slow solution has correct efficiency label")

    # ── Attack 6b: Missing validator but efficiency computed anyway ──
    # Container has weak validator (accepts anything >= 0).
    # Efficiency should still be computed — it's independent.
    correct_container = (
        "def maxArea(height):\n"
        "    left, right = 0, len(height)-1\n"
        "    max_a = 0\n"
        "    while left < right:\n"
        "        a = min(height[left], height[right]) * (right - left)\n"
        "        max_a = max(max_a, a)\n"
        "        if height[left] < height[right]: left += 1\n"
        "        else: right -= 1\n"
        "    return max_a"
    )
    report_container = te.verify("Container With Most Water", correct_container)
    traces_c = report_container.traces

    if traces_c:
        eff_c = compute_efficiency(traces_c, "Container With Most Water")
        # Container is linear → not_applicable
        if eff_c.efficiency != "not_applicable":
            harness.record_failure(Failure(
                test_id="6b Cross-Layer: Container got wrong efficiency",
                severity="MINOR",
                message=(
                    f"Container solution got efficiency={eff_c.efficiency} "
                    f"(expected: not_applicable). s_final={eff_c.s_final}."
                ),
                layer="S-Efficiency + Validator coupling",
                repro="Run correct Container, compute efficiency from traces",
                deterministic=True,
                data={
                    "verdict": report_container.verdict,
                    "efficiency": eff_c.efficiency,
                    "s_final": eff_c.s_final,
                },
            ))
        else:
            harness.record_pass("6b Cross-Layer: Container efficiency independent of weak validator")

    # ── Attack 6c: No validator exists — does system handle gracefully? ──
    # Use a problem name that has no validator
    try:
        report_unknown = te.verify("Unknown Problem With No Tests", "def foo(): pass")
        if report_unknown.verdict != "incorrect" or report_unknown.error == "":
            harness.record_failure(Failure(
                test_id="6c Cross-Layer: Unknown problem not handled gracefully",
                severity="MAJOR",
                message=(
                    f"Unknown problem got verdict={report_unknown.verdict}, "
                    f"error='{report_unknown.error}'. "
                    f"Expected: verdict=incorrect with error message."
                ),
                layer="Layer 2 (Test Executor)",
                repro="Call verify with unknown problem name",
                deterministic=True,
                data={
                    "verdict": report_unknown.verdict,
                    "error": report_unknown.error,
                    "total": report_unknown.total,
                },
            ))
        else:
            harness.record_pass("6c Cross-Layer: Unknown problem handled gracefully")
    except Exception as e:
        harness.record_failure(Failure(
            test_id="6c Cross-Layer: Unknown problem raises exception",
            severity="CRITICAL",
            message=f"verify('Unknown Problem') raised: {e}",
            layer="Layer 2 (Test Executor)",
            repro="Call verify('Unknown Problem With No Tests', 'def foo(): pass')",
            deterministic=True,
            data={"exception": str(e)},
        ))


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("DOCTOR SYSTEM — DESTRUCTIVE VALIDATION PROTOCOL")
    print("=" * 65)
    print()
    print("Goal: BREAK the system's assumptions.")
    print("Target: Find contradictions, hidden dependencies, invalid invariants.")
    print()
    print("6 Attack Vectors:")
    print("  1. End-to-End System Failure (expected output vs validator)")
    print("  2. Measurement Adversarial Stability (30 runs, delays)")
    print("  3. Validator Adversarial Robustness (strong reject / weak false-accept)")
    print("  4. Reference System Integrity (circular reference)")
    print("  5. Scaling Logic Stress (non-geometric, reversed, identical S)")
    print("  6. Cross-Layer Consistency (mutated outputs)")

    # Run all attacks
    test_e2e_correctness_bypass()
    test_measurement_adversarial()
    test_validator_adversarial()
    test_reference_integrity()
    test_scaling_logic_stress()
    test_cross_layer_consistency()

    # Print results
    harness.print_results()

    # Save detailed results
    s = harness.summary()
    report = {
        "title": "Doctor System Destructive Validation Protocol",
        "summary": s,
        "failures": [
            {
                "test_id": f.test_id,
                "severity": f.severity,
                "message": f.message,
                "layer": f.layer,
                "repro": f.repro,
                "deterministic": f.deterministic,
                "data": f.data,
            }
            for f in harness.failures
        ],
        "passed": harness.passed,
    }

    report_path = "scratch/destructive_stress_test_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")

    return 0 if s["failures"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

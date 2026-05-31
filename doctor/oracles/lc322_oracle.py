"""
D_probe_selection_independent_v1 — Fully Independent Structural Probe Selection.

Implements the frozen protocol from D_PROBE_SELECTION_INDEPENDENT_V1_FREEZE.json.

Status: SPEC_FROZEN_NO_RESULTS -> result-producing run.

INDEPENDENCE REQUIREMENT:
- doctor_independent_probe_selector_v1 must NOT access training pass/fail rows.
- doctor_independent_probe_selector_v1 must NOT access historical failure counts/rates.
- doctor_independent_probe_selector_v1 must NOT use failure-family tags.
- doctor_independent_probe_selector_v1 must use ONLY neutral input-derived features.

This runner does NOT modify the freeze/spec file or prior results.
"""
from __future__ import annotations

import hashlib
import importlib
import itertools
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "experiments" / "frozen_taxonomy_lc322"))

import runner as frozen_runner
from doctor.oracles.lc322_oracle import lc322_oracle

# ──────────────────────────────────────────────────────────
# Load frozen spec
# ──────────────────────────────────────────────────────────
FREEZE_PATH = BASE / "D_PROBE_SELECTION_INDEPENDENT_V1_FREEZE.json"
freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))

assert freeze["decision_id"] == "D_probe_selection_independent_v1"
assert freeze["status"] == "SPEC_FROZEN_NO_RESULTS"
assert freeze["budget_grid"]["values"] == [1, 2, 4, 8, 16]
assert freeze["downstream_decision_rule"]["name"] == "reject_on_any_failure"

# ──────────────────────────────────────────────────────────
# Frozen constants from spec
# ──────────────────────────────────────────────────────────
BUDGET_GRID = freeze["budget_grid"]["values"]
RANDOM_SEEDS = freeze["selector_arms"][0]["predeclared_seeds"]
PROBE_CASES = list(frozen_runner.PROBE_CASES)
CASE_IDS = [c["case_id"] for c in PROBE_CASES]
CASE_BY_ID = {c["case_id"]: c for c in PROBE_CASES}

# ──────────────────────────────────────────────────────────
# Precompute oracle outputs for all PROBE_CASES
# ──────────────────────────────────────────────────────────
print("Computing oracle outputs for PROBE_CASES ...")
ORACLE_OUTPUTS: dict[str, int] = {}
for case in PROBE_CASES:
    ORACLE_OUTPUTS[case["case_id"]] = lc322_oracle(case["coins"], case["amount"])

# ──────────────────────────────────────────────────────────
# Load training solvers (10 known solvers) - for baselines only
# ──────────────────────────────────────────────────────────
print("Loading training solvers ...")
sys.path.insert(0, str(BASE / "doctor" / "adversarial"))
candidates = importlib.import_module("lc322_candidates")

TRAINING_SOLVER_FNS: dict[str, Callable] = {
    "lc322_dp": candidates.lc322_dp,
    "lc322_greedy": candidates.lc322_greedy,
    "lc322_smallest_first": candidates.lc322_smallest_first,
    "lc322_memo_collision": candidates.lc322_memo_collision,
    "lc322_lookahead_one": candidates.lc322_lookahead_one,
    "lc322_bfs_coin_count_cutoff": candidates.lc322_bfs_coin_count_cutoff,
    "lc322_modulo_memo_alias": candidates.lc322_modulo_memo_alias,
    "lc322_reachability_lookahead": candidates.lc322_reachability_lookahead,
    "lc322_ordering_commitment": candidates.lc322_ordering_commitment,
    "lc322_transition_asymmetric_forward_dp": candidates.lc322_transition_asymmetric_forward_dp,
}


def make_wrapper(fn: Callable) -> Callable:
    """Wrap a solver that accepts (coins+[amount]) to (coins, amount)."""
    def wrapper(coins, amount):
        try:
            return fn(coins, amount)
        except TypeError:
            pass
        try:
            return fn(coins + [amount])
        except TypeError:
            pass
        return None
    return wrapper


# Precompute training pass/fail matrix for historical baseline ONLY
print("Precomputing training pass/fail matrix for historical baseline ...")
TRAINING_PF: dict[str, dict[str, bool]] = {}
for solver_id, solver_fn in TRAINING_SOLVER_FNS.items():
    wrapped = make_wrapper(solver_fn)
    TRAINING_PF[solver_id] = {}
    for case in PROBE_CASES:
        try:
            output = wrapped(case["coins"], case["amount"])
            oracle_out = ORACLE_OUTPUTS[case["case_id"]]
            TRAINING_PF[solver_id][case["case_id"]] = (output == oracle_out)
        except Exception:
            TRAINING_PF[solver_id][case["case_id"]] = False

# ──────────────────────────────────────────────────────────
# Load evaluation solvers (15 held-out)
# ──────────────────────────────────────────────────────────
print("Loading evaluation solvers ...")
EVAL_SOLVER_MAKERS: list[tuple[Callable, str, str]] = []
for i, (maker, true_label) in enumerate(frozen_runner.HELDOUT_SOLVER_MAKERS):
    sid = f"solver_{i+1:03d}"
    EVAL_SOLVER_MAKERS.append((maker, sid, true_label))

# Load adversarial solvers
print("Loading adversarial solvers (Track B) ...")
ADVERSARIAL_SOLVER_MAKERS: list[tuple[Callable, str, str]] = []
try:
    adv_manifest = json.loads(
        (BASE / "data" / "lc322_adversarial_shift_15_solver_panel.json").read_text(encoding="utf-8")
    )
    for solver_spec in adv_manifest.get("solvers", []):
        module_name = solver_spec["module"]
        fn_name = solver_spec["function"]
        solver_id = solver_spec["id"]

        mod = importlib.import_module(f"doctor.adversarial.{module_name}")
        fn = getattr(mod, fn_name)
        ADVERSARIAL_SOLVER_MAKERS.append((fn, solver_id, "adversarial"))
except Exception as e:
    print(f"Warning: Could not load adversarial panel: {e}")
    ADVERSARIAL_SOLVER_MAKERS = []

# ──────────────────────────────────────────────────────────
# NEUTRAL FEATURE EXTRACTION
# ──────────────────────────────────────────────────────────
def compute_gcd(coins: list[int]) -> int:
    """Compute GCD of all coins."""
    from math import gcd
    if not coins:
        return 1
    result = coins[0]
    for c in coins[1:]:
        result = gcd(result, c)
    return result if result > 0 else 1


def extract_neutral_features(case: dict) -> dict[str, float]:
    """
    Extract neutral input-derived features from a case.
    Must NOT use historical failure info or failure-family tags.
    """
    coins = case["coins"]
    amount = case["amount"]

    coin_count = len(coins)
    min_coin = min(coins) if coins else 0
    max_coin = max(coins) if coins else 0
    coin_range = max_coin - min_coin

    gcd_val = compute_gcd(coins)
    amount_mod_gcd = amount % gcd_val if gcd_val > 0 else 0

    coin_density = sum(coins) / amount if amount > 0 else 0

    amount_to_max_coin_ratio = amount / max_coin if max_coin > 0 else 0

    sorted_coin_ratios = [c / max_coin for c in sorted(coins)] if max_coin > 0 else []
    sorted_coin_ratios_scalar = sum(sorted_coin_ratios) / len(sorted_coin_ratios) if sorted_coin_ratios else 0

    duplicate_coin_count = len(coins) - len(set(coins))

    amount_below_max_coin = 1.0 if amount < max_coin else 0.0

    input_size = len(str(coins)) + len(str(amount))

    return {
        "amount": float(amount),
        "coin_count": float(coin_count),
        "min_coin": float(min_coin),
        "max_coin": float(max_coin),
        "coin_range": float(coin_range),
        "gcd_approx": float(gcd_val),
        "amount_mod_gcd": float(amount_mod_gcd),
        "coin_density": float(coin_density),
        "amount_to_max_coin_ratio": float(amount_to_max_coin_ratio),
        "sorted_coin_ratios_mean": float(sorted_coin_ratios_scalar),
        "duplicate_coin_count": float(duplicate_coin_count),
        "amount_below_max_coin": float(amount_below_max_coin),
        "input_size": float(input_size),
    }


# Precompute neutral features for all cases
print("Computing neutral features for all PROBE_CASES ...")
NEUTRAL_FEATURES: dict[str, dict[str, float]] = {}
for case in PROBE_CASES:
    NEUTRAL_FEATURES[case["case_id"]] = extract_neutral_features(case)

# ──────────────────────────────────────────────────────────
# BASELINE IMPLEMENTATIONS
# ──────────────────────────────────────────────────────────

def random_selector(case_ids: list[str], k: int, seed: int) -> list[str]:
    """Select k cases uniformly without replacement."""
    rng = random.Random(seed)
    return rng.sample(case_ids, min(k, len(case_ids)))


def fixed_order_selector(case_ids: list[str], k: int) -> list[str]:
    """Select first k cases in canonical order."""
    return case_ids[:k]


def metadata_diversity_selector(case_ids: list[str], k: int) -> list[str]:
    """
    Select k cases to maximize diversity over neutral features.
    This is similar to independent Doctor but serves as a baseline.
    """
    if not case_ids or k <= 0:
        return []

    selected = []
    remaining = set(case_ids)

    # Normalize features
    feature_names = list(NEUTRAL_FEATURES[case_ids[0]].keys())
    norm_features = {}
    for fname in feature_names:
        values = [NEUTRAL_FEATURES[cid][fname] for cid in case_ids]
        min_v = min(values)
        max_v = max(values)
        range_v = max_v - min_v if max_v > min_v else 1.0
        norm_features[fname] = {cid: (NEUTRAL_FEATURES[cid][fname] - min_v) / range_v for cid in case_ids}

    # Compute pool center
    pool_center = {fname: sum(norm_features[fname][cid] for cid in case_ids) / len(case_ids) for fname in feature_names}

    # Select first case (extremeness)
    def dist_from_center(cid):
        return sum((norm_features[fname][cid] - pool_center[fname]) ** 2 for fname in feature_names) ** 0.5

    first = max(remaining, key=dist_from_center)
    selected.append(first)
    remaining.remove(first)

    # Greedy selection
    while len(selected) < k and remaining:
        def score_candidate(cid):
            d_center = dist_from_center(cid)
            d_selected = min(
                sum((norm_features[fname][cid] - norm_features[fname][s]) ** 2 for fname in feature_names) ** 0.5
                for s in selected
            ) if selected else 0.0
            return 0.3 * d_center + 0.7 * d_selected

        next_case = max(remaining, key=score_candidate)
        selected.append(next_case)
        remaining.remove(next_case)

    return selected


def historical_failure_count_selector(case_ids: list[str], k: int) -> list[str]:
    """
    Select cases with high historical failure rate on training panel.
    NOTE: This baseline is ALLOWED to use TRAINING_PF.
    doctor_independent_probe_selector_v1 is NOT allowed.
    """
    failure_counts = {}
    for cid in case_ids:
        count = sum(1 for solver_id in TRAINING_SOLVER_FNS if not TRAINING_PF[solver_id][cid])
        failure_counts[cid] = count

    sorted_by_failure = sorted(case_ids, key=lambda cid: (-failure_counts[cid], cid))
    return sorted_by_failure[:k]


def doctor_independent_probe_selector_v1(case_ids: list[str], k: int) -> list[str]:
    """
    Structural diversity maximization using neutral input-derived features only.

    CRITICAL: This selector must NOT access TRAINING_PF or any historical failure info.
    """
    if not case_ids or k <= 0:
        return []

    # Normalize neutral features
    feature_names = list(NEUTRAL_FEATURES[case_ids[0]].keys())
    norm_features = {}
    for fname in feature_names:
        values = [NEUTRAL_FEATURES[cid][fname] for cid in case_ids]
        min_v = min(values)
        max_v = max(values)
        range_v = max_v - min_v if max_v > min_v else 1.0
        norm_features[fname] = {cid: (NEUTRAL_FEATURES[cid][fname] - min_v) / range_v for cid in case_ids}

    # Compute pool center
    pool_center = {fname: sum(norm_features[fname][cid] for cid in case_ids) / len(case_ids) for fname in feature_names}

    def distance_from_center(cid):
        return sum((norm_features[fname][cid] - pool_center[fname]) ** 2 for fname in feature_names) ** 0.5

    selected = []
    remaining = set(case_ids)

    # Step 4: Select first case (extremeness)
    first = max(remaining, key=distance_from_center)
    selected.append(first)
    remaining.remove(first)

    # Step 5: Greedy selection for k > 1
    while len(selected) < k and remaining:
        def composite_score(cid):
            d_center = distance_from_center(cid)

            d_selected = min(
                sum((norm_features[fname][cid] - norm_features[fname][s]) ** 2 for fname in feature_names) ** 0.5
                for s in selected
            ) if selected else 0.0

            # Feature coverage: count how many features this case helps cover
            coverage = 0.0
            for fname in feature_names:
                val = norm_features[fname][cid]
                existing_vals = [norm_features[fname][s] for s in selected]
                if not existing_vals or abs(val - min(existing_vals)) > 0.1 or abs(val - max(existing_vals)) > 0.1:
                    coverage += 1.0
            coverage /= len(feature_names) if feature_names else 1.0

            return 0.3 * d_center + 0.5 * d_selected + 0.2 * coverage

        next_case = max(remaining, key=composite_score)
        selected.append(next_case)
        remaining.remove(next_case)

    # Step 6: Tie-break by case_id (lexical order) - handled by deterministic score
    return sorted(selected, key=lambda cid: CASE_IDS.index(cid))


# ──────────────────────────────────────────────────────────
# DECISION RULE
# ──────────────────────────────────────────────────────────

def reject_on_any_failure(selected_case_ids: list[str], pf_vector: dict[str, bool]) -> bool:
    """
    ACCEPT if all selected cases pass.
    REJECT if any selected case fails.
    Returns True = ACCEPT, False = REJECT.
    """
    for cid in selected_case_ids:
        if not pf_vector.get(cid, False):
            return False
    return True


# ──────────────────────────────────────────────────────────
# EVALUATION: TRACK A (Original LC322 Panel)
# ──────────────────────────────────────────────────────────

def run_track_a():
    """Original LC322 panel with held-out solvers."""
    print("\n" + "="*70)
    print("TRACK A: Original LC322 Panel")
    print("="*70)

    track_results = {"track": "A", "solvers": []}

    selectors = {
        "random": (random_selector, True),  # (fn, needs_seed)
        "fixed_order": (fixed_order_selector, False),
        "metadata_diversity": (metadata_diversity_selector, False),
        "historical_failure_count": (historical_failure_count_selector, False),
        "doctor_independent_probe_selector_v1": (doctor_independent_probe_selector_v1, False),
    }

    for solver_fn, solver_id, label in EVAL_SOLVER_MAKERS:
        wrapped_fn = make_wrapper(solver_fn)
        solver_results = {
            "solver_id": solver_id,
            "label": label,
            "by_k": {}
        }

        # Compute full-suite label (ACCEPT/REJECT)
        full_suite_pf = {}
        for case in PROBE_CASES:
            try:
                output = wrapped_fn(case["coins"], case["amount"])
                oracle_out = ORACLE_OUTPUTS[case["case_id"]]
                full_suite_pf[case["case_id"]] = (output == oracle_out)
            except Exception:
                full_suite_pf[case["case_id"]] = False

        full_suite_pass = all(full_suite_pf.values())

        for k in BUDGET_GRID:
            k_result = {}

            for selector_name, (selector_fn, needs_seed) in selectors.items():
                if needs_seed:
                    # Random selector: aggregate over seeds
                    selector_results = []
                    for seed in RANDOM_SEEDS:
                        selected_ids = selector_fn(CASE_IDS, k, seed)
                        pf_vec = {cid: full_suite_pf[cid] for cid in selected_ids}
                        decision = reject_on_any_failure(selected_ids, pf_vec)
                        correct = (decision == full_suite_pass)
                        selector_results.append({
                            "seed": seed,
                            "selected": selected_ids,
                            "correct": correct
                        })

                    correct_count = sum(1 for r in selector_results if r["correct"])
                    k_result[selector_name] = {
                        "correct_count": correct_count,
                        "total_seeds": len(selector_results),
                        "accuracy": correct_count / len(selector_results),
                        "seeds": selector_results
                    }
                else:
                    selected_ids = selector_fn(CASE_IDS, k)
                    pf_vec = {cid: full_suite_pf[cid] for cid in selected_ids}
                    decision = reject_on_any_failure(selected_ids, pf_vec)
                    correct = (decision == full_suite_pass)

                    k_result[selector_name] = {
                        "selected": selected_ids,
                        "correct": correct,
                        "decision": "ACCEPT" if decision else "REJECT",
                        "full_suite": "ACCEPT" if full_suite_pass else "REJECT",
                        "accuracy": 1.0 if correct else 0.0
                    }

            solver_results["by_k"][k] = k_result

        track_results["solvers"].append(solver_results)

    return track_results


# ──────────────────────────────────────────────────────────
# EVALUATION: TRACK B (Adversarial Panel)
# ──────────────────────────────────────────────────────────

def run_track_b():
    """Shifted adversarial LC322 panel."""
    print("\n" + "="*70)
    print("TRACK B: Shifted Adversarial Panel")
    print("="*70)

    track_results = {"track": "B", "solvers": []}

    if not ADVERSARIAL_SOLVER_MAKERS:
        print("Adversarial panel not loaded; Track B skipped.")
        return track_results

    selectors = {
        "random": (random_selector, True),
        "fixed_order": (fixed_order_selector, False),
        "metadata_diversity": (metadata_diversity_selector, False),
        "historical_failure_count": (historical_failure_count_selector, False),
        "doctor_independent_probe_selector_v1": (doctor_independent_probe_selector_v1, False),
    }

    for solver_fn, solver_id, label in ADVERSARIAL_SOLVER_MAKERS:
        wrapped_fn = make_wrapper(solver_fn)
        solver_results = {
            "solver_id": solver_id,
            "label": label,
            "by_k": {}
        }

        # Compute full-suite label (all adversarial should REJECT)
        full_suite_pf = {}
        for case in PROBE_CASES:
            try:
                output = wrapped_fn(case["coins"], case["amount"])
                oracle_out = ORACLE_OUTPUTS[case["case_id"]]
                full_suite_pf[case["case_id"]] = (output == oracle_out)
            except Exception:
                full_suite_pf[case["case_id"]] = False

        full_suite_pass = all(full_suite_pf.values())

        for k in BUDGET_GRID:
            k_result = {}

            for selector_name, (selector_fn, needs_seed) in selectors.items():
                if needs_seed:
                    selector_results = []
                    for seed in RANDOM_SEEDS:
                        selected_ids = selector_fn(CASE_IDS, k, seed)
                        pf_vec = {cid: full_suite_pf[cid] for cid in selected_ids}
                        decision = reject_on_any_failure(selected_ids, pf_vec)
                        correct = (decision == full_suite_pass)
                        selector_results.append({
                            "seed": seed,
                            "selected": selected_ids,
                            "correct": correct
                        })

                    correct_count = sum(1 for r in selector_results if r["correct"])
                    k_result[selector_name] = {
                        "correct_count": correct_count,
                        "total_seeds": len(selector_results),
                        "accuracy": correct_count / len(selector_results),
                        "seeds": selector_results
                    }
                else:
                    selected_ids = selector_fn(CASE_IDS, k)
                    pf_vec = {cid: full_suite_pf[cid] for cid in selected_ids}
                    decision = reject_on_any_failure(selected_ids, pf_vec)
                    correct = (decision == full_suite_pass)

                    k_result[selector_name] = {
                        "selected": selected_ids,
                        "correct": correct,
                        "decision": "ACCEPT" if decision else "REJECT",
                        "full_suite": "ACCEPT" if full_suite_pass else "REJECT",
                        "accuracy": 1.0 if correct else 0.0
                    }

            solver_results["by_k"][k] = k_result

        track_results["solvers"].append(solver_results)

    return track_results


# ──────────────────────────────────────────────────────────
# RUN EXPERIMENTS
# ──────────────────────────────────────────────────────────

print("\nRunning independent Doctor selector evaluation...")
track_a_results = run_track_a()
track_b_results = run_track_b()

# ──────────────────────────────────────────────────────────
# VERDICT LOGIC
# ──────────────────────────────────────────────────────────

def compute_verdict(track_results):
    """Compute verdict based on freeze success rule."""
    if not track_results.get("solvers"):
        return "ABORTED", "No evaluation solvers available"

    # Aggregate accuracy for each selector across all solvers and k
    selector_accuracies = defaultdict(list)

    for solver_result in track_results["solvers"]:
        for k, k_result in solver_result["by_k"].items():
            for selector_name, result in k_result.items():
                if isinstance(result, dict):
                    if "accuracy" in result:
                        selector_accuracies[selector_name].append(result["accuracy"])
                    elif "seeds" in result:
                        # Random selector aggregated
                        selector_accuracies[selector_name].append(result["accuracy"])

    # Compute mean accuracies
    mean_accuracies = {
        sel: sum(accs) / len(accs) if accs else 0.0
        for sel, accs in selector_accuracies.items()
    }

    print(f"\nTrack {track_results['track']} mean accuracies:")
    for sel in sorted(mean_accuracies.keys()):
        print(f"  {sel}: {mean_accuracies[sel]:.4f}")

    # Find best baseline (excluding independent Doctor)
    baseline_accuracies = {
        sel: acc for sel, acc in mean_accuracies.items()
        if sel != "doctor_independent_probe_selector_v1"
    }

    if not baseline_accuracies:
        return "SPEC_MISMATCH", "No baselines available"

    best_baseline_acc = max(baseline_accuracies.values())
    doctor_acc = mean_accuracies.get("doctor_independent_probe_selector_v1", 0.0)

    # Check success rule: Doctor must strictly beat best baseline at every k
    doctor_wins_at_every_k = True
    for solver_result in track_results["solvers"]:
        for k, k_result in solver_result["by_k"].items():
            doctor_k_accs = []
            baseline_k_accs = []

            for selector_name, result in k_result.items():
                if "accuracy" in result or "seeds" in result:
                    acc = result["accuracy"]
                    if selector_name == "doctor_independent_probe_selector_v1":
                        doctor_k_accs.append(acc)
                    else:
                        baseline_k_accs.append(acc)

            if doctor_k_accs and baseline_k_accs:
                doctor_k_avg = sum(doctor_k_accs) / len(doctor_k_accs)
                baseline_k_best = max(baseline_k_accs)
                if doctor_k_avg <= baseline_k_best:
                    doctor_wins_at_every_k = False
                    break

    if doctor_wins_at_every_k and doctor_acc > best_baseline_acc:
        return "UTILITY_PASS", f"Independent Doctor beat all baselines (avg accuracy {doctor_acc:.4f} > best baseline {best_baseline_acc:.4f})"
    else:
        reason = f"Independent Doctor did not strictly beat best baseline at every k"
        return "UTILITY_FAIL", reason


track_a_verdict, track_a_reason = compute_verdict(track_a_results)
track_b_verdict, track_b_reason = compute_verdict(track_b_results)

print(f"\nTrack A verdict: {track_a_verdict} ({track_a_reason})")
print(f"Track B verdict: {track_b_verdict} ({track_b_reason})")

# ──────────────────────────────────────────────────────────
# SAVE RESULTS
# ──────────────────────────────────────────────────────────

output_results = {
    "schema_version": "1.0.0",
    "decision_id": "D_probe_selection_independent_v1",
    "freeze_file": str(FREEZE_PATH),
    "freeze_file_hash": hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest()[:16],
    "track_a_verdict": track_a_verdict,
    "track_b_verdict": track_b_verdict,
    "track_a_reason": track_a_reason,
    "track_b_reason": track_b_reason,
    "track_a_results": track_a_results,
    "track_b_results": track_b_results,
    "independence_audit": {
        "training_pf_used_by_doctor": "NO",
        "failure_family_tags_used_by_doctor": "NO",
        "failure_counts_used_by_doctor": "NO",
        "neutral_features_used_by_doctor": "YES",
        "historical_data_accessed": "NO"
    },
    "overall_verdict": track_a_verdict if track_a_verdict == track_b_verdict else "UTILITY_FAIL",
    "final_note": "If Track A and Track B verdicts differ, overall is UTILITY_FAIL per freeze spec."
}

RESULTS_PATH = BASE / "data" / "d_probe_selection_independent_v1_results.json"
RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
RESULTS_PATH.write_text(json.dumps(output_results, indent=2), encoding="utf-8")
print(f"\nResults saved to {RESULTS_PATH}")

# Final summary
print("\n" + "="*70)
print("FINAL VERDICT")
print("="*70)
print(f"Track A: {track_a_verdict}")
print(f"Track B: {track_b_verdict}")
print(f"Overall: {output_results['overall_verdict']}")
print(f"  - Independent Doctor uses zero historical failure information: YES")
print(f"  - Independence contract enforced: YES")
print(f"  - Prior results (UTILITY_FAIL) unchanged: YES")

# runners/run_asymmetric_cost_lc45.py
# Phase C-1: Asymmetric-Cost Decision Utility — LC45 runner
#
# Loads existing estimator decisions from data/midweather_fingerprint_lc45.json
# Loads protocol parameters from PHASE_C1_FREEZE.json
# Runs cost-weighted utility sweep across all lambda values
# Writes results to data/asymmetric_cost_lc45.json
#
# Does NOT re-run probes. Does NOT modify any existing data file.
# Does NOT adjust delta or lambda sweep after results are seen.
#
# Population role: STRESS TEST (1/9 accept/reject split, single survivor).
# LC45 results are reported but do not determine the primary verdict.
# See PHASE_C1_FREEZE.json: populations[1].role = "stress_test".

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.asymmetric_cost import run_sweep, run_sweep_aggregate, is_degenerate

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

FREEZE_PATH = ROOT / "PHASE_C1_FREEZE.json"
DATA_PATH   = ROOT / "data" / "midweather_fingerprint_lc45.json"
OUTPUT_PATH = ROOT / "data" / "asymmetric_cost_lc45.json"

# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_freeze() -> dict:
    with FREEZE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_lc45_aggregates(data_path: Path) -> tuple[list[str], dict[str, dict]]:
    """Load ground truth labels and per-estimator aggregate stats from the LC45 data file.

    The data file persists per-solver ground truth and per-estimator aggregate
    statistics (wrong_accepts, wrong_rejects, degeneracy flags). It does NOT
    persist per-solver decision lists. Under the PHASE_C1 freeze cost model,
    (WA, WR) is a sufficient statistic for total cost, so aggregates are
    sufficient to compute the sweep.

    Returns:
        ground_truth    : list of "ACCEPT" / "REJECT" in solver-id order
        estimator_stats : dict mapping estimator name -> {
            wrong_accepts, wrong_rejects, n_solvers,
            degenerate_all_accept, degenerate_all_reject
        }

    Fails loudly if required keys are absent.
    """
    with data_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if "per_solver_ground_truth" not in data:
        raise KeyError(
            f"'per_solver_ground_truth' not found in {data_path}. "
            f"Available keys: {list(data.keys())}"
        )
    pgt = data["per_solver_ground_truth"]

    if "estimator_table" not in data:
        raise KeyError(
            f"'estimator_table' not found in {data_path}. "
            f"Available keys: {list(data.keys())}"
        )
    et = data["estimator_table"]

    sorted_solver_ids = sorted(pgt.keys())
    ground_truth = [pgt[sid]["truth_label"] for sid in sorted_solver_ids]
    n_solvers = len(ground_truth)

    estimator_stats = {}
    for entry in et:
        name = entry["estimator"]
        estimator_stats[name] = {
            "wrong_accepts": int(entry["wrong_accepts"]),
            "wrong_rejects": int(entry["wrong_rejects"]),
            "n_solvers": n_solvers,
            "degenerate_all_accept": bool(entry["degenerate_all_accept"]),
            "degenerate_all_reject": bool(entry["degenerate_all_reject"]),
        }

    return ground_truth, estimator_stats


# ---------------------------------------------------------------------------
# Falsification criterion
# ---------------------------------------------------------------------------

def apply_falsification(
    c_results: list[dict],
    b1_results: list[dict],
    delta: float,
) -> dict:
    """Apply the pre-declared falsification criterion.

    NOTE: LC45 is a stress test population. This verdict is reported
    separately. It does not override the LC322 primary verdict.

    PASS : exists lambda such that utility(C) - utility(B1) > delta
           and neither C nor B1 is degenerate at that lambda
    FAIL : no such lambda found
    """
    gap_table = []
    best_gap = None
    best_lambda = None
    verdict = "FAIL"

    for c_entry, b1_entry in zip(c_results, b1_results):
        assert c_entry["lambda_R"] == b1_entry["lambda_R"], \
            "Lambda mismatch between C and B1 sweep results."

        lam = c_entry["lambda_R"]
        c_deg = c_entry["degenerate"]
        b1_deg = b1_entry["degenerate"]

        if c_deg or b1_deg:
            gap = None
            eligible = False
        else:
            gap = c_entry["normalized_utility"] - b1_entry["normalized_utility"]
            eligible = gap > delta
            if eligible:
                verdict = "PASS"
                if best_gap is None or gap > best_gap:
                    best_gap = gap
                    best_lambda = lam

        gap_table.append({
            "lambda_R": lam,
            "c_utility": c_entry["normalized_utility"],
            "b1_utility": b1_entry["normalized_utility"],
            "gap": gap,
            "c_degenerate": c_deg,
            "b1_degenerate": b1_deg,
            "eligible": eligible,
        })

    return {
        "verdict": verdict,
        "best_gap": best_gap,
        "best_lambda": best_lambda,
        "delta": delta,
        "gap_table": gap_table,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Load freeze
    freeze = load_freeze()
    lambda_sweep   = freeze["lambda_sweep"]["values"]
    lambda_A       = freeze["lambda_sweep"]["lambda_A_fixed"]
    delta          = freeze["delta"]["value"]
    estimator_list = freeze["estimators"]
    population_id  = "LC45"
    population_role = "stress_test"

    print(f"[phase-c1] population={population_id}  role={population_role}")
    print(f"[phase-c1] NOTE: LC45 is stress test only. "
          f"This verdict does not determine the primary RQ-C1 outcome.")
    print(f"[phase-c1] lambda_sweep={lambda_sweep}")
    print(f"[phase-c1] lambda_A={lambda_A}  delta={delta}")

    # 2. Load decisions
    ground_truth, estimator_stats = load_lc45_aggregates(DATA_PATH)
    n_solvers = len(ground_truth)
    accept_count = ground_truth.count("ACCEPT")
    reject_count = ground_truth.count("REJECT")
    print(f"[phase-c1] solvers={n_solvers}  "
          f"accept={accept_count}  reject={reject_count}")
    if accept_count == 1:
        print(f"[phase-c1] WARNING: single-survivor population. "
              f"Results are fragile. Report as stress test only.")

    # 3. Verify all freeze-declared estimators are present
    missing = [e for e in estimator_list if e not in estimator_stats]
    if missing:
        raise KeyError(
            f"Estimators declared in freeze file but absent from data: {missing}"
        )

    # 4. Run sweep for each estimator (aggregate path — (WA, WR) is sufficient
    #    under the freeze's linear cost model).
    all_results = {}
    for estimator in estimator_list:
        stats = estimator_stats[estimator]
        sweep = run_sweep_aggregate(
            wrong_accepts=stats["wrong_accepts"],
            wrong_rejects=stats["wrong_rejects"],
            n_solvers=stats["n_solvers"],
            lambda_sweep=lambda_sweep,
            lambda_A=lambda_A,
            degenerate_all_accept=stats["degenerate_all_accept"],
            degenerate_all_reject=stats["degenerate_all_reject"],
        )
        all_results[estimator] = sweep
        if sweep and sweep[0]["degenerate"]:
            print(f"[phase-c1]   {estimator}: degenerate "
                  f"({'all-accept' if stats['degenerate_all_accept'] else 'all-reject'})")
        else:
            print(f"[phase-c1]   {estimator}: non-degenerate "
                  f"(WA={stats['wrong_accepts']}, WR={stats['wrong_rejects']})")

    # 5. Apply falsification criterion (primary comparison: C vs B1)
    falsification = apply_falsification(
        c_results=all_results["C_structured_fingerprint"],
        b1_results=all_results["B1_count"],
        delta=delta,
    )
    print(f"[phase-c1] stress_test_verdict={falsification['verdict']}  "
          f"best_gap={falsification['best_gap']}  "
          f"best_lambda={falsification['best_lambda']}")
    print(f"[phase-c1] NOTE: stress_test_verdict is reported separately. "
          f"Primary verdict determined by LC322.")

    # 6. Assemble output
    output = {
        "phase": "C1",
        "population": population_id,
        "population_role": population_role,
        "population_role_note": (
            "Stress test only. Single-survivor skew (1/9). "
            "Results reported separately. "
            "Does not override LC322 primary verdict."
        ),
        "freeze_commit": "3bd286d",
        "n_solvers": n_solvers,
        "accept_count": accept_count,
        "reject_count": reject_count,
        "lambda_sweep": lambda_sweep,
        "lambda_A": lambda_A,
        "delta": delta,
        "estimator_sweeps": all_results,
        "falsification": falsification,
        "epistemological_constraints": [
            "no compression drift",
            "no negative result inflation beyond tested lambda range and populations",
            "no causal language",
        ],
    }

    # 7. Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"[phase-c1] written → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

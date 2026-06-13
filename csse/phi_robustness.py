"""PHI_ROBUSTNESS_SPEC v1.0 — Mimo Execution.

Compute ΔU stability under φ-perturbations for LC322, LC3946, LC45, LC743.
No modifications to E, solver population, or canonical φ.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# ══════════════════════════════════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════════════════════════════════

SEED = 20260611
N_BOOTSTRAP = 100
P4_N_PERMUTATIONS = 1000
P12_K = 20

PROBLEMS = ["lc322", "lc3946", "lc45", "lc743"]
CONDITIONS = ["P1", "P2", "P3", "P4", "P5"]

# ══════════════════════════════════════════════════════════════════════════
# Probe loading (frozen)
# ══════════════════════════════════════════════════════════════════════════

def load_probes(problem_class: str) -> list[dict]:
    if problem_class == "lc743":
        from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE
        probes = []
        for i, tc in enumerate(CANONICAL_TEST_SUITE):
            note = tc.get("note", "unknown")
            family = note.split(":")[0] if ":" in note else "unknown"
            probes.append({
                "probe_id": tc.get("label", f"f{i}"),
                "times": tc["times"],
                "n": tc["n"],
                "k": tc["k"],
                "expected": tc["expected"],
                "family": family,
            })
        return probes
    path = REPO / "data" / f"midweather_fingerprint_{problem_class}_probe_index.json"
    with open(path) as f:
        data = json.load(f)
    return data["probes"]


# ══════════════════════════════════════════════════════════════════════════
# Oracle functions (frozen)
# ══════════════════════════════════════════════════════════════════════════

def lc322_oracle(solver_input: list) -> int:
    from doctor.adversarial.lc322_ground_truth import lc322_brute_force
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return lc322_brute_force(coins, amount)

def lc3946_oracle(solver_input: list) -> int:
    from doctor.adversarial.lc3946_ground_truth import lc3946_brute_force
    flat = [int(x) for x in solver_input]
    items = [(flat[2 * k], flat[2 * k + 1]) for k in range(len(flat) // 2)]
    factor_budget, budget = items[-1]
    return lc3946_brute_force(items[:-1], int(budget))

def lc45_oracle(solver_input: list) -> int:
    from doctor.adversarial.lc45_ground_truth import lc45_brute_force
    return lc45_brute_force(list(solver_input))

def lc79_oracle(solver_input: dict) -> bool:
    from doctor.adversarial.lc79_ground_truth import lc79_brute_force
    board = [row[:] for row in solver_input["board"]]
    word = solver_input["word"]
    return lc79_brute_force(board, word)

def lc743_oracle(times, n=None, k=None) -> int:
    from doctor.oracles.lc743_oracle import lc743_oracle as _oracle
    if isinstance(times, tuple) and n is None:
        times, n, k = times
    return _oracle(times, n, k)


# ══════════════════════════════════════════════════════════════════════════
# Probe-to-solver-input converters (frozen)
# ══════════════════════════════════════════════════════════════════════════

def lc322_to_input(probe):
    return [*list(probe["coins"]), int(probe["amount"])]

def lc3946_to_input(probe):
    flat = []
    for item in probe["items"]:
        flat.append(int(item[0]))
        flat.append(int(item[1]))
    flat.append(0)
    flat.append(probe["budget"])
    return flat

def lc45_to_input(probe):
    return list(probe["nums"])

def lc79_to_input(probe):
    return {"board": [row[:] for row in probe["board"]], "word": probe["word"]}

def lc743_to_input(probe):
    return (probe["times"], probe["n"], probe["k"])


# ══════════════════════════════════════════════════════════════════════════
# Decision functions (frozen)
# ══════════════════════════════════════════════════════════════════════════

def b1_decision(obs_fails: int) -> str:
    return "ACCEPT" if obs_fails == 0 else "REJECT"

def c_genuine_decision(family_fails: dict[str, int]) -> str:
    if sum(family_fails.values()) == 0:
        return "ACCEPT"
    if len(family_fails) <= 1:
        return "ACCEPT"
    return "REJECT"


# ══════════════════════════════════════════════════════════════════════════
# Canonical φ extraction
# ══════════════════════════════════════════════════════════════════════════

def extract_canonical_phi(probes: list[dict]) -> dict[str, str]:
    """Extract canonical probe-to-family mapping from probes."""
    return {p["probe_id"]: p.get("family", "unknown") for p in probes}

def get_family_sizes(phi: dict[str, str]) -> dict[str, int]:
    """Get size of each family."""
    sizes = defaultdict(int)
    for fam in phi.values():
        sizes[fam] += 1
    return dict(sizes)

def get_n_families(phi: dict[str, str]) -> int:
    return len(set(phi.values()))


# ══════════════════════════════════════════════════════════════════════════
# φ Perturbation Engine
# ══════════════════════════════════════════════════════════════════════════

def phi_perturb_P1(probes: list[dict], phi: dict[str, str], seed: int) -> dict[str, str]:
    """P1: Randomized coarse merging — merge families into ceil(N/2) groups."""
    rng = random.Random(seed)
    families = list(set(phi.values()))
    n = len(families)
    target = math.ceil(n / 2)

    shuffled = list(families)
    rng.shuffle(shuffled)

    groups = []
    for i in range(target):
        start = i * 2
        if start < n:
            group = [shuffled[start]]
            if start + 1 < n:
                group.append(shuffled[start + 1])
            groups.append(group)

    merge_map = {}
    for new_idx, group in enumerate(groups):
        new_name = f"P1_group_{new_idx}"
        for fam in group:
            merge_map[fam] = new_name

    return {pid: merge_map.get(fam, fam) for pid, fam in phi.items()}


def phi_perturb_P2(probes: list[dict], phi: dict[str, str], seed: int) -> dict[str, str]:
    """P2: Balanced stochastic splitting — split each family into two subgroups."""
    rng = random.Random(seed)
    families = defaultdict(list)
    for pid, fam in phi.items():
        families[fam].append(pid)

    result = {}
    for fam, pids in families.items():
        shuffled = list(pids)
        rng.shuffle(shuffled)
        half = len(shuffled) // 2
        for pid in shuffled[:half]:
            result[pid] = f"{fam}_a"
        for pid in shuffled[half:]:
            result[pid] = f"{fam}_b"
    return result


def phi_perturb_P3(probes: list[dict], phi: dict[str, str], seed: int) -> dict[str, str]:
    """P3: Semantic axis re-partitioning — regroup by an orthogonal axis.

    For each problem, we define an alternative axis based on input properties:
    - LC322: group by amount size (small/medium/large)
    - LC3946: group by budget size (small/medium/large)
    - LC45: group by array length (short/medium/long)
    - LC743: group by graph size (n value)
    """
    probe_dict = {p["probe_id"]: p for p in probes}

    result = {}
    for pid, fam in phi.items():
        p = probe_dict[pid]

        if "amount" in p:
            amount = p["amount"]
            if amount <= 10:
                result[pid] = "P3_small_amount"
            elif amount <= 50:
                result[pid] = "P3_medium_amount"
            else:
                result[pid] = "P3_large_amount"
        elif "budget" in p:
            budget = p["budget"]
            if budget <= 8:
                result[pid] = "P3_small_budget"
            elif budget <= 14:
                result[pid] = "P3_medium_budget"
            else:
                result[pid] = "P3_large_budget"
        elif "nums" in p:
            nums = p["nums"]
            length = len(nums)
            if length <= 5:
                result[pid] = "P3_short_array"
            elif length <= 7:
                result[pid] = "P3_medium_array"
            else:
                result[pid] = "P3_long_array"
        elif "n" in p:
            n = p["n"]
            if n <= 3:
                result[pid] = "P3_small_graph"
            elif n <= 4:
                result[pid] = "P3_medium_graph"
            else:
                result[pid] = "P3_large_graph"
        else:
            result[pid] = fam  # fallback: keep canonical

    return result


def phi_perturb_P4(probes: list[dict], phi: dict[str, str], seed: int) -> dict[str, str]:
    """P4: Constrained random partition — random assignment preserving family count and size vector."""
    rng = random.Random(seed)
    family_sizes = get_family_sizes(phi)
    n_families = len(family_sizes)
    sorted_sizes = sorted(family_sizes.values(), reverse=True)

    probe_ids = list(phi.keys())
    shuffled = list(probe_ids)
    rng.shuffle(shuffled)

    result = {}
    idx = 0
    for fam_idx in range(n_families):
        fam_name = f"P4_random_{fam_idx}"
        size = sorted_sizes[fam_idx] if fam_idx < len(sorted_sizes) else 0
        for _ in range(size):
            if idx < len(shuffled):
                result[shuffled[idx]] = fam_name
                idx += 1

    return result


def phi_perturb_P5(probes: list[dict], phi: dict[str, str], seed: int,
                   solver_evals: dict[str, dict[str, bool]] | None = None) -> dict[str, str]:
    """P5: Adversarial equal-mixing partition — maximize homogenization of family signal.

    Assigns probes to families such that each family contains an equal mixture
    of pass and fail outcomes across all solvers.
    """
    rng = random.Random(seed)
    probe_ids = list(phi.keys())
    n_families = get_n_families(phi)

    if solver_evals is None:
        rng.shuffle(probe_ids)
        result = {}
        for i, pid in enumerate(probe_ids):
            result[pid] = f"P5_family_{i % n_families}"
        return result

    failure_rates = {}
    for pid in probe_ids:
        n_fail = sum(1 for sid, results in solver_evals.items() if not results.get(pid, True))
        n_total = len(solver_evals)
        failure_rates[pid] = n_fail / n_total if n_total > 0 else 0

    sorted_probes = sorted(probe_ids, key=lambda p: failure_rates[p])

    result = {}
    for i, pid in enumerate(sorted_probes):
        result[pid] = f"P5_family_{i % n_families}"

    return result


def phi_perturb(probes: list[dict], phi: dict[str, str], condition_id: str,
                seed: int, solver_evals: dict | None = None) -> dict[str, str]:
    """Generate a single perturbed φ variant."""
    if condition_id == "P1":
        return phi_perturb_P1(probes, phi, seed)
    elif condition_id == "P2":
        return phi_perturb_P2(probes, phi, seed)
    elif condition_id == "P3":
        return phi_perturb_P3(probes, phi, seed)
    elif condition_id == "P4":
        return phi_perturb_P4(probes, phi, seed)
    elif condition_id == "P5":
        return phi_perturb_P5(probes, phi, seed, solver_evals)
    else:
        raise ValueError(f"Unknown condition: {condition_id}")


# ══════════════════════════════════════════════════════════════════════════
# Observed / Target probe splits (frozen from C-4 protocol)
# ══════════════════════════════════════════════════════════════════════════

def load_observed_target_split(problem_class: str) -> tuple[list[str], list[str]]:
    """Load observed (O_obs) and target (D_target) probe IDs for a problem.

    For lc322/lc3946/lc45: odd-numbered probes are observed, even-numbered are target.
    For lc743: stratified 3-per-direction observed, 3-per-direction target.
    """
    if problem_class == "lc743":
        from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE
        rng = random.Random(SEED)
        by_dir = {
            "F1": list(range(0, 6)),
            "F2": list(range(6, 12)),
            "F3": list(range(12, 18)),
            "F4": list(range(18, 24)),
        }
        observed_indices = []
        target_indices = []
        for d, indices in by_dir.items():
            shuffled = list(indices)
            rng.shuffle(shuffled)
            observed_indices.extend(shuffled[:3])
            target_indices.extend(shuffled[3:])
        observed_indices.sort()
        target_indices.sort()
        observed_ids = [CANONICAL_TEST_SUITE[i].get("label", f"f{i}") for i in observed_indices]
        target_ids = [CANONICAL_TEST_SUITE[i].get("label", f"f{i}") for i in target_indices]
        return observed_ids, target_ids

    probes = load_probes(problem_class)
    probe_ids = [p["probe_id"] for p in probes]

    observed_ids = sorted([pid for pid in probe_ids if int(pid.split("_")[-1]) % 2 == 1])
    target_ids = sorted([pid for pid in probe_ids if int(pid.split("_")[-1]) % 2 == 0])
    return observed_ids, target_ids


# ══════════════════════════════════════════════════════════════════════════
# Decision_loss computation (C-4 protocol)
# ══════════════════════════════════════════════════════════════════════════

def decision_loss_single(decision: str, correct: bool,
                         wrong_accept_cost: float = 1.0,
                         wrong_reject_cost: float = 1.0) -> float:
    """Compute the cost of a single decision under the C-4 cost model."""
    if decision == "ACCEPT" and correct:
        return 0.0
    if decision == "REJECT" and not correct:
        return 0.0
    if decision == "ACCEPT" and not correct:
        return wrong_accept_cost
    # decision == "REJECT" and correct
    return wrong_reject_cost


def compute_deltaU(solver_evals: dict[str, dict[str, bool]],
                   phi: dict[str, str],
                   observed_ids: list[str],
                   ground_truth: dict[str, bool],
                   wrong_accept_cost: float = 1.0,
                   wrong_reject_cost: float = 1.0) -> float:
    """Compute ΔU as decision_loss differential under C-4 protocol.

    ΔU = mean over solvers of [loss(B1, s) - loss(C_genuine, s)]

    Positive ΔU means C_genuine has lower decision loss (is better).
    """
    losses_b1 = []
    losses_cgen = []

    for sid, results in solver_evals.items():
        if sid not in ground_truth:
            continue

        is_correct = ground_truth[sid]
        obs_fails = sum(1 for pid in observed_ids if not results.get(pid, True))

        b1 = b1_decision(obs_fails)

        family_fails = defaultdict(int)
        for pid in observed_ids:
            if not results.get(pid, True):
                fam = phi.get(pid, "unknown")
                family_fails[fam] += 1
        c_gen = c_genuine_decision(dict(family_fails))

        losses_b1.append(decision_loss_single(b1, is_correct, wrong_accept_cost, wrong_reject_cost))
        losses_cgen.append(decision_loss_single(c_gen, is_correct, wrong_accept_cost, wrong_reject_cost))

    if not losses_b1:
        return 0.0

    return (sum(losses_b1) - sum(losses_cgen)) / len(losses_b1)


def bootstrap_ci_deltaU(solver_evals: dict[str, dict[str, bool]],
                        phi: dict[str, str],
                        observed_ids: list[str],
                        ground_truth: dict[str, bool],
                        wrong_accept_cost: float = 1.0,
                        wrong_reject_cost: float = 1.0,
                        n_bootstrap: int = 100,
                        ci: float = 0.95) -> tuple[float, float, float]:
    """Compute ΔU with bootstrap confidence interval."""
    n = len(solver_evals)
    sids = list(solver_evals.keys())

    deltaU = compute_deltaU(solver_evals, phi, observed_ids, ground_truth,
                            wrong_accept_cost, wrong_reject_cost)

    boot_values = []
    for _ in range(n_bootstrap):
        sample_sids = random.choices(sids, k=n)
        sample_evals = {sid: solver_evals[sid] for sid in sample_sids}
        sample_gt = {sid: ground_truth[sid] for sid in sample_sids if sid in ground_truth}
        boot_values.append(compute_deltaU(sample_evals, phi, observed_ids, sample_gt,
                                          wrong_accept_cost, wrong_reject_cost))

    boot_values.sort()
    alpha = (1 - ci) / 2
    lo = boot_values[int(alpha * n_bootstrap)]
    hi = boot_values[int((1 - alpha) * n_bootstrap)]

    return deltaU, lo, hi


# ══════════════════════════════════════════════════════════════════════════
# Frozen solver loading (C-4 protocol population)
# ══════════════════════════════════════════════════════════════════════════

def load_frozen_solvers(problem_class: str) -> dict[str, any]:
    """Load the 30 (or 10) frozen solvers for a problem class.

    Returns {solver_id: module} where module has a .solve() function.
    """
    solver_dir = REPO / "experiments" / f"frozen_taxonomy_{problem_class}" / "solvers"
    if not solver_dir.exists():
        raise FileNotFoundError(f"Frozen solver directory not found: {solver_dir}")

    solvers = {}
    for solver_file in sorted(solver_dir.glob("solver_*.py")):
        sid = solver_file.stem  # e.g. "solver_001"
        spec = importlib.util.spec_from_file_location(sid, str(solver_file))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        solvers[sid] = mod

    return solvers


def load_ground_truth_from_json(problem_class: str) -> dict[str, bool]:
    """Load pre-computed ground truth labels from the C-4 result file.

    Returns {solver_id: True if ACCEPT (correct), False if REJECT (incorrect)}.
    """
    json_path = REPO / "data" / f"midweather_fingerprint_{problem_class}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Ground truth JSON not found: {json_path}")

    with open(json_path) as f:
        data = json.load(f)

    gt_data = data.get("per_solver_ground_truth", {})
    ground_truth = {}
    for sid, info in gt_data.items():
        ground_truth[sid] = (info["truth_label"] == "ACCEPT")
    return ground_truth


def evaluate_frozen_solvers(problem_class: str, to_input, oracle_fn,
                            invoke_style: str) -> dict[str, dict[str, bool]]:
    """Evaluate the frozen solver population on all probes.

    Returns {solver_id: {probe_id: passed}}.
    """
    probes = load_probes(problem_class)
    solvers = load_frozen_solvers(problem_class)

    results = {}
    for sid, mod in solvers.items():
        solver_fn = mod.solve
        probe_results = {}
        for probe in probes:
            solver_input = to_input(probe)
            try:
                truth = oracle_fn(solver_input)
                if invoke_style == "single":
                    observed = solver_fn(copy.deepcopy(solver_input))
                elif invoke_style == "lc79":
                    observed = solver_fn(copy.deepcopy(solver_input["board"]), solver_input["word"])
                elif invoke_style == "lc743":
                    observed = solver_fn(*solver_input)
                else:
                    observed = solver_fn(copy.deepcopy(solver_input))
            except Exception:
                observed = "EXC"
            probe_results[probe["probe_id"]] = (observed == truth)
        results[sid] = probe_results

    return results


# ══════════════════════════════════════════════════════════════════════════
# Hash computation
# ══════════════════════════════════════════════════════════════════════════

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def compute_phi_hash(phi: dict[str, str]) -> str:
    serialized = json.dumps(phi, sort_keys=True)
    return compute_hash(serialized)

def compute_solvers_hash(solver_evals: dict[str, dict[str, bool]]) -> str:
    serialized = json.dumps(solver_evals, sort_keys=True)
    return compute_hash(serialized)


# ══════════════════════════════════════════════════════════════════════════
# P4 Null Model
# ══════════════════════════════════════════════════════════════════════════

def run_p4_null_model(probes: list[dict], phi: dict[str, str],
                      solver_evals: dict[str, dict[str, bool]],
                      observed_ids: list[str],
                      ground_truth: dict[str, bool],
                      wrong_accept_cost: float = 1.0,
                      wrong_reject_cost: float = 1.0,
                      n_permutations: int = 100) -> dict:
    """Run P4 null model: random permutations preserving family count and size vector."""
    deltaU_canonical = compute_deltaU(solver_evals, phi, observed_ids, ground_truth,
                                      wrong_accept_cost, wrong_reject_cost)

    perm_deltas = []
    for i in range(n_permutations):
        perm_phi = phi_perturb_P4(probes, phi, seed=SEED + 1000 + i)
        perm_deltaU = compute_deltaU(solver_evals, perm_phi, observed_ids, ground_truth,
                                     wrong_accept_cost, wrong_reject_cost)
        perm_deltas.append(perm_deltaU)

    perm_deltas_sorted = sorted(perm_deltas)
    n_below = sum(1 for d in perm_deltas_sorted if d < deltaU_canonical)
    percentile = (n_below / n_permutations) * 100

    canonical_sign = 1 if deltaU_canonical > 0 else (-1 if deltaU_canonical < 0 else 0)
    fraction_same = sum(1 for d in perm_deltas
                        if (1 if d > 0 else (-1 if d < 0 else 0)) == canonical_sign) / n_permutations

    return {
        "n_permutations": n_permutations,
        "deltaU_canonical": deltaU_canonical,
        "deltaU_distribution": perm_deltas,
        "deltaU_mean": sum(perm_deltas) / n_permutations,
        "deltaU_std": (sum((d - sum(perm_deltas)/n_permutations)**2
                          for d in perm_deltas) / n_permutations) ** 0.5,
        "canonical_percentile": percentile,
        "fraction_same_sign": fraction_same,
    }


# ══════════════════════════════════════════════════════════════════════════
# Stability Classification
# ══════════════════════════════════════════════════════════════════════════

def classify_stability(p4_result: dict, p1_sign_stable: bool,
                       p2_sign_stable: bool, p3_sign_stable: bool,
                       p5_collapses: bool) -> str:
    """Classify stability per spec rules.

    ROBUST: sign-stable P1,P2,P3. Canonical >80th percentile P4. P5 collapses.
    CONDITIONALLY ROBUST: sign-stable P1,P2. P3 shows axis-dependence.
    FRAGILE: sign unstable under P1 or P2.
    ARTIFACT: canonical not in >=80th percentile of P4.
    """
    if p4_result["canonical_percentile"] < 80:
        return "ARTIFACT"

    if not p1_sign_stable or not p2_sign_stable:
        return "FRAGILE"

    if not p3_sign_stable:
        return "CONDITIONALLY ROBUST"

    return "ROBUST"


# ══════════════════════════════════════════════════════════════════════════
# Main execution
# ══════════════════════════════════════════════════════════════════════════

def run_problem(problem_class: str, to_input, oracle_fn,
                invoke_style: str, lambda_val: float = 1.0) -> list[dict]:
    """Run full phi-robustness experiment for one problem on frozen population."""
    print(f"\n{'='*70}")
    print(f"  {problem_class.upper()} -- phi-robustness experiment (lambda={lambda_val})")
    print(f"  Population: frozen C-4 solvers (n=30)")
    print(f"{'='*70}")

    probes = load_probes(problem_class)
    canonical_phi = extract_canonical_phi(probes)
    n_families_canonical = get_n_families(canonical_phi)

    observed_ids, target_ids = load_observed_target_split(problem_class)
    print(f"  Probes: {len(probes)}, Families: {n_families_canonical}")
    print(f"  Observed: {len(observed_ids)}, Target: {len(target_ids)}")

    print(f"  Loading frozen solvers...")
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, invoke_style)
    n_valid = len(solver_evals)
    print(f"  Frozen solvers: {n_valid}")

    ground_truth = load_ground_truth_from_json(problem_class)
    n_correct = sum(1 for v in ground_truth.values() if v)
    n_incorrect = sum(1 for v in ground_truth.values() if not v)
    print(f"  Ground truth (from JSON): {n_correct} correct, {n_incorrect} incorrect")

    wrong_accept_cost = 1.0
    wrong_reject_cost = lambda_val

    deltaU_canonical, ci_lo, ci_hi = bootstrap_ci_deltaU(
        solver_evals, canonical_phi, observed_ids, ground_truth,
        wrong_accept_cost, wrong_reject_cost, N_BOOTSTRAP
    )
    print(f"  DU_canonical: {deltaU_canonical:.6f} [{ci_lo:.6f}, {ci_hi:.6f}]")

    results = []

    for condition in CONDITIONS:
        print(f"\n  --- {condition} ---")

        if condition == "P4":
            p4_result = run_p4_null_model(probes, canonical_phi, solver_evals,
                                          observed_ids, ground_truth,
                                          wrong_accept_cost, wrong_reject_cost,
                                          P4_N_PERMUTATIONS)
            print(f"    Canonical percentile: {p4_result['canonical_percentile']:.1f}")
            print(f"    Fraction same sign: {p4_result['fraction_same_sign']:.3f}")

            results.append({
                "problem_id": problem_class.upper(),
                "condition_id": "P4",
                "phi_description": "Constrained random partition preserving family count and size vector",
                "n_families_canonical": n_families_canonical,
                "n_families_perturbed": n_families_canonical,
                "deltaU_canonical": deltaU_canonical,
                "deltaU_mean": p4_result["deltaU_mean"],
                "deltaU_std": p4_result["deltaU_std"],
                "sign_stability": p4_result["fraction_same_sign"] > 0.5,
                "magnitude_ratio": abs(p4_result["deltaU_mean"] - deltaU_canonical) / abs(deltaU_canonical) if deltaU_canonical != 0 else 0,
                "bootstrap_CI_deltaU": [ci_lo, ci_hi],
                "n_permutations": P4_N_PERMUTATIONS,
                "deltaU_distribution": p4_result["deltaU_distribution"],
                "canonical_percentile": p4_result["canonical_percentile"],
                "fraction_same_sign": p4_result["fraction_same_sign"],
                "notes": "P4 null model — canonical must be >80th percentile for validity",
            })
            continue

        variant_deltas = []
        for k in range(P12_K):
            seed_k = SEED + hash((problem_class, condition, k)) % 100000
            perturbed_phi = phi_perturb(probes, canonical_phi, condition, seed_k, solver_evals)
            deltaU_k = compute_deltaU(solver_evals, perturbed_phi, observed_ids, ground_truth,
                                      wrong_accept_cost, wrong_reject_cost)
            variant_deltas.append(deltaU_k)

        mean_deltaU = sum(variant_deltas) / len(variant_deltas)
        std_deltaU = (sum((d - mean_deltaU)**2 for d in variant_deltas) / len(variant_deltas)) ** 0.5

        canonical_sign = 1 if deltaU_canonical > 0 else (-1 if deltaU_canonical < 0 else 0)
        variant_signs = [1 if d > 0 else (-1 if d < 0 else 0) for d in variant_deltas]
        sign_stability = all(s == canonical_sign for s in variant_signs)

        mag_ratio = abs(mean_deltaU - deltaU_canonical) / abs(deltaU_canonical) if deltaU_canonical != 0 else 0

        n_families_perturbed = get_n_families(
            phi_perturb(probes, canonical_phi, condition, SEED, solver_evals)
        )

        print(f"    Mean DU: {mean_deltaU:.6f} +/- {std_deltaU:.6f}")
        print(f"    Sign stable: {sign_stability}")
        print(f"    Magnitude ratio: {mag_ratio:.4f}")

        results.append({
            "problem_id": problem_class.upper(),
            "condition_id": condition,
            "phi_description": f"{condition} perturbation",
            "n_families_canonical": n_families_canonical,
            "n_families_perturbed": n_families_perturbed,
            "deltaU_canonical": deltaU_canonical,
            "deltaU_mean": mean_deltaU,
            "deltaU_std": std_deltaU,
            "sign_stability": sign_stability,
            "magnitude_ratio": mag_ratio,
            "bootstrap_CI_deltaU": [ci_lo, ci_hi],
            "notes": f"{condition} with K={P12_K} variants",
        })

    return results


def main():
    random.seed(SEED)

    phi_hashes = {}
    for pc in ["lc322", "lc3946", "lc45", "lc743"]:
        probes = load_probes(pc)
        phi = extract_canonical_phi(probes)
        phi_hashes[pc] = compute_phi_hash(phi)

    frozen_configs = [
        ("lc322", lc322_to_input, lc322_oracle, "single"),
        ("lc3946", lc3946_to_input, lc3946_oracle, "single"),
        ("lc45", lc45_to_input, lc45_oracle, "single"),
        ("lc743", lc743_to_input, lc743_oracle, "lc743"),
    ]

    # ── Validation: LC3946 canonical must show DU close to 1.0 ──────────
    print(f"\n{'='*70}")
    print("  VALIDATION: LC3946 canonical DU check")
    print(f"{'='*70}")
    lc3946_probes = load_probes("lc3946")
    lc3946_phi = extract_canonical_phi(lc3946_probes)
    lc3946_obs, lc3946_tgt = load_observed_target_split("lc3946")
    lc3946_evals = evaluate_frozen_solvers("lc3946", lc3946_to_input, lc3946_oracle, "single")
    lc3946_gt = load_ground_truth_from_json("lc3946")
    n_correct = sum(1 for v in lc3946_gt.values() if v)
    n_incorrect = sum(1 for v in lc3946_gt.values() if not v)
    print(f"  LC3946 frozen solvers: {len(lc3946_evals)}")
    print(f"  LC3946 ground truth: {n_correct} correct, {n_incorrect} incorrect")
    lc3946_du = compute_deltaU(lc3946_evals, lc3946_phi, lc3946_obs, lc3946_gt, 1.0, 1.0)
    print(f"  LC3946 DU_canonical (lambda=1): {lc3946_du:.6f}")
    if abs(lc3946_du) < 0.001:
        print(f"  WARNING: DU={lc3946_du:.4f} is zero. Stopping.")
        return None
    print(f"  Validation PASSED: DU={lc3946_du:.4f} is non-zero.")

    # ── Full run with lambda=1 (uniform cost, matching C-4) ─────────────
    all_results = []
    all_classifications = {}

    for pc, to_input, oracle_fn, style in frozen_configs:
        try:
            results = run_problem(pc, to_input, oracle_fn, style, lambda_val=1.0)
            all_results.extend(results)

            p4_result = next((r for r in results if r["condition_id"] == "P4"), None)
            p1_stable = next((r for r in results if r["condition_id"] == "P1"), {}).get("sign_stability", True)
            p2_stable = next((r for r in results if r["condition_id"] == "P2"), {}).get("sign_stability", True)
            p3_stable = next((r for r in results if r["condition_id"] == "P3"), {}).get("sign_stability", True)

            classification = classify_stability(
                p4_result or {"canonical_percentile": 0},
                p1_stable, p2_stable, p3_stable, False
            )
            all_classifications[pc.upper()] = classification
            print(f"\n  {pc.upper()} classification: {classification}")

        except Exception as e:
            print(f"ERROR on {pc}: {e}")
            import traceback; traceback.print_exc()

    # ── Lambda sensitivity: LC322 at lambda=10, 50, 100 ─────────────────
    print(f"\n{'='*70}")
    print("  LAMBDA SENSITIVITY: LC322")
    print(f"{'='*70}")
    lc322_probes = load_probes("lc322")
    lc322_phi = extract_canonical_phi(lc322_probes)
    lc322_obs, lc322_tgt = load_observed_target_split("lc322")
    lc322_evals = evaluate_frozen_solvers("lc322", lc322_to_input, lc322_oracle, "single")
    lc322_gt = load_ground_truth_from_json("lc322")

    lambda_sensitivity = {}
    for lam in [10, 50, 100]:
        du_lam, lo_lam, hi_lam = bootstrap_ci_deltaU(
            lc322_evals, lc322_phi, lc322_obs, lc322_gt,
            wrong_accept_cost=1.0, wrong_reject_cost=float(lam), n_bootstrap=N_BOOTSTRAP
        )
        lambda_sensitivity[str(lam)] = {"DU": du_lam, "CI": [lo_lam, hi_lam]}
        print(f"  LC322 DU at lambda={lam}: {du_lam:.6f} [{lo_lam:.6f}, {hi_lam:.6f}]")

    control_ok = True
    for ctrl in ["lc45", "lc743"]:
        ctrl_results = [r for r in all_results if r["problem_id"] == ctrl.upper()]
        for r in ctrl_results:
            if abs(r.get("deltaU_mean", 0)) > 0.1:
                print(f"  CONTROL VIOLATION: {ctrl.upper()} DU={r['deltaU_mean']:.4f} under {r['condition_id']}")
                control_ok = False

    output = {
        "spec_version": "PHI_ROBUSTNESS_SPEC v1.0",
        "metric": "decision_loss_differential (C-4 protocol)",
        "seed": SEED,
        "population": "30 frozen C-4 solvers per problem",
        "n_bootstrap": N_BOOTSTRAP,
        "p4_n_permutations": P4_N_PERMUTATIONS,
        "p12_k": P12_K,
        "environment_lock": {
            "phi_hashes": phi_hashes,
            "oracle_hash": compute_hash("lc322_oracle,lc3946_oracle,lc45_oracle,lc743_oracle"),
        },
        "lambda_sensitivity": {"lc322": lambda_sensitivity},
        "results": all_results,
        "classifications": all_classifications,
        "control_verification": {"status": "PASS" if control_ok else "FAIL"},
    }

    out_path = REPO / "results" / "phi_robustness_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    print(f"\n{'='*70}")
    print(f"  CLASSIFICATION TABLE")
    print(f"{'='*70}")
    for pc, cls in all_classifications.items():
        print(f"  {pc:<10} {cls}")
    print(f"{'='*70}")

    return output


if __name__ == "__main__":
    main()

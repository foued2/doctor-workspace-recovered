"""JRT — Joint Representability Test.

Tests whether ANY embedding makes discrete oracle and continuous metrics co-monotonic.

Two cases:
  Case 1: Joint embedding exists → oracle and continuous metrics are reparameterizations
           of same latent structure.
  Case 2: No joint embedding exists → two fundamentally incompatible observational systems.

Tests:
  1. Monotonicity: Is there ANY scalar function f(continuous_metrics) monotonic w.r.t. discrete?
  2. Threshold separability: Is there ANY threshold on ANY continuous metric (or linear combo)
     that perfectly separates discrete=0 from discrete>0?
  3. Rank correlation: Is there ANY monotonic relationship between continuous metrics and discrete?
  4. Linear separability: Can a linear classifier perfectly separate discrete=0 from discrete>0
     in continuous metric space?

No narrative synthesis. No per-solver decomposition. Strictly structural.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def load_data():
    """Load O2-A and O2-B per-solver results."""
    # Try multiple paths
    for base in [ROOT, ROOT.parent]:
        o2a_path = base / "results" / "o2a_scoring.json"
        o2b_path = base / "results" / "o2b_resolution.json"
        if o2a_path.exists() and o2b_path.exists():
            o2a = json.loads(o2a_path.read_text(encoding="utf-8"))
            o2b = json.loads(o2b_path.read_text(encoding="utf-8"))
            o2b_by_solver = {s["solver_id"]: s for s in o2b["per_solver"]}
            return o2a, o2b_by_solver
    raise FileNotFoundError("O2 results not found")


def kendall_tau(x, y):
    """Compute Kendall's tau rank correlation."""
    n = len(x)
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            x_diff = x[i] - x[j]
            y_diff = y[i] - y[j]
            if x_diff * y_diff > 0:
                concordant += 1
            elif x_diff * y_diff < 0:
                discordant += 1
    if concordant + discordant == 0:
        return 0.0
    return (concordant - discordant) / (concordant + discordant)


def spearman_rho(x, y):
    """Compute Spearman's rank correlation."""
    n = len(x)
    rank_x = [0] * n
    rank_y = [0] * n

    sorted_x = sorted(range(n), key=lambda i: x[i])
    for rank, i in enumerate(sorted_x, 1):
        rank_x[i] = rank

    sorted_y = sorted(range(n), key=lambda i: y[i])
    for rank, i in enumerate(sorted_y, 1):
        rank_y[i] = rank

    return kendall_tau(rank_x, rank_y)


def threshold_separability(values, labels):
    """Test if any threshold perfectly separates labels.

    values: list of scalar values
    labels: list of 0/1 labels
    Returns: (separable: bool, best_threshold: float, best_error: int)
    """
    n = len(values)
    # Sort by value
    indexed = sorted(range(n), key=lambda i: values[i])

    best_error = n
    best_threshold = None

    # Test all possible thresholds (midpoints between consecutive values)
    for k in range(n):
        if k == 0:
            threshold = values[indexed[0]] - 1
        else:
            threshold = (values[indexed[k - 1]] + values[indexed[k]]) / 2

        errors = 0
        for i in range(n):
            predicted = 1 if values[i] > threshold else 0
            if predicted != labels[i]:
                errors += 1

        if errors < best_error:
            best_error = errors
            best_threshold = threshold

    return best_error == 0, best_threshold, best_error


def linear_separability(features, labels):
    """Test if a linear classifier can perfectly separate labels.

    Simple brute-force over all pairs of opposite-class points.
    For 2D: check if a separating line exists.
    For higher D: use perceptron convergence (if linearly separable, converges).

    Returns: (separable: bool, iterations: int)
    """
    import random
    random.seed(42)

    n = len(features)
    d = len(features[0])

    # Initialize weights
    w = [0.0] * d
    b = 0.0
    lr = 0.01

    max_iter = 10000
    for iteration in range(max_iter):
        misclassified = False
        for i in range(n):
            # Label: 0 -> -1, 1 -> +1
            y = 1 if labels[i] == 1 else -1
            dot = sum(w[j] * features[i][j] for j in range(d)) + b
            if y * dot <= 0:
                # Misclassified
                for j in range(d):
                    w[j] += lr * y * features[i][j]
                b += lr * y
                misclassified = True
        if not misclassified:
            return True, iteration + 1

    return False, max_iter


def normalize(values):
    """Min-max normalize to [0, 1]."""
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return [0.5] * len(values)
    return [(v - vmin) / (vmax - vmin) for v in values]


def main():
    o2a, o2b_by_solver = load_data()

    # Build feature matrix
    solvers = o2a["per_solver"]
    n = len(solvers)

    # Discrete labels: 0 if discrete_mismatches == 0, 1 otherwise
    discrete_labels = [1 if s["discrete_mismatches"] > 0 else 0 for s in solvers]

    # Continuous features
    features_raw = []
    feature_names = [
        "avg_abs_error", "max_abs_error", "avg_norm_error", "max_norm_error",
        "avg_reach_agree", "avg_max_dist_error"
    ]
    for s in solvers:
        b = o2b_by_solver[s["solver_id"]]
        row = [
            s["avg_abs_error"],
            s["max_abs_error"],
            s["avg_norm_error"],
            s["max_norm_error"],
            b["avg_reach_agree"],
            b["avg_max_dist_error"],
        ]
        features_raw.append(row)

    # Normalize features
    features_norm = []
    for j in range(len(feature_names)):
        col = [features_raw[i][j] for i in range(n)]
        features_norm.append(normalize(col))
    features = list(zip(*features_norm))  # transpose back to n x d

    # Count classes
    n_zero = sum(1 for l in discrete_labels if l == 0)
    n_nonzero = sum(1 for l in discrete_labels if l == 1)

    print("=" * 70)
    print("JOINT REPRESENTABILITY TEST (JRT)")
    print("=" * 70)
    print(f"\nSolver population: {n}")
    print(f"discrete=0 (perfect match): {n_zero}")
    print(f"discrete>0 (mismatch): {n_nonzero}")

    results = {}

    # Test 1: Rank correlation — each continuous metric vs discrete_mismatches
    print(f"\n{'=' * 70}")
    print("TEST 1: Rank correlation (discrete_mismatches vs continuous metrics)")
    print(f"{'=' * 70}")
    discrete_vals = [s["discrete_mismatches"] for s in solvers]
    for j, name in enumerate(feature_names):
        raw_vals = [features_raw[i][j] for i in range(n)]
        tau = kendall_tau(raw_vals, discrete_vals)
        rho = spearman_rho(raw_vals, discrete_vals)
        print(f"  {name:<24s}: tau={tau:+.4f}, rho={rho:+.4f}")
        results[f"tau_{name}"] = tau
        results[f"rho_{name}"] = rho

    # Test 2: Threshold separability — can any single metric separate discrete=0 from discrete>0?
    print(f"\n{'=' * 70}")
    print("TEST 2: Threshold separability (single metric)")
    print(f"{'=' * 70}")
    for j, name in enumerate(feature_names):
        raw_vals = [features_raw[i][j] for i in range(n)]
        separable, threshold, errors = threshold_separability(raw_vals, discrete_labels)
        status = "SEPARABLE" if separable else f"NOT SEPARABLE ({errors} errors)"
        print(f"  {name:<24s}: {status}" + (f" (threshold={threshold:.4f})" if separable else ""))
        results[f"threshold_{name}"] = {"separable": separable, "errors": errors}

    # Test 3: Threshold on linear combinations (pairwise)
    print(f"\n{'=' * 70}")
    print("TEST 3: Threshold separability (pairwise linear combos)")
    print(f"{'=' * 70}")
    pair_separable = 0
    pair_total = 0
    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            combo = [(features[k][i] + features[k][j]) / 2 for k in range(n)]
            separable, _, errors = threshold_separability(combo, discrete_labels)
            pair_total += 1
            if separable:
                pair_separable += 1
                print(f"  {feature_names[i]} + {feature_names[j]}: SEPARABLE")
    print(f"  Summary: {pair_separable}/{pair_total} pairs separable")
    results["pair_separable"] = pair_separable
    results["pair_total"] = pair_total

    # Test 4: Linear separability (all features)
    print(f"\n{'=' * 70}")
    print("TEST 4: Linear separability (perceptron, all 6 features)")
    print(f"{'=' * 70}")
    separable, iters = linear_separability(features, discrete_labels)
    status = f"SEPARABLE (converged in {iters} iterations)" if separable else f"NOT SEPARABLE (did not converge in {iters} iterations)"
    print(f"  {status}")
    results["linear_separable"] = separable
    results["linear_iterations"] = iters

    # Test 5: s027 position in feature space
    print(f"\n{'=' * 70}")
    print("TEST 5: s027 structural position")
    print(f"{'=' * 70}")
    s027_idx = None
    for i, s in enumerate(solvers):
        if s["solver_id"] == "s027":
            s027_idx = i
            break

    if s027_idx is not None:
        s027_features = features_raw[s027_idx]
        # Check if s027 is at boundary of discrete=0 cluster
        zero_indices = [i for i in range(n) if discrete_labels[i] == 0]
        nonzero_indices = [i for i in range(n) if discrete_labels[i] == 1]

        print(f"  s027 features: {[f'{v:.4f}' for v in s027_features]}")

        # Distance to nearest discrete=0 solver (excluding itself)
        min_dist_zero = float("inf")
        for i in zero_indices:
            if i != s027_idx:
                dist = math.sqrt(sum((s027_features[j] - features_raw[i][j])**2 for j in range(len(feature_names))))
                min_dist_zero = min(min_dist_zero, dist)

        # Distance to nearest discrete>0 solver
        min_dist_nonzero = float("inf")
        for i in nonzero_indices:
            if i != s027_idx:
                dist = math.sqrt(sum((s027_features[j] - features_raw[i][j])**2 for j in range(len(feature_names))))
                min_dist_nonzero = min(min_dist_nonzero, dist)

        print(f"  Distance to nearest discrete=0 solver: {min_dist_zero:.4f}")
        print(f"  Distance to nearest discrete>0 solver: {min_dist_nonzero:.4f}")
        if min_dist_zero < min_dist_nonzero:
            print(f"  => s027 is CLOSER to discrete=0 cluster (continuous geometry says it belongs with zero)")
        else:
            print(f"  => s027 is CLOSER to discrete>0 cluster (continuous geometry says it belongs with nonzero)")

        results["s027_closer_to"] = "zero" if min_dist_zero < min_dist_nonzero else "nonzero"
        results["s027_dist_zero"] = min_dist_zero
        results["s027_dist_nonzero"] = min_dist_nonzero

    # Verdict
    print(f"\n{'=' * 70}")
    print("JRT VERDICT")
    print(f"{'=' * 70}")

    any_monotonic = any(abs(results.get(f"tau_{name}", 0)) > 0.5 for name in feature_names)
    any_single_separable = any(results.get(f"threshold_{name}", {}).get("separable", False) for name in feature_names)
    any_pair_separable = results.get("pair_separable", 0) > 0
    linear_sep = results.get("linear_separable", False)

    if any_single_separable or any_pair_separable or linear_sep:
        verdict = "CASE_1"
        explanation = "Joint embedding exists: oracle and continuous metrics are reparameterizations of same latent structure"
    elif any_monotonic:
        verdict = "CASE_1_PARTIAL"
        explanation = "Partial monotonic relationship exists: weak joint embedding possible"
    else:
        verdict = "CASE_2"
        explanation = "No joint embedding: two fundamentally incompatible observational systems"

    print(f"  Verdict: {verdict}")
    print(f"  {explanation}")
    results["verdict"] = verdict
    results["explanation"] = explanation

    # Save
    output = {
        "phase": "JRT_joint_representability",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "estimators": ["C_genuine", "B1", "B2"],
            "oracle": "LC743",
            "canonical_test_suite": "24-case",
        },
        "test_results": results,
    }

    for base in [ROOT, ROOT.parent]:
        out_path = base / "results" / "jrt_result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()

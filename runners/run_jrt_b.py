"""JRT-b — Basis Stability Test.

Tests whether the separating hyperplane remains stable under alternative
continuous embeddings.

Distinguishes:
  Case A: true shared latent structure (stable under re-embedding)
  Case B: accidental linear separability in a convenient representation (unstable)

Basis perturbations:
  1. Random orthogonal rotations (10 trials)
  2. Feature dropout (leave-one-out, 6 conditions)
  3. Random linear combinations (10 trials)
  4. PCA projection (2D, 3D, 4D, 5D)
  5. Noise injection (3 noise levels)

For each perturbation:
  - Recompute linear separability (perceptron convergence)
  - Track s027 classification stability
  - Measure boundary distance changes

No narrative synthesis.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

random.seed(42)


def load_data():
    """Load O2-A and O2-B per-solver results."""
    for base in [ROOT, ROOT.parent]:
        o2a_path = base / "results" / "o2a_scoring.json"
        o2b_path = base / "results" / "o2b_resolution.json"
        if o2a_path.exists() and o2b_path.exists():
            o2a = json.loads(o2a_path.read_text(encoding="utf-8"))
            o2b = json.loads(o2b_path.read_text(encoding="utf-8"))
            o2b_by_solver = {s["solver_id"]: s for s in o2b["per_solver"]}
            return o2a, o2b_by_solver
    raise FileNotFoundError("O2 results not found")


def normalize(values):
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return [0.5] * len(values)
    return [(v - vmin) / (vmax - vmin) for v in values]


def perceptron(features, labels, max_iter=10000, lr=0.01):
    """Train perceptron. Returns (converged, iterations, weights, bias)."""
    n = len(features)
    d = len(features[0])
    w = [0.0] * d
    b = 0.0

    for iteration in range(max_iter):
        misclassified = False
        for i in range(n):
            y = 1 if labels[i] == 1 else -1
            dot = sum(w[j] * features[i][j] for j in range(d)) + b
            if y * dot <= 0:
                for j in range(d):
                    w[j] += lr * y * features[i][j]
                b += lr * y
                misclassified = True
        if not misclassified:
            return True, iteration + 1, w, b

    return False, max_iter, w, b


def decision_value(features, w, b):
    """Compute signed distance from hyperplane for each point."""
    return [sum(w[j] * f[j] for j in range(len(w))) + b for f in features]


def random_rotation_matrix(d, rng):
    """Generate a random orthogonal rotation matrix using Gram-Schmidt."""
    # Generate random matrix
    mat = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(d)]
    # Gram-Schmidt orthogonalization
    for i in range(d):
        for j in range(i):
            dot = sum(mat[i][k] * mat[j][k] for k in range(d))
            for k in range(d):
                mat[i][k] -= dot * mat[j][k]
        norm = math.sqrt(sum(mat[i][k] ** 2 for k in range(d)))
        if norm > 1e-10:
            for k in range(d):
                mat[i][k] /= norm
    return mat


def mat_vec_mul(mat, vec):
    return [sum(mat[i][j] * vec[j] for j in range(len(vec))) for i in range(len(mat))]


def apply_rotation(features, mat):
    return [mat_vec_mul(mat, f) for f in features]


def pca(features, d_out):
    """Simple PCA projection to d_out dimensions."""
    n = len(features)
    d = len(features[0])

    # Center
    mean = [sum(features[i][j] for i in range(n)) / n for j in range(d)]
    centered = [[features[i][j] - mean[j] for j in range(d)] for i in range(n)]

    # Covariance matrix
    cov = [[sum(centered[i][j] * centered[i][k] for i in range(n)) / n
            for k in range(d)] for j in range(d)]

    # Power iteration for top d_out eigenvectors
    eigenvectors = []
    for _ in range(d_out):
        v = [random.gauss(0, 1) for _ in range(d)]
        norm = math.sqrt(sum(x ** 2 for x in v))
        v = [x / norm for x in v]

        for _ in range(100):
            # Multiply by covariance
            new_v = [sum(cov[j][k] * v[k] for k in range(d)) for j in range(d)]
            # Subtract previous eigenvectors
            for ev in eigenvectors:
                dot = sum(new_v[j] * ev[j] for j in range(d))
                new_v = [new_v[j] - dot * ev[j] for j in range(d)]
            norm = math.sqrt(sum(x ** 2 for x in new_v))
            if norm > 1e-10:
                new_v = [x / norm for x in new_v]
            if all(abs(new_v[j] - v[j]) < 1e-8 for j in range(d)):
                break
            v = new_v
        eigenvectors.append(v)

    # Project
    projected = []
    for i in range(n):
        row = [sum(centered[i][j] * ev[j] for j in range(d)) for ev in eigenvectors]
        projected.append(row)
    return projected


def main():
    o2a, o2b_by_solver = load_data()
    solvers = o2a["per_solver"]
    n = len(solvers)

    # Build feature matrix
    feature_names = [
        "avg_abs_error", "max_abs_error", "avg_norm_error", "max_norm_error",
        "avg_reach_agree", "avg_max_dist_error"
    ]
    features_raw = []
    for s in solvers:
        b = o2b_by_solver[s["solver_id"]]
        features_raw.append([
            s["avg_abs_error"], s["max_abs_error"],
            s["avg_norm_error"], s["max_norm_error"],
            b["avg_reach_agree"], b["avg_max_dist_error"],
        ])

    # Normalize
    features_norm = []
    for j in range(len(feature_names)):
        col = [features_raw[i][j] for i in range(n)]
        features_norm.append(normalize(col))
    features = list(zip(*features_norm))

    discrete_labels = [1 if s["discrete_mismatches"] > 0 else 0 for s in solvers]
    s027_idx = next(i for i, s in enumerate(solvers) if s["solver_id"] == "s027")

    # Baseline
    base_converged, base_iters, base_w, base_b = perceptron(features, discrete_labels)
    base_dv = decision_value(features, base_w, base_b)
    base_s027_class = 1 if base_dv[s027_idx] > 0 else 0

    print("=" * 70)
    print("JRT-b: BASIS STABILITY TEST")
    print("=" * 70)
    print(f"\nBaseline: converged={base_converged}, iters={base_iters}, s027_class={base_s027_class}")
    print(f"Baseline decision values range: [{min(base_dv):.4f}, {max(base_dv):.4f}]")

    results = {
        "baseline": {
            "converged": base_converged,
            "iterations": base_iters,
            "s027_class": base_s027_class,
            "dv_min": min(base_dv),
            "dv_max": max(base_dv),
        }
    }

    # Test 1: Random orthogonal rotations
    print(f"\n{'=' * 70}")
    print("TEST 1: Random orthogonal rotations (10 trials)")
    print(f"{'=' * 70}")
    rot_results = []
    for trial in range(10):
        rng = random.Random(trial * 1000)
        rot_mat = random_rotation_matrix(6, rng)
        rotated = apply_rotation(features, rot_mat)
        conv, iters, w, b = perceptron(rotated, discrete_labels)
        dv = decision_value(rotated, w, b)
        s027_class = 1 if dv[s027_idx] > 0 else 0
        rot_results.append({
            "trial": trial,
            "converged": conv,
            "iterations": iters,
            "s027_class": s027_class,
            "dv_min": min(dv),
            "dv_max": max(dv),
        })
        status = "CONVERGED" if conv else "DID NOT CONVERGE"
        print(f"  Trial {trial}: {status} ({iters} iters), s027={s027_class}")

    rot_converged = sum(1 for r in rot_results if r["converged"])
    rot_s027_stable = sum(1 for r in rot_results if r["s027_class"] == base_s027_class)
    print(f"  Summary: {rot_converged}/10 converged, {rot_s027_stable}/10 s027 stable")
    results["rotations"] = {
        "converged_count": rot_converged,
        "s027_stable_count": rot_s027_stable,
        "trials": rot_results,
    }

    # Test 2: Feature dropout (leave-one-out)
    print(f"\n{'=' * 70}")
    print("TEST 2: Feature dropout (leave-one-out)")
    print(f"{'=' * 70}")
    drop_results = []
    for drop_idx in range(6):
        dropped = [[f[j] for j in range(6) if j != drop_idx] for f in features]
        conv, iters, w, b = perceptron(dropped, discrete_labels)
        dv = decision_value(dropped, w, b)
        # Need to recompute s027 class in reduced space
        s027_class = 1 if dv[s027_idx] > 0 else 0
        drop_results.append({
            "dropped_feature": feature_names[drop_idx],
            "converged": conv,
            "iterations": iters,
            "s027_class": s027_class,
        })
        status = "CONVERGED" if conv else "DID NOT CONVERGE"
        print(f"  Drop {feature_names[drop_idx]}: {status} ({iters} iters), s027={s027_class}")

    drop_converged = sum(1 for r in drop_results if r["converged"])
    drop_s027_stable = sum(1 for r in drop_results if r["s027_class"] == base_s027_class)
    print(f"  Summary: {drop_converged}/6 converged, {drop_s027_stable}/6 s027 stable")
    results["feature_dropout"] = {
        "converged_count": drop_converged,
        "s027_stable_count": drop_s027_stable,
        "conditions": drop_results,
    }

    # Test 3: Random linear combinations
    print(f"\n{'=' * 70}")
    print("TEST 3: Random linear combinations (10 trials)")
    print(f"{'=' * 70}")
    combo_results = []
    for trial in range(10):
        rng = random.Random(trial * 2000)
        # Generate random 6x6 matrix
        mat = [[rng.gauss(0, 1) for _ in range(6)] for _ in range(6)]
        combo = [mat_vec_mul(mat, f) for f in features]
        conv, iters, w, b = perceptron(combo, discrete_labels)
        dv = decision_value(combo, w, b)
        s027_class = 1 if dv[s027_idx] > 0 else 0
        combo_results.append({
            "trial": trial,
            "converged": conv,
            "iterations": iters,
            "s027_class": s027_class,
        })
        status = "CONVERGED" if conv else "DID NOT CONVERGE"
        print(f"  Trial {trial}: {status} ({iters} iters), s027={s027_class}")

    combo_converged = sum(1 for r in combo_results if r["converged"])
    combo_s027_stable = sum(1 for r in combo_results if r["s027_class"] == base_s027_class)
    print(f"  Summary: {combo_converged}/10 converged, {combo_s027_stable}/10 s027 stable")
    results["random_combos"] = {
        "converged_count": combo_converged,
        "s027_stable_count": combo_s027_stable,
        "trials": combo_results,
    }

    # Test 4: PCA projection
    print(f"\n{'=' * 70}")
    print("TEST 4: PCA projection (2D, 3D, 4D, 5D)")
    print(f"{'=' * 70}")
    pca_results = []
    for d_out in [2, 3, 4, 5]:
        projected = pca(features, d_out)
        conv, iters, w, b = perceptron(projected, discrete_labels)
        dv = decision_value(projected, w, b)
        s027_class = 1 if dv[s027_idx] > 0 else 0
        pca_results.append({
            "dimensions": d_out,
            "converged": conv,
            "iterations": iters,
            "s027_class": s027_class,
        })
        status = "CONVERGED" if conv else "DID NOT CONVERGE"
        print(f"  PCA-{d_out}D: {status} ({iters} iters), s027={s027_class}")

    pca_converged = sum(1 for r in pca_results if r["converged"])
    pca_s027_stable = sum(1 for r in pca_results if r["s027_class"] == base_s027_class)
    print(f"  Summary: {pca_converged}/4 converged, {pca_s027_stable}/4 s027 stable")
    results["pca"] = {
        "converged_count": pca_converged,
        "s027_stable_count": pca_s027_stable,
        "conditions": pca_results,
    }

    # Test 5: Noise injection
    print(f"\n{'=' * 70}")
    print("TEST 5: Noise injection (3 levels)")
    print(f"{'=' * 70}")
    noise_results = []
    for noise_level in [0.01, 0.05, 0.10]:
        stable_count = 0
        for trial in range(10):
            rng = random.Random(trial * 3000 + int(noise_level * 1000))
            noisy = [[f[j] + rng.gauss(0, noise_level) for j in range(6)] for f in features]
            conv, iters, w, b = perceptron(noisy, discrete_labels)
            dv = decision_value(noisy, w, b)
            s027_class = 1 if dv[s027_idx] > 0 else 0
            if s027_class == base_s027_class:
                stable_count += 1
        noise_results.append({
            "noise_level": noise_level,
            "s027_stable_count": stable_count,
        })
        print(f"  Noise {noise_level}: s027 stable {stable_count}/10 trials")

    results["noise"] = {"conditions": noise_results}

    # Overall verdict
    print(f"\n{'=' * 70}")
    print("JRT-b VERDICT")
    print(f"{'=' * 70}")

    total_tests = (10 + 6 + 10 + 4)  # rotations + dropout + combos + pca
    total_converged = rot_converged + drop_converged + combo_converged + pca_converged
    total_s027_stable = rot_s027_stable + drop_s027_stable + combo_s027_stable + pca_s027_stable

    print(f"  Total basis perturbations: {total_tests}")
    print(f"  Converged (separable): {total_converged}/{total_tests}")
    print(f"  s027 classification stable: {total_s027_stable}/{total_tests}")

    if total_converged == total_tests and total_s027_stable == total_tests:
        verdict = "CASE_A"
        explanation = "Stable under re-embedding: true shared latent structure"
    elif total_converged >= total_tests * 0.8 and total_s027_stable >= total_tests * 0.8:
        verdict = "CASE_A_PARTIAL"
        explanation = "Mostly stable: weak shared latent structure with some representation dependence"
    elif total_converged >= total_tests * 0.5:
        verdict = "CASE_AMBIGUOUS"
        explanation = "Mixed stability: separation exists but is representation-dependent"
    else:
        verdict = "CASE_B"
        explanation = "Unstable under re-embedding: accidental linear separability"

    print(f"  Verdict: {verdict}")
    print(f"  {explanation}")

    results["verdict"] = verdict
    results["explanation"] = explanation
    results["total_tests"] = total_tests
    results["total_converged"] = total_converged
    results["total_s027_stable"] = total_s027_stable

    # Save
    output = {
        "phase": "JRTb_basis_stability",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "estimators": ["C_genuine", "B1", "B2"],
            "oracle": "LC743",
            "canonical_test_suite": "24-case",
        },
        "test_results": results,
    }

    for base in [ROOT, ROOT.parent]:
        out_path = base / "results" / "jrtb_result.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()

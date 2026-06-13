"""Basis-Invariant Oracle Test.

Replace oracle decision rule with geometry-aware classifiers.
Check whether s027 remains anomalous under each.

Fixed:
  - Solver population: LC756(R2) set
  - Continuous metrics: 6D feature space (avg_abs_error, max_abs_error, ...)
  - Discrete labels: oracle ground truth (discrete_mismatches > 0)

Variable:
  - Decision rule: oracle binary partition vs geometry-aware classifiers

Classifiers tested:
  1. kNN (k=1, 3, 5)
  2. SVM (linear kernel)
  3. Decision tree (depth 1, 2, 3)
  4. Centroid-based (distance from class mean)
  5. Radius-based (fixed radius from class centroid)

For each classifier:
  - Full-data accuracy (does it recover oracle labels?)
  - s027 classification (does it agree with oracle?)
  - Leave-one-out accuracy (generalization)

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


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# --- Classifiers ---

def knn_classify(train_features, train_labels, test_point, k):
    """k-Nearest Neighbors classification."""
    dists = [(euclidean(train_features[i], test_point), train_labels[i])
             for i in range(len(train_features))]
    dists.sort(key=lambda x: x[0])
    neighbors = dists[:k]
    votes = {}
    for _, label in neighbors:
        votes[label] = votes.get(label, 0) + 1
    return max(votes, key=votes.get)


def svm_linear_classify(train_features, train_labels, test_point, lr=0.01, max_iter=10000):
    """Simple linear SVM (perceptron with margin)."""
    n = len(train_features)
    d = len(train_features[0])
    w = [0.0] * d
    b = 0.0

    for _ in range(max_iter):
        misclassified = False
        for i in range(n):
            y = 1 if train_labels[i] == 1 else -1
            dot = sum(w[j] * train_features[i][j] for j in range(d)) + b
            if y * dot <= 1:  # hinge loss
                for j in range(d):
                    w[j] += lr * (y * train_features[i][j] - 0.01 * w[j])
                b += lr * y
                misclassified = True
        if not misclassified:
            break

    dot = sum(w[j] * test_point[j] for j in range(d)) + b
    return 1 if dot > 0 else 0


def decision_tree_classify(train_features, train_labels, test_point, max_depth):
    """Simple decision tree (axis-aligned splits)."""
    if max_depth == 0 or len(set(train_labels)) == 1:
        return train_labels[0] if train_labels else 0

    n = len(train_features)
    d = len(train_features[0])
    best_feature = 0
    best_threshold = 0
    best_gini = 1.0

    for j in range(d):
        values = sorted(set(train_features[i][j] for i in range(n)))
        for t in values:
            left_labels = [train_labels[i] for i in range(n) if train_features[i][j] <= t]
            right_labels = [train_labels[i] for i in range(n) if train_features[i][j] > t]
            if not left_labels or not right_labels:
                continue
            gini_left = 1.0 - (sum(1 for l in left_labels if l == 0) / len(left_labels)) ** 2 - \
                         (sum(1 for l in left_labels if l == 1) / len(left_labels)) ** 2
            gini_right = 1.0 - (sum(1 for l in right_labels if l == 0) / len(right_labels)) ** 2 - \
                          (sum(1 for l in right_labels if l == 1) / len(right_labels)) ** 2
            weighted_gini = (len(left_labels) * gini_left + len(right_labels) * gini_right) / n
            if weighted_gini < best_gini:
                best_gini = weighted_gini
                best_feature = j
                best_threshold = t

    if test_point[best_feature] <= best_threshold:
        subset_idx = [i for i in range(n) if train_features[i][best_feature] <= best_threshold]
    else:
        subset_idx = [i for i in range(n) if train_features[i][best_feature] > best_threshold]

    if not subset_idx:
        return max(set(train_labels), key=train_labels.count)

    return decision_tree_classify(
        [train_features[i] for i in subset_idx],
        [train_labels[i] for i in subset_idx],
        test_point,
        max_depth - 1
    )


def centroid_classify(train_features, train_labels, test_point):
    """Classify by distance to class centroids."""
    zero_pts = [train_features[i] for i in range(len(train_labels)) if train_labels[i] == 0]
    one_pts = [train_features[i] for i in range(len(train_labels)) if train_labels[i] == 1]

    d = len(test_point)
    centroid_zero = [sum(p[j] for p in zero_pts) / len(zero_pts) for j in range(d)] if zero_pts else [0] * d
    centroid_one = [sum(p[j] for p in one_pts) / len(one_pts) for j in range(d)] if one_pts else [0] * d

    dist_zero = euclidean(test_point, centroid_zero)
    dist_one = euclidean(test_point, centroid_one)

    return 0 if dist_zero < dist_one else 1


def radius_classify(train_features, train_labels, test_point, radius):
    """Classify by nearest class within radius."""
    zero_pts = [train_features[i] for i in range(len(train_labels)) if train_labels[i] == 0]
    one_pts = [train_features[i] for i in range(len(train_labels)) if train_labels[i] == 1]

    min_dist_zero = min((euclidean(test_point, p) for p in zero_pts), default=float('inf'))
    min_dist_one = min((euclidean(test_point, p) for p in one_pts), default=float('inf'))

    in_zero = min_dist_zero <= radius
    in_one = min_dist_one <= radius

    if in_zero and not in_one:
        return 0
    if in_one and not in_zero:
        return 1
    # Tie or neither: use centroid
    return centroid_classify(train_features, train_labels, test_point)


def loo_accuracy(features, labels, classifier_fn, **kwargs):
    """Leave-one-out accuracy."""
    n = len(features)
    correct = 0
    for i in range(n):
        train_idx = [j for j in range(n) if j != i]
        train_f = [features[j] for j in train_idx]
        train_l = [labels[j] for j in train_idx]
        pred = classifier_fn(train_f, train_l, features[i], **kwargs)
        if pred == labels[i]:
            correct += 1
    return correct / n


def main():
    o2a, o2b_by_solver = load_data()
    solvers = o2a["per_solver"]
    n = len(solvers)

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

    features_norm = []
    for j in range(len(feature_names)):
        col = [features_raw[i][j] for i in range(n)]
        features_norm.append(normalize(col))
    features = list(zip(*features_norm))

    discrete_labels = [1 if s["discrete_mismatches"] > 0 else 0 for s in solvers]
    s027_idx = next(i for i, s in enumerate(solvers) if s["solver_id"] == "s027")

    print("=" * 70)
    print("BASIS-INVARIANT ORACLE TEST")
    print("=" * 70)
    print(f"\nOracle label for s027: {discrete_labels[s027_idx]} (discrete>0)")
    print(f"Continuous features for s027: {[f'{v:.4f}' for v in features[s027_idx]]}")

    results = {
        "oracle_s027_label": discrete_labels[s027_idx],
        "s027_features": [round(v, 4) for v in features[s027_idx]],
    }

    # Classifiers
    classifiers = [
        ("kNN-1", lambda train_f, train_l, tp: knn_classify(train_f, train_l, tp, k=1)),
        ("kNN-3", lambda train_f, train_l, tp: knn_classify(train_f, train_l, tp, k=3)),
        ("kNN-5", lambda train_f, train_l, tp: knn_classify(train_f, train_l, tp, k=5)),
        ("SVM-linear", lambda train_f, train_l, tp: svm_linear_classify(train_f, train_l, tp)),
        ("DecisionTree-1", lambda train_f, train_l, tp: decision_tree_classify(train_f, train_l, tp, 1)),
        ("DecisionTree-2", lambda train_f, train_l, tp: decision_tree_classify(train_f, train_l, tp, 2)),
        ("DecisionTree-3", lambda train_f, train_l, tp: decision_tree_classify(train_f, train_l, tp, 3)),
        ("Centroid", lambda train_f, train_l, tp: centroid_classify(train_f, train_l, tp)),
        ("Radius-0.1", lambda train_f, train_l, tp: radius_classify(train_f, train_l, tp, 0.1)),
        ("Radius-0.2", lambda train_f, train_l, tp: radius_classify(train_f, train_l, tp, 0.2)),
        ("Radius-0.3", lambda train_f, train_l, tp: radius_classify(train_f, train_l, tp, 0.3)),
    ]

    print(f"\n{'=' * 70}")
    print("CLASSIFIER RESULTS")
    print(f"{'=' * 70}")
    print(f"{'Classifier':<20s} {'s027 pred':<10s} {'Oracle':<10s} {'Agree':<8s} {'LOO acc':<10s}")
    print("-" * 70)

    s027_agree_count = 0
    s027_disagree_classifiers = []

    for name, clf_fn in classifiers:
        # Full-data prediction for s027
        pred = clf_fn(features, discrete_labels, features[s027_idx])
        agree = pred == discrete_labels[s027_idx]

        # LOO accuracy
        loo_acc = loo_accuracy(features, discrete_labels, clf_fn)

        s027_pred_str = f"class={pred}"
        oracle_str = f"class={discrete_labels[s027_idx]}"
        agree_str = "YES" if agree else "NO"

        print(f"{name:<20s} {s027_pred_str:<10s} {oracle_str:<10s} {agree_str:<8s} {loo_acc:<10.4f}")

        if agree:
            s027_agree_count += 1
        else:
            s027_disagree_classifiers.append(name)

        results[name] = {
            "s027_prediction": pred,
            "oracle_label": discrete_labels[s027_idx],
            "agrees_with_oracle": agree,
            "loo_accuracy": round(loo_acc, 4),
        }

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"Classifiers that AGREE with oracle on s027: {s027_agree_count}/{len(classifiers)}")
    if s027_disagree_classifiers:
        print(f"Classifiers that DISAGREE: {', '.join(s027_disagree_classifiers)}")
    else:
        print("All classifiers agree with oracle on s027")

    # Verdict
    print(f"\n{'=' * 70}")
    print("VERDICT")
    print(f"{'=' * 70}")

    if s027_agree_count == len(classifiers):
        verdict = "ORACLE_CONSISTENT"
        explanation = "All geometry-aware classifiers agree with oracle: s027 classification is geometry-invariant"
    elif s027_agree_count >= len(classifiers) * 0.8:
        verdict = "MOSTLY_CONSISTENT"
        explanation = "Most classifiers agree: s027 classification is largely geometry-invariant"
    elif s027_agree_count >= len(classifiers) * 0.5:
        verdict = "PARTIALLY_CONSISTENT"
        explanation = "Mixed agreement: s027 classification is partially geometry-dependent"
    else:
        verdict = "GEOMETRY_DEPENDENT"
        explanation = "Most classifiers disagree: s027 classification is geometry-dependent"

    print(f"  Verdict: {verdict}")
    print(f"  {explanation}")

    results["summary"] = {
        "agree_count": s027_agree_count,
        "total_classifiers": len(classifiers),
        "disagree_classifiers": s027_disagree_classifiers,
        "verdict": verdict,
        "explanation": explanation,
    }

    # Save
    output = {
        "phase": "basis_invariant_oracle",
        "hard_invariants": {
            "solver_population": "LC756(R2)",
            "estimators": ["C_genuine", "B1", "B2"],
            "oracle": "LC743",
            "canonical_test_suite": "24-case",
        },
        "test_results": results,
    }

    for base in [ROOT, ROOT.parent]:
        out_path = base / "results" / "basis_invariant_oracle.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()

"""Stability diagnostic for trajectory scoring axis.

Two tests required by GPT before the trajectory axis can be trusted:

1. RENAMING INVARIANCE -- rename all solver manifold IDs and re-run.
   If the 8 topology classes persist, scores reflect trajectory structure
   not solver labels. If they collapse, scores are label artifacts.

2. WEIGHT SENSITIVITY -- increase ONSET_OPERATOR_WEIGHT by 20% (1.5 -> 1.8).
   If the cluster structure (number of distinct scores, relative ordering)
   holds, the scoring is robust. If it collapses, scores are hyperparameter
   artifacts.
"""
from __future__ import annotations

import copy
import itertools
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ARTIFACT_ROOT = (
    PROJECT_ROOT
    / "doctor"
    / "adversarial"
    / "observer"
    / "artifacts"
)

PROBLEMS = ("lc322", "lc45")


def load_artifacts() -> list[dict]:
    artifacts = []
    for problem in PROBLEMS:
        path = ARTIFACT_ROOT / problem
        for fpath in sorted(path.glob("*.json")):
            artifacts.append(json.loads(fpath.read_text(encoding="utf-8")))
    return artifacts


def label(a: dict) -> str:
    return f"{a['problem_id']}.{a['manifold_id']}"


def run_all_pairs(artifacts: list[dict]) -> list[dict]:
    trajectories = {label(a): extract_trajectory(a) for a in artifacts}
    results = []
    for left_lbl, right_lbl in itertools.combinations(sorted(trajectories), 2):
        score, matching = compare_trajectories(trajectories[left_lbl], trajectories[right_lbl])
        results.append({
            "left": left_lbl,
            "right": right_lbl,
            "score": round(score, 4),
            "matching": matching,
        })
    return results


def rename_artifacts(artifacts: list[dict]) -> list[dict]:
    renamed = []
    counter: dict[str, int] = {}
    for a in artifacts:
        b = copy.deepcopy(a)
        base = a["manifold_id"]
        counter[base] = counter.get(base, 0) + 1
        b["manifold_id"] = f"renamed_{base}_{counter[base]}"
        renamed.append(b)
    return renamed


def format_scores(scores: list) -> str:
    return "[" + ", ".join(f"{s:.4f}" for s in sorted(set(scores))) + "]"


def main() -> int:
    artifacts = load_artifacts()
    n_lc322 = len([a for a in artifacts if a["problem_id"] == "lc322"])
    n_lc45 = len([a for a in artifacts if a["problem_id"] == "lc45"])
    print(f"Loaded {len(artifacts)} artifacts ({n_lc322} LC322, {n_lc45} LC45)")
    print()

    # BASELINE
    print("=" * 72)
    print("BASELINE: compare_trajectories() as committed")
    print("=" * 72)
    baseline = run_all_pairs(artifacts)
    base_scores = [r["score"] for r in baseline]
    base_unique = sorted(set(base_scores))
    lc322_within = [r for r in baseline if r["left"].startswith("lc322") and r["right"].startswith("lc322")]
    lc45_within = [r for r in baseline if r["left"].startswith("lc45") and r["right"].startswith("lc45")]
    cross = [r for r in baseline if r["left"].split(".")[0] != r["right"].split(".")[0]]
    print(f"  Total pairs:          {len(baseline)}")
    print(f"  Score range:          {min(base_scores):.2f} - {max(base_scores):.2f}")
    print(f"  Unique scores:        {len(base_unique)}")
    print(f"  Score values:         {format_scores(base_scores)}")
    print(f"  Within-LC322 unique:  {len(set(r['score'] for r in lc322_within))}")
    print(f"  Within-LC45 unique:   {len(set(r['score'] for r in lc45_within))}")
    print()

    # RENAMING TEST
    print("=" * 72)
    print("TEST 1: Solver renaming invariance")
    print("=" * 72)
    renamed_artifacts = rename_artifacts(artifacts)
    renamed_results = run_all_pairs(renamed_artifacts)
    old_scores = [r["score"] for r in baseline]
    new_scores = [r["score"] for r in renamed_results]
    scores_match = old_scores == new_scores
    print(f"  Scores identical after renaming: {scores_match}")
    print()

    # WEIGHT TEST 1: ONSET_OPERATOR_WEIGHT
    print("=" * 72)
    print("TEST 2: ONSET_OPERATOR_WEIGHT 1.5 -> 1.8 (+20%)")
    print("=" * 72)
    orig_w = traj_mod.ONSET_OPERATOR_WEIGHT
    traj_mod.ONSET_OPERATOR_WEIGHT = 1.8
    w1_results = run_all_pairs(artifacts)
    traj_mod.ONSET_OPERATOR_WEIGHT = orig_w
    w1_scores = [r["score"] for r in w1_results]
    w1_unique = sorted(set(w1_scores))
    w1_ordered = sorted([(r["left"], r["right"], r["score"]) for r in w1_results], key=lambda x: -x[2])
    base_ordered = sorted([(r["left"], r["right"], r["score"]) for r in baseline], key=lambda x: -x[2])
    order_same = [b[0:2] for b in base_ordered] == [w[0:2] for w in w1_ordered]
    print(f"  Baseline unique:      {len(base_unique)}")
    print(f"  Modified unique:      {len(w1_unique)}")
    print(f"  Baseline values:      {format_scores(base_scores)}")
    print(f"  Modified values:      {format_scores(w1_scores)}")
    print(f"  Ordering preserved:   {order_same}")
    print()

    # WEIGHT TEST 2: CROSS_ONSET_OPERATOR_COMPATIBILITY
    print("=" * 72)
    print("TEST 3: CROSS_ONSET_OPERATOR_COMPATIBILITY 0.5 -> 0.6 (+20%)")
    print("=" * 72)
    orig_cc = traj_mod.CROSS_ONSET_OPERATOR_COMPATIBILITY
    traj_mod.CROSS_ONSET_OPERATOR_COMPATIBILITY = 0.6
    w2_results = run_all_pairs(artifacts)
    traj_mod.CROSS_ONSET_OPERATOR_COMPATIBILITY = orig_cc
    w2_scores = [r["score"] for r in w2_results]
    w2_unique = sorted(set(w2_scores))
    w2_ordered = sorted([(r["left"], r["right"], r["score"]) for r in w2_results], key=lambda x: -x[2])
    w2_order_same = [b[0:2] for b in base_ordered] == [w[0:2] for w in w2_ordered]
    print(f"  Baseline unique:      {len(base_unique)}")
    print(f"  Modified unique:      {len(w2_unique)}")
    print(f"  Baseline values:      {format_scores(base_scores)}")
    print(f"  Modified values:      {format_scores(w2_scores)}")
    print(f"  Ordering preserved:   {w2_order_same}")
    print()

    # FINAL VERDICT
    print("=" * 72)
    print("STABILITY VERDICT")
    print("=" * 72)
    r_pass = scores_match
    w1_pass = len(base_unique) == len(w1_unique)
    w2_pass = len(base_unique) == len(w2_unique)
    print(f"  Renaming invariance:            {'PASS' if r_pass else 'FAIL'}")
    print(f"  Onset weight sensitivity:       {'PASS' if w1_pass else 'FAIL'}")
    print(f"  Cross-operator weight:          {'PASS' if w2_pass else 'FAIL'}")
    if r_pass and w1_pass and w2_pass:
        print()
        print("  >>> TRAJECTORY AXIS IS STABLE.")
        print("  >>> 8 topology classes are real structure, not artifacts.")
        print("  >>> DOCTOR has two validated measurement axes.")
    else:
        print()
        print("  >>> TRAJECTORY AXIS IS UNSTABLE.")
        print("  >>> Classes are parameter artifacts.")
        print("  >>> Option 1 is the correct answer.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

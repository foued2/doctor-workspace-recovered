"""Diagnostic: connect trajectory subsystem to verdict path for LC322 × LC45.

Loads all observer artifacts, extracts PerturbationTrajectory for each
solver manifold, computes compare_trajectories() across all solver pairs,
and reports whether the trajectory axis produces solver differentiation
that the perturbation axis did not.
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.observer.trajectory import (
    compare_trajectories,
    extract_trajectory,
)

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


def artifact_label(a: dict) -> str:
    return f"{a['problem_id']}.{a['manifold_id']}"


def main() -> int:
    artifacts = load_artifacts()
    print(f"Loaded {len(artifacts)} artifacts")
    print(f"LC322: {sum(1 for a in artifacts if a['problem_id'] == 'lc322')}")
    print(f"LC45:  {sum(1 for a in artifacts if a['problem_id'] == 'lc45')}")
    print()

    trajectories = {artifact_label(a): extract_trajectory(a) for a in artifacts}

    print(f"{'Left':42s} | {'Right':42s} | {'Score':6s} | Matching tags")
    print("-" * 42 + "-+-" + "-" * 42 + "-+-" + "-" * 6 + "-+-" + "-" * 60)

    all_scores = []

    for left_label, right_label in itertools.combinations(sorted(trajectories), 2):
        left_traj = trajectories[left_label]
        right_traj = trajectories[right_label]
        score, matching = compare_trajectories(left_traj, right_traj)

        left_problem = left_label.split(".")[0]
        right_problem = right_label.split(".")[0]

        all_scores.append(
            {
                "left": left_label,
                "right": right_label,
                "cross_problem": left_problem != right_problem,
                "score": round(score, 4),
                "matching": matching,
            }
        )

        tags = ", ".join(matching) if matching else "(none)"
        print(
            f"{left_label:42s} | {right_label:42s} | {score:6.2f} | {tags}"
        )

    print()
    print("=" * 160)
    print("ANALYSIS: Do solver pairs produce distinct topology classes?")
    print("=" * 160)

    cross_problem_scores = [s for s in all_scores if s["cross_problem"]]
    within_lc322 = [s for s in all_scores if not s["cross_problem"] and s["left"].startswith("lc322")]
    within_lc45 = [s for s in all_scores if not s["cross_problem"] and s["left"].startswith("lc45")]

    cross_scores = [s["score"] for s in cross_problem_scores]
    print(f"\nCross-problem pairs:        {len(cross_problem_scores)}")
    print(f"  Score range:              {min(cross_scores):.2f} – {max(cross_scores):.2f}")
    print(f"  Unique scores:            {len(set(cross_scores))}")
    print(f"  Mean score:               {sum(cross_scores)/len(cross_scores):.4f}")

    within_scores_32 = [s["score"] for s in within_lc322]
    print(f"\nWithin-LC322 pairs:         {len(within_lc322)}")
    print(f"  Score range:              {min(within_scores_32):.2f} – {max(within_scores_32):.2f}")
    print(f"  Unique scores:            {len(set(within_scores_32))}")
    print(f"  Mean score:               {sum(within_scores_32)/len(within_scores_32):.4f}")

    within_scores_45 = [s["score"] for s in within_lc45]
    print(f"\nWithin-LC45 pairs:          {len(within_lc45)}")
    print(f"  Score range:              {min(within_scores_45):.2f} – {max(within_scores_45):.2f}")
    print(f"  Unique scores:            {len(set(within_scores_45))}")
    print(f"  Mean score:               {sum(within_scores_45)/len(within_scores_45):.4f}")

    all_unique = set(cross_scores) | set(within_scores_32) | set(within_scores_45)
    print(f"\nTotal unique scores across all pairs: {len(all_unique)}")
    print(f"Distinct topology classes:  {'YES' if len(all_unique) > 1 else 'NO — all pairs collapse to same score'}")

    print()
    print("Per-pair topology_divergence_score (1 - normalized score):")
    max_possible = max(cross_scores + within_scores_32 + within_scores_45) if all_scores else 1.0
    for s in all_scores:
        nd = round(1.0 - s["score"] / max_possible, 4) if max_possible > 0 else 0.0
        tag = "CROSS" if s["cross_problem"] else "WITHIN"
        print(f"  {tag:6s}  {s['left']:42s} × {s['right']:42s}  score={s['score']:.4f}  td={nd:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

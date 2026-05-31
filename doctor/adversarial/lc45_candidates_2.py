"""LC45 ingestion gate runner — suffix_reach_invariant, 3 solvers, narrow falsification."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc45_candidates import lc45_dp, lc45_greedy_frontier, lc45_naive_greedy
from doctor.adversarial.lc45_ground_truth import lc45_brute_force, GroundTruthDomainError
from doctor.adversarial.lc45_ingestion_gate import lc45_ingestion_gate


REFERENCE_TESTS: list[dict[str, list[int]]] = [
    {"nums": [2, 3, 1, 1, 4]},
    {"nums": [2, 3, 0, 1, 4]},
    {"nums": [1, 2, 1, 1, 1]},
    {"nums": [2, 2, 1, 1, 1]},
    {"nums": [3, 1, 2, 1, 1]},
    {"nums": [1, 3, 1, 1, 1]},
    {"nums": [2, 4, 1, 1, 1, 1]},
    {"nums": [3, 5, 1, 1, 1, 1, 1]},
    {"nums": [2, 5, 0, 0, 1, 1, 1]},
    {"nums": [1, 1, 1, 1]},
    {"nums": [2, 2, 2, 2]},
    {"nums": [3, 3, 3, 3]},
]


def main() -> int:
    # Filter tests within oracle domain cap (len(nums) <= 15).
    valid_tests = []
    for t in REFERENCE_TESTS:
        try:
            lc45_brute_force(t["nums"])
            valid_tests.append(t)
        except GroundTruthDomainError:
            print(f"SKIP (domain): {t['nums']}")

    if not valid_tests:
        print("ERROR: no valid reference tests within oracle domain")
        return 1

    print(f"Reference tests: {len(valid_tests)}")
    print(f"Solvers: greedy_frontier, naive_greedy, dp")
    print(f"Perturbation family: suffix_reach_invariant")
    print()

    solvers = [lc45_greedy_frontier, lc45_naive_greedy, lc45_dp]

    result = lc45_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc45_brute_force,
        reference_tests=valid_tests,
    )

    print(json.dumps(result, indent=2, default=str))

    ingest = result.get("ingest", False)
    print(f"\n{'='*60}")
    print(f"VERDICT: {'INGEST' if ingest else 'REJECT'}")
    print(f"REASON: {result.get('reason', 'N/A')}")
    print(f"{'='*60}")

    return 0 if ingest else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""LC135 ingestion gate runner — plateaumorphic_invariant, 3 solvers."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc135_candidates import (
    lc135_left_pass_only,
    lc135_right_pass_only,
    lc135_two_pass,
)
from doctor.adversarial.lc135_ground_truth import lc135_brute_force, GroundTruthDomainError
from doctor.adversarial.lc135_ingestion_gate import lc135_ingestion_gate


REFERENCE_TESTS: list[dict[str, list[int]]] = [
    {"ratings": [1, 0, 2]},
    {"ratings": [1, 2, 2]},
    {"ratings": [1, 3, 2, 2, 1]},
    {"ratings": [1, 2, 3, 4, 5]},
    {"ratings": [5, 4, 3, 2, 1]},
    {"ratings": [1, 1, 1, 1]},
    {"ratings": [3, 2, 1, 0, 1, 2, 3]},
    {"ratings": [1, 2, 3, 3, 2, 1]},
    {"ratings": [2, 2, 2, 1, 1, 1]},
    {"ratings": [1, 3, 5, 3, 1, 2, 4]},
    {"ratings": [4, 3, 3, 2, 2, 1, 1]},
    {"ratings": [1, 5, 2, 4, 3, 6, 0, 2]},
]


def main() -> int:
    valid_tests = []
    for t in REFERENCE_TESTS:
        try:
            lc135_brute_force(t["ratings"])
            valid_tests.append(t)
        except GroundTruthDomainError:
            print(f"SKIP (domain): {t['ratings']}")

    if not valid_tests:
        print("ERROR: no valid reference tests within oracle domain")
        return 1

    print(f"Reference tests: {len(valid_tests)}")
    print(f"Solvers: two_pass, left_pass_only, right_pass_only")
    print(f"Perturbation family: plateaumorphic_invariant")
    print()

    solvers = [lc135_two_pass, lc135_left_pass_only, lc135_right_pass_only]

    result = lc135_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc135_brute_force,
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

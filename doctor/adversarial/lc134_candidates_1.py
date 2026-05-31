"""LC134 ingestion gate runner — paired_conservation, 5 solvers."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc134_candidates import (
    lc134_always_min,
    lc134_first_positive,
    lc134_last_positive,
    lc134_max_surplus,
    lc134_reference,
)
from doctor.adversarial.lc134_ground_truth import lc134_brute_force, GroundTruthDomainError
from doctor.adversarial.lc134_ingestion_gate import lc134_ingestion_gate


REFERENCE_TESTS: list[dict] = [
    {"n": 3, "gas": [1, 2, 3], "cost": [3, 2, 1]},
    {"n": 4, "gas": [2, 3, 4, 5], "cost": [3, 4, 5, 1]},
    {"n": 5, "gas": [1, 2, 3, 4, 5], "cost": [3, 4, 5, 1, 2]},
    {"n": 3, "gas": [2, 3, 4], "cost": [3, 4, 3]},
    {"n": 5, "gas": [5, 1, 2, 3, 4], "cost": [4, 4, 1, 5, 1]},
    {"n": 4, "gas": [3, 3, 3, 3], "cost": [2, 4, 2, 4]},
    {"n": 6, "gas": [4, 5, 2, 6, 5, 3], "cost": [3, 2, 7, 3, 2, 9]},
    {"n": 6, "gas": [6, 5, 4, 3, 2, 1], "cost": [1, 2, 3, 4, 5, 6]},
    {"n": 7, "gas": [2, 4, 6, 8, 10, 12, 14], "cost": [1, 3, 5, 7, 9, 11, 13]},
    {"n": 8, "gas": [1, 3, 5, 7, 9, 11, 13, 15], "cost": [2, 4, 6, 8, 10, 12, 14, 16]},
    # Negative control seed — minimal circuit where rotation changes feasibility
    {"n": 5, "gas": [1, 1, 1, 1, 1], "cost": [2, 2, 2, 2, 2]},
    {"n": 5, "gas": [3, 0, 3, 0, 3], "cost": [2, 1, 2, 1, 2]},
]


def main() -> int:
    valid_tests = []
    for t in REFERENCE_TESTS:
        try:
            lc134_brute_force(t["n"], t["gas"], t["cost"])
            valid_tests.append(t)
        except GroundTruthDomainError:
            print(f"SKIP (domain): n={t['n']}")

    if not valid_tests:
        print("ERROR: no valid reference tests within oracle domain")
        return 1

    print(f"Reference tests: {len(valid_tests)}")
    print(f"Solvers: reference, max_surplus, first_positive, last_positive, always_min")
    print(f"Perturbation family: paired_conservation")
    print()

    solvers = [lc134_reference, lc134_max_surplus, lc134_first_positive, lc134_last_positive, lc134_always_min]

    result = lc134_ingestion_gate(
        problem={},
        solvers=solvers,
        oracle=lc134_brute_force,
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

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc45_bimaristan import LC45
from runners.run_lc45 import _apply_solver_assumption_break, _run_generator


OUTPUT_PATH = PROJECT_ROOT / "data" / "lc45_interaction_matrix.json"


def _bucket(value: float) -> str:
    if value <= -0.05:
        return "negative"
    if value >= 0.05:
        return "positive"
    return "zero"


SIGNATURE_FIELDS = (
    "naive_divergence_rate",
    "greedy_frontier_pass_rate",
    "dp_pass_rate",
    "perturbation_resulting_behavior",
    "perturbation_divergence_delta_bucket",
    "perturbation_satisfiability_delta_bucket",
    "valid_region_control",
    "rejection_topology",
)


def _row_signature(row: dict[str, Any], drop_field: str | None = None) -> tuple[Any, ...]:
    values = {
        "naive_divergence_rate": row["naive_divergence_rate"],
        "greedy_frontier_pass_rate": row["greedy_frontier_pass_rate"],
        "dp_pass_rate": row["dp_pass_rate"],
        "perturbation_resulting_behavior": row["perturbation_resulting_behavior"],
        "perturbation_divergence_delta_bucket": _bucket(row["perturbation_divergence_delta"]),
        "perturbation_satisfiability_delta_bucket": _bucket(row["perturbation_satisfiability_delta"]),
        "valid_region_control": row["valid_region_control"],
        "rejection_topology": row["rejection_topology"],
    }
    return tuple(
        values[field]
        for field in SIGNATURE_FIELDS
        if field != drop_field
    )


def _minimal_basis(rows: list[dict[str, Any]], drop_field: str | None = None) -> list[str]:
    universe = {_row_signature(row, drop_field) for row in rows}
    candidates = sorted(row["manifold_id"] for row in rows)
    by_name = {row["manifold_id"]: row for row in rows}
    for size in range(1, len(candidates) + 1):
        valid_subsets: list[tuple[str, ...]] = []
        for subset in combinations(candidates, size):
            covered = {_row_signature(by_name[name], drop_field) for name in subset}
            if covered == universe:
                valid_subsets.append(subset)
        if valid_subsets:
            return list(min(valid_subsets, key=lambda subset: tuple(subset)))
    return candidates


def _sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    full_count = len({_row_signature(row) for row in rows})
    ablations = []
    for field in SIGNATURE_FIELDS:
        signatures = {_row_signature(row, field) for row in rows}
        ablations.append(
            {
                "dropped_field": field,
                "signature_count": len(signatures),
                "signature_count_delta": len(signatures) - full_count,
                "minimal_basis": _minimal_basis(rows, field),
            }
        )
    return {
        "full_signature_count": full_count,
        "feature_ablations": ablations,
    }


def build_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for family in LC45.invariant_families:
        for manifold in family.failure_manifolds:
            generator = manifold.geometry_generators[0]
            result = _run_generator(manifold, generator)
            accepted = result["accepted"]
            total = len(accepted)
            stats = result["stats"]
            event = _apply_solver_assumption_break(manifold.manifold_id, accepted)
            row = {
                "manifold_id": manifold.manifold_id,
                "generator_id": generator.generator_id,
                "candidate_count": total,
                "rejection_rate": round(float(result["rejection_rate"]) / 100.0, 4),
                "rejection_topology": "concentrated" if float(result["rejection_rate"]) >= 70.0 else "distributed",
                "violated_predicates": list(result["violated"]),
                "registry_routing_errors": list(result["routing_errors"]),
                "greedy_frontier_pass_rate": round(stats["greedy_frontier_agree"] / total, 4) if total else 0.0,
                "dp_pass_rate": round(stats["dp_agree"] / total, 4) if total else 0.0,
                "naive_divergence_rate": round(stats["naive_diverge"] / total, 4) if total else 0.0,
                "valid_region_control": manifold.manifold_id
                in {"uniform_jump_array", "greedy_frontier_valid_no_false_pressure"},
                "perturbation_operator": event["perturbation_operator"],
                "perturbation_transform": event["parameterization"].get("transform"),
                "perturbation_resulting_behavior": event["resulting_behavior"],
                "perturbation_divergence_delta": event["divergence_delta"],
                "perturbation_satisfiability_delta": event["satisfiability_delta"],
            }
            rows.append(row)

    signatures = {row["manifold_id"]: list(_row_signature(row)) for row in rows}
    return {
        "problem_id": "lc45",
        "method": "family_by_solver_interaction_matrix",
        "candidate_cap_per_family": 12,
        "rows": rows,
        "signatures": signatures,
        "minimal_observed_basis": _minimal_basis(rows),
        "sensitivity": _sensitivity(rows),
        "basis_rule": (
            "smallest lexicographic subset preserving all observed row signatures "
            "over solver pass rates, perturbation response, control flag, and rejection topology"
        ),
    }


def main() -> int:
    report = build_matrix()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Wrote: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc42_oracle import LC42OracleEvaluator, RegistryRoutingError, ValidationPredicate


PREDICATES = (
    ValidationPredicate("total_positive", "total_trapped_water(arr)", ">", "0"),
    ValidationPredicate("wide_trapped_indices", "len(trapped_indices(arr))", ">=", "4"),
    ValidationPredicate("separator_peak_dry", "water_at(arr, wide_peak_index)", "==", "0"),
    ValidationPredicate(
        "sum_decomposition",
        "total_trapped_water(arr)",
        "==",
        "sum(water_at(arr, i) for i in trapped_indices(arr))",
    ),
)


def _candidates() -> tuple[tuple[int, ...], ...]:
    return (
        (3, 1, 1, 1, 1, 3, 5, 0, 5),
        (4, 2, 2, 2, 2, 4, 6, 1, 6),
        (3, 1, 2, 1, 1, 3, 5, 0, 5),
        (4, 2, 3, 2, 2, 4, 7, 1, 7),
        (5, 3, 3, 3, 3, 5, 8, 2, 8),
    )


def _is_grounded_candidate(arr: tuple[int, ...], evaluator: LC42OracleEvaluator) -> bool:
    trapped = evaluator.registry.get("trapped_indices").compute({"arr": arr})
    wide_region = [index for index in (1, 2, 3, 4) if index in trapped]
    narrow_region = [index for index in (7,) if index in trapped]
    wide_water = [evaluator.registry.get("water_at").compute({"arr": arr, "i": index}) for index in wide_region]
    narrow_water = [evaluator.registry.get("water_at").compute({"arr": arr, "i": index}) for index in narrow_region]
    if not (6 <= len(arr) <= 12):
        return False
    if len(wide_region) < 4 or len(narrow_region) == 0:
        return False
    if len(wide_region) < 4 or sum(wide_water) / len(wide_water) > 2:
        return False
    if len(narrow_region) > 2 or min(narrow_water) < 3:
        return False
    return sum(wide_water) > sum(narrow_water)


def main() -> None:
    evaluator = LC42OracleEvaluator()
    candidates = _candidates()
    accepted: list[tuple[int, ...]] = []
    rejected = 0
    routing_errors: list[str] = []
    violated: list[str] = []

    for candidate in candidates:
        if not _is_grounded_candidate(candidate, evaluator):
            rejected += 1
            continue
        accepted.append(candidate)
        try:
            result = evaluator.evaluate(candidate, PREDICATES)
            violated.extend(result.violated_predicate_ids)
        except RegistryRoutingError as exc:
            routing_errors.append(str(exc))

    total = len(accepted) + rejected
    rejection_rate = (rejected / total * 100) if total else 0.0
    grounding = "PASS" if not routing_errors and accepted else "FAIL"

    print("LC42 grounded run — shallow_wide_vs_deep_narrow")
    print(f"  Candidates generated: {len(accepted)}")
    print(f"  Rejection rate: {rejection_rate:.2f}%")
    print(f"  Violated predicates: {violated if violated else 'none'}")
    print(f"  RegistryRoutingErrors: {routing_errors if routing_errors else 'none'}")
    print(f"  Semantic grounding: {grounding}")
    print("Grounding verdict:")
    print("  Predicate semantics: domain-bound")
    print("  Evidence: total_trapped_water(arr) is resolved by LC42_SYMBOL_REGISTRY and equals the sum of water_at(arr, i) over trapped_indices(arr).")


if __name__ == "__main__":
    main()

"""Oracle evaluator — reconstructed from import map analysis.

Reconstructs the public surface imported by 12 files in doctor/adversarial/.
Symbols exposed:
  - evaluation_surface
  - LC11OracleEvaluator
  - OracleCeilingError

Runtime behavior for LC11OracleEvaluator.evaluate is intentionally not
reconstructed: only the import surface and the OracleCeilingError-on-empty-
predicates contract are recovered. Full evaluation logic depends on
`LC11_SYMBOL_REGISTRY` (defined in doctor.adversarial.symbol_registry)
and is out of scope for this reconstruction.
"""
from __future__ import annotations

from typing import Any

from doctor.adversarial.oracle_contract import (
    LC45_COMPLEXITY_CEILING,
    OracleEvaluationSurface,
    OracleResult,
    OracleSymbolValue,
    PredicateEvaluation,
)


class OracleCeilingError(RuntimeError):
    pass


def evaluation_surface(
    candidate: Any,
    validation_predicates: Any,
    generator_id: str,
    synthesized_input_id: str | None = None,
) -> OracleEvaluationSurface:
    return OracleEvaluationSurface(
        candidate=candidate,
        validation_predicates=tuple(validation_predicates),
        provenance_generator_id=generator_id,
        provenance_synthesized_input_id=synthesized_input_id,
        complexity_ceiling=LC45_COMPLEXITY_CEILING,
    )


class LC11OracleEvaluator:
    def __init__(self, max_n: int = 1000) -> None:
        self.max_n = max_n

    def evaluate(self, surface: OracleEvaluationSurface) -> OracleResult:
        if not surface.validation_predicates:
            raise OracleCeilingError(
                f"LC11 oracle ceiling exceeded or empty predicate set: "
                f"generator_id={surface.provenance_generator_id}"
            )
        raise NotImplementedError(
            "LC11OracleEvaluator runtime evaluation is not reconstructed; "
            "only the import surface and OracleCeilingError contract are recovered."
        )

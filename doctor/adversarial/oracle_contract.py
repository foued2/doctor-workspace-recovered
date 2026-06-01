"""Oracle contract — reconstructed from import map analysis.

Reconstructs the public surface imported by 12 files in doctor/adversarial/.
Symbols exposed:
  - ComplexityCeiling
  - OracleSymbolValue
  - PredicateEvaluation
  - OracleResult
  - OracleEvaluationSurface
  - LC45_COMPLEXITY_CEILING
  - LC322_COMPLEXITY_CEILING

Field shapes were derived from call sites in bimaristan_schema_*.py and
lc322_oracle.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ComplexityCeiling is imported but never instantiated in any caller.
# Treated as an int alias since the per-LC ceiling constants are passed
# as kwargs to OracleEvaluationSurface(complexity_ceiling=...).
ComplexityCeiling = int

LC45_COMPLEXITY_CEILING: int = 45
LC322_COMPLEXITY_CEILING: int = 322


@dataclass(frozen=True)
class OracleSymbolValue:
    symbol_name: str
    category: Any
    value: Any


@dataclass(frozen=True)
class PredicateEvaluation:
    predicate_id: str
    predicate: Any
    passed: bool
    left: Any = None
    right: Any = None


@dataclass(frozen=True)
class OracleResult:
    input_array: tuple[Any, ...]
    oracle_dependent_values: tuple[OracleSymbolValue, ...]
    predicate_results: tuple[PredicateEvaluation, ...]
    passed: bool
    violated_predicate_ids: tuple[str, ...]
    provenance_generator_id: str
    provenance_synthesized_input_id: str | None = None


@dataclass(frozen=True)
class OracleEvaluationSurface:
    candidate: Any
    validation_predicates: tuple[Any, ...]
    provenance_generator_id: str
    provenance_synthesized_input_id: str | None
    complexity_ceiling: ComplexityCeiling

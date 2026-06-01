"""LC322 symbol registry — reconstructed from import map analysis.

Reconstructs the public surface imported by 11+ files in
`doctor/adversarial/`. Symbols exposed:
  - LC322_SYMBOL_REGISTRY

The registry is dereferenced by the `LC322OracleEvaluator` implementation
copied into `doctor/adversarial/lc322_oracle.py:46-202` (and by the
sibling `bimaristan_schema_21.py`). Required shape (inferred from
call sites):

    registry.entries          -> iterable of entry objects
    registry.names            -> set[str]
    registry.get(name)        -> entry | None
    entry.name                -> str
    entry.category            -> SymbolCategory
    entry.input_signature     -> tuple[str, ...]
    entry.compute(context)    -> Any
    entry.ambiguity           -> Any (commonly None)

Shape is otherwise opaque. Runtime bodies are no-ops; the
98/98 baseline is the only runtime contract enforced.
"""
from __future__ import annotations

from typing import Any

from doctor.adversarial.symbol_registry import SymbolCategory


class _LC322Entry:
    def __init__(
        self,
        name: str,
        category: SymbolCategory,
        input_signature: tuple[str, ...] = (),
        compute: Any = None,
        ambiguity: Any = None,
    ) -> None:
        self.name = name
        self.category = category
        self.input_signature = input_signature
        self._compute = compute
        self.ambiguity = ambiguity

    def compute(self, context: dict) -> Any:
        if self._compute is not None:
            return self._compute(context)
        return None


class _LC322Registry:
    def __init__(self) -> None:
        self.problem_id: str = ""
        self.entries: tuple[_LC322Entry, ...] = ()
        self.names: set[str] = set()

    def get(self, name: str) -> _LC322Entry | None:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None


LC322_SYMBOL_REGISTRY: _LC322Registry = _LC322Registry()

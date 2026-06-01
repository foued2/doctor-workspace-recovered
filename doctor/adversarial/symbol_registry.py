"""doctor.adversarial.symbol_registry — stub.

Reconstructed from import map analysis. `SymbolCategory` and
`LC11_SYMBOL_REGISTRY` are imported in this file's own test
functions and by `bimaristan_schema.py:14`, `bimaristan_schema_21.py:19`,
and the rest of the bimaristan_schema_NN.py siblings. The only
SymbolCategory value used in the workspace is `ORACLE_DEPENDENT`
(38 read-sites: `entry.category is SymbolCategory.ORACLE_DEPENDENT`).

The `LC11_SYMBOL_REGISTRY` shape is inferred from the test at
`symbol_registry.py:103-105` and from the LC45 sibling at
`doctor.adversarial.lc45_symbol_registry.py`:
  - `.problem_id` (str)
  - `.entries` (tuple of entry objects)
  - `.names` (set of str)
  - `.get(name) -> entry | None`
where entries have `.name`, `.category`, `.ambiguity`, `.compute(ctx)`,
`.input_signature`.

Runtime bodies are no-ops. 98/98 baseline is the only runtime
contract enforced.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class SymbolCategory(Enum):
    ORACLE_DEPENDENT = "oracle_dependent"


class _LC11Entry:
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


class _LC11Registry:
    def __init__(self) -> None:
        self.problem_id: str = ""
        self.entries: tuple[_LC11Entry, ...] = ()
        self.names: set[str] = set()

    def get(self, name: str) -> _LC11Entry | None:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None


LC11_SYMBOL_REGISTRY: _LC11Registry = _LC11Registry()

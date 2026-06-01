"""doctor.adversarial.lc45_symbol_registry — stub.

Reconstructed from import map analysis. `LC45_SYMBOL_REGISTRY` is
used in `bimaristan_schema_28.py` as a `registry=` kwarg and stored
on the evaluator. The instance is then used as `.entries`,
`.names`, and `.get(name)` (where entries have `.compute(ctx)` and
`.input_signature`). Same shape as the LC11 registry pattern.

Runtime bodies are no-ops. 98/98 baseline is the only runtime
contract enforced.
"""
from __future__ import annotations

from typing import Any, Iterator


class _LC45Entry:
    def __init__(self, name: str, input_signature: tuple[str, ...] = (), compute: Any = None) -> None:
        self.name = name
        self.input_signature = input_signature
        self._compute = compute

    def compute(self, context: dict) -> Any:
        if self._compute is not None:
            return self._compute(context)
        return None


class _LC45Registry:
    def __init__(self) -> None:
        self.entries: tuple[_LC45Entry, ...] = ()
        self.names: set[str] = set()

    def get(self, name: str) -> _LC45Entry | None:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None


LC45_SYMBOL_REGISTRY: _LC45Registry = _LC45Registry()

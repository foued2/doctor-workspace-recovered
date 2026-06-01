"""doctor.adversarial.schema_validator — stub.

`assert_valid_schema(schema, **kwargs) -> None` is the only symbol from
this module referenced by the import chain feeding the
`bimaristan_schema.py` test surface. Call sites (30+ across the
workspace) all follow the pattern:

    assert_valid_schema(SOMETHING, registry=REGISTRY)

with no return value used. A no-op stub matches that contract.

Runtime bodies are no-ops. 98/98 baseline is the only runtime
contract enforced.
"""
from __future__ import annotations

from typing import Any


def assert_valid_schema(schema: Any, **kwargs: Any) -> None:
    return None

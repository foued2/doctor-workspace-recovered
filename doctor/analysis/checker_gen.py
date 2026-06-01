from __future__ import annotations

from typing import Any, Callable, Dict, Optional


def generate_checker(spec: Any) -> Callable[[Any], bool]:
    spec_type = getattr(spec, "spec_type", None) or (spec.get("spec_type") if isinstance(spec, dict) else None)
    problem_id = getattr(spec, "problem_id", None) or (spec.get("problem_id") if isinstance(spec, dict) else None)

    if spec_type == "unverifiable":
        return lambda output: True

    def checker(output: Any) -> bool:
        if output is None:
            return False
        if isinstance(output, str) and output.strip() == "":
            return False
        return True

    return checker

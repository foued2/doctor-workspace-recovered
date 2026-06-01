from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SpecBundle:
    problem_id: str
    spec_type: str
    confidence: float
    source: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    hypothesis: Optional[str] = None


@dataclass
class SpecHypothesis:
    problem_id: Optional[str] = None
    spec_type: str = "unknown"
    confidence: float = 0.0
    source: str = "unknown"
    inferred_input_schema: Dict[str, str] = field(default_factory=dict)
    inferred_output_shape: str = "unknown"
    completeness_score: float = 0.0
    canonical_form: Optional[str] = None


def infer_spec(
    problem_id_or_statement: str,
    source_code: Optional[str] = None,
    execution_traces: Optional[List[Dict[str, Any]]] = None,
) -> SpecHypothesis:
    statement = problem_id_or_statement
    traces = execution_traces or []

    input_schema: Dict[str, str] = {}
    output_shape = "unknown"

    if source_code:
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.args.args:
                    for arg in node.args.args:
                        name = arg.arg
                        if name in ("nums", "arr", "array", "height", "grid", "board"):
                            input_schema[name] = "list"
                        elif name in ("s", "text", "string"):
                            input_schema[name] = "string"
                        elif name in ("n", "num", "number", "amount"):
                            input_schema[name] = "int"
                        elif name in ("target", "k"):
                            input_schema[name] = "int"
                        elif name in ("head",):
                            input_schema[name] = "linked_list"
                        elif name in ("root",):
                            input_schema[name] = "tree"
                        elif name in ("coins",):
                            input_schema[name] = "list"
                        elif name in ("word",):
                            input_schema[name] = "string"
                        else:
                            input_schema[name] = "any"
                    break  # only process the first (outermost) function
        except SyntaxError:
            pass

    statement_lower = (statement or "").lower()

    if not input_schema:
        if "array" in statement_lower or "list" in statement_lower or "nums" in statement_lower:
            input_schema = {"nums": "list"}
        elif "string" in statement_lower:
            input_schema = {"s": "string"}
        elif "integer" in statement_lower or "number" in statement_lower:
            input_schema = {"n": "int"}

    if output_shape == "unknown" and "return" in (statement or "").lower():
        if "array" in statement_lower or "list" in statement_lower:
            output_shape = "list"
        elif "integer" in statement_lower or "number" in statement_lower:
            output_shape = "int"
        elif "boolean" in statement_lower or "true or false" in statement_lower:
            output_shape = "bool"
        elif "character" in statement_lower or "string" in statement_lower:
            output_shape = "string"

    return SpecHypothesis(
        problem_id=statement,
        spec_type="inferred",
        confidence=0.5 if input_schema else 0.2,
        source="inference",
        inferred_input_schema=input_schema,
        inferred_output_shape=output_shape,
        completeness_score=0.5 if input_schema else 0.2,
        canonical_form=None,
    )


def infer_spec_bundle(
    problem_id: str,
    test_cases: Optional[List[Dict[str, Any]]] = None,
) -> List[SpecBundle]:
    tc = test_cases or []
    confidence = min(1.0, 0.5 + 0.1 * len(tc)) if tc else 0.0
    source = "test_cases" if tc else "no_test_cases"
    return [
        SpecBundle(
            problem_id=problem_id,
            spec_type="test_based" if tc else "unverifiable",
            confidence=confidence,
            source=source,
            test_cases=tc,
        )
    ]

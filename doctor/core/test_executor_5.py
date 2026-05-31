"""
Sandbox worker for Doctor execution.

This module runs in a child Python process. It receives a JSON payload on
stdin and writes exactly one JSON response to stdout.
"""
from __future__ import annotations

import contextlib
import json
import os
import sys
import traceback
from typing import Any


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def _jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, tuple):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, list):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if hasattr(obj, "val") and hasattr(obj, "next"):
        vals = []
        seen = set()
        current = obj
        while current is not None:
            ident = id(current)
            if ident in seen:
                vals.append("<cycle>")
                break
            seen.add(ident)
            vals.append(_jsonable(getattr(current, "val", None)))
            current = getattr(current, "next", None)
        return vals
    return repr(obj)


def _failure_response(message: str, *, total: int = 0) -> dict:
    return {
        "ok": False,
        "error": message,
        "total": total,
        "passed": 0,
        "results": [],
        "traces": [],
    }


def _worker_input(problem_id: str, raw_input: Any) -> tuple:
    if problem_id == "merge_two_sorted_lists":
        from doctor.core.test_executor import make_list

        return tuple(make_list(item) if isinstance(item, list) else item for item in raw_input)
    return tuple(raw_input)


def _run_payload(payload: dict) -> dict:
    from doctor.core.execution_trace import run_test_with_trace
    from doctor.core.test_executor import (
        _results_equal,
        _verify_with_validator,
        validate_arrangement,
    )
    from doctor.normalize.solution_normalizer import extract_function, normalize_solution

    code = payload.get("code", "")
    problem_id = payload.get("problem_id")
    tests = payload.get("tests", [])
    timeout_seconds = payload.get("per_test_timeout_seconds", 30)

    if not isinstance(code, str) or not code.strip():
        return _failure_response("No solution code provided", total=len(tests))
    if not isinstance(problem_id, str) or not problem_id:
        return _failure_response("No problem_id provided", total=len(tests))
    if not isinstance(tests, list):
        return _failure_response("Invalid tests payload")

    normalized = normalize_solution(code)
    if normalized is None:
        return _failure_response("Failed to normalize solution code", total=len(tests))

    func = extract_function(normalized, problem_id)
    if func is None:
        return _failure_response("Failed to parse/execute solution code", total=len(tests))

    results = []
    traces = []

    for test in tests:
        label = test.get("label", "")
        test_input = _worker_input(problem_id, test.get("input", []))
        expected = test.get("expected")
        validation_type = test.get("validation_type")

        trace = run_test_with_trace(
            func,
            test_input,
            expected,
            timeout_seconds=timeout_seconds,
        )
        trace = _jsonable(trace)
        traces.append(trace)

        if validation_type == "arrangement_validator":
            passed = False if trace.get("error") is not None else validate_arrangement(
                trace.get("output"), test_input
            )
            validator_result = passed
            validator_kind = "arrangement_validator"
        else:
            passed = False if trace.get("error") is not None else _results_equal(
                trace.get("output"), expected
            )
            validator_result, validator_kind = _verify_with_validator(
                problem_id, trace.get("output"), test_input
            )

        error = ""
        if trace.get("error"):
            lines = str(trace["error"]).splitlines()
            error = lines[-1] if lines else str(trace["error"])

        results.append({
            "label": label,
            "passed": bool(passed),
            "got": _jsonable(trace.get("output")),
            "expected": _jsonable(expected),
            "error": error,
            "validator_passed": _jsonable(validator_result),
            "validator_kind": validator_kind,
        })

    return {
        "ok": True,
        "error": "",
        "total": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "results": results,
        "traces": traces,
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception as exc:
        print(json.dumps(_failure_response(f"Invalid JSON payload: {exc}")))
        return 2

    try:
        with contextlib.redirect_stdout(sys.stderr):
            response = _run_payload(payload)
    except BaseException:
        response = _failure_response(traceback.format_exc(), total=len(payload.get("tests", [])))

    sys.stdout.write(json.dumps(_jsonable(response), ensure_ascii=True))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

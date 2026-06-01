from __future__ import annotations

from typing import Any


def generate_checker(spec: Any) -> str:
    """Return a Python code string defining checker_entry(solution_output, input_args).

    The code is embedded in a sandbox by _run_checker in agreement.py.
    checker_entry must return True (PASS), False (FAIL), or raise (INCONCLUSIVE).
    """
    spec_type = getattr(spec, "spec_type", None) or (spec.get("spec_type") if isinstance(spec, dict) else None)
    test_cases = getattr(spec, "test_cases", None) or []

    if spec_type == "unverifiable":
        return _UNVERIFIABLE_CHECKER

    if test_cases:
        expected = test_cases[0].get("expected") if isinstance(test_cases[0], dict) else None
        if expected is not None:
            mode = _infer_mode(expected)
            return _EXPECTED_CHECKER.format(expected=repr(expected), mode=repr(mode))

    return _BASIC_CHECKER


def _infer_mode(expected: Any) -> str:
    if isinstance(expected, (list, tuple, set, frozenset)):
        return "sorted"
    return "scalar"


_UNVERIFIABLE_CHECKER = """\
def checker_entry(solution_output, input_args):
    return True
"""

_EXPECTED_CHECKER = """\
def checker_entry(solution_output, input_args):
    EXPECTED = {expected}
    MODE = {mode}
    actual = solution_output
    expected = EXPECTED
    try:
        if MODE == "scalar":
            verdict = "PASS" if actual == expected else "FAIL"
        elif MODE == "sorted":
            try:
                verdict = "PASS" if sorted(actual) == sorted(expected) else "FAIL"
            except Exception:
                verdict = "INCONCLUSIVE"
        elif MODE == "set":
            try:
                verdict = "PASS" if set(actual) == set(expected) else "FAIL"
            except Exception:
                verdict = "INCONCLUSIVE"
        else:
            verdict = "INCONCLUSIVE"
    except Exception:
        verdict = "INCONCLUSIVE"
    if verdict == "PASS":
        return True
    if verdict == "FAIL":
        return False
    raise RuntimeError("checker inconclusive")
"""

_BASIC_CHECKER = """\
def checker_entry(solution_output, input_args):
    if solution_output is None:
        return False
    if isinstance(solution_output, str) and solution_output.strip() == "":
        return False
    return True
"""

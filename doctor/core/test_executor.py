from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class TestCase:
    input: Tuple[Any, ...]
    expected: Any
    label: str = ""


@dataclass
class TestResult:
    label: str
    passed: bool
    expected: Any
    got: Any
    error: Optional[str] = None


@dataclass
class ExecutionReport:
    verdict: str
    total: int
    passed: int
    pass_rate: float
    results: List[TestResult]
    traces: List[Dict[str, Any]]
    evidence_score: float
    error: Optional[str] = None


def _results_equal(got: Any, expected: Any) -> bool:
    if got is None and expected is None:
        return True
    if got is None or expected is None:
        return False
    if isinstance(expected, (list, tuple)) and isinstance(got, (list, tuple)):
        return list(got) == list(expected)
    if isinstance(expected, set) and isinstance(got, set):
        return got == expected
    return got == expected


def _extract_function(code: str, problem_id: str) -> Optional[Callable]:
    namespace: Dict[str, Any] = {}
    try:
        exec(code, namespace)
    except SyntaxError:
        return None

    function_names = [
        name for name, obj in namespace.items()
        if callable(obj) and not name.startswith("_")
    ]

    if len(function_names) == 1:
        return namespace[function_names[0]]

    for name in ["solve", "solution", "twoSum", "maxArea", "trap", "lengthOfLongestSubstring", "isValid"]:
        if name in namespace and callable(namespace[name]):
            return namespace[name]

    if function_names:
        return namespace[function_names[0]]

    return None


def _load_test_cases(problem_id: str) -> List[TestCase]:
    from doctor.core.test_suites import TEST_SUITES as _TS
    return _TS.get(problem_id, [])


TEST_SUITES: Dict[str, List[TestCase]] = {}


def _init_test_suites():
    global TEST_SUITES
    if not TEST_SUITES:
        from doctor.core.test_suites import TEST_SUITES as _TS
        TEST_SUITES.update(_TS)


class TestExecutor:
    def verify(self, problem_id: str, code: str) -> ExecutionReport:
        func = _extract_function(code, problem_id)
        if func is None:
            return ExecutionReport(
                verdict="error",
                total=0,
                passed=0,
                pass_rate=0.0,
                results=[],
                traces=[],
                evidence_score=0.0,
                error="syntax_error",
            )

        test_cases = _load_test_cases(problem_id)
        if not test_cases:
            return ExecutionReport(
                verdict="unverifiable",
                total=0,
                passed=0,
                pass_rate=0.0,
                results=[],
                traces=[],
                evidence_score=0.0,
                error="no_test_cases",
            )

        results: List[TestResult] = []
        traces: List[Dict[str, Any]] = []
        passed_count = 0

        for tc in test_cases:
            label = tc.label or f"test_{len(results)}"
            try:
                got = func(*tc.input)
                ok = _results_equal(got, tc.expected)
            except Exception as e:
                got = None
                ok = False
                traces.append({"error": str(e), "error_type": type(e).__name__})

            results.append(TestResult(label=label, passed=ok, expected=tc.expected, got=got))
            if ok:
                passed_count += 1

        total = len(test_cases)
        pass_rate = passed_count / total if total > 0 else 0.0

        if passed_count == total:
            verdict = "correct"
        elif passed_count == 0:
            verdict = "incorrect"
        else:
            verdict = "partial"

        return ExecutionReport(
            verdict=verdict,
            total=total,
            passed=passed_count,
            pass_rate=pass_rate,
            results=results,
            traces=traces,
            evidence_score=pass_rate,
            error=None,
        )

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

from doctor.analysis.checker_gen import generate_checker
from doctor.analysis.spec_inferrer import SpecBundle
from doctor.core.sandbox_runner import run_solution_in_sandbox


@dataclass
class AgreementResult:
    verdict: str          # "PASS" | "FAIL" | "INCONCLUSIVE"
    agreeing_specs: float # confidence-weighted sum of specs that returned PASS
    total_specs: int      # len(spec_bundles)
    dominant_source: str  # source field of highest-confidence agreeing spec, or "none"


def compute_agreement_multi(
    spec_bundles: list[SpecBundle],
    test_results: list[tuple[Any, Any]],
) -> AgreementResult:
    """
    Run agreement check against all test outputs.

    Priority: FAIL > INCONCLUSIVE > PASS.
    A None solution output is INCONCLUSIVE for that test, not FAIL.
    """
    # Probe output variance check — if all outputs identical, zero evidential value
    non_none_outputs = [o for o, _ in test_results if o is not None]
    if non_none_outputs and len(set(map(str, non_none_outputs))) == 1:
        return AgreementResult(
            verdict="INCONCLUSIVE",
            agreeing_specs=0.0,
            total_specs=len(spec_bundles),
            dominant_source="none",
        )

    checker_results: list[tuple[SpecBundle, str]] = []

    for solution_output, input_args in test_results:
        if solution_output is None:
            for spec in spec_bundles:
                checker_results.append((spec, "INCONCLUSIVE"))
            continue

        for spec in spec_bundles:
            checker_code = generate_checker(spec)
            if checker_code is None:
                checker_results.append((spec, "INCONCLUSIVE"))
                continue
            checker_results.append((spec, _run_checker(checker_code, solution_output, input_args)))

    agreeing = [(spec, result) for spec, result in checker_results if result == "PASS"]
    agreeing_specs = sum(spec.confidence for spec, result in agreeing)
    dominant_source = max(agreeing, key=lambda x: x[0].confidence)[0].source if agreeing else "none"

    fail_count = sum(spec.confidence for spec, r in checker_results if r == "FAIL")
    pass_count = sum(spec.confidence for spec, r in checker_results if r == "PASS")

    if fail_count > pass_count:
        verdict = "FAIL"
    elif pass_count > fail_count:
        verdict = "PASS"
    else:
        verdict = "INCONCLUSIVE"

    return AgreementResult(
        verdict=verdict,
        agreeing_specs=agreeing_specs,
        total_specs=len(spec_bundles),
        dominant_source=dominant_source,
    )





def _run_checker(checker_code: str, solution_output: Any, input_args: Any) -> str:
    """Run checker in sandbox and return PASS/FAIL/INCONCLUSIVE."""
    import subprocess
    import sys
    import tempfile
    import os

    sandbox_code = f"""
{checker_code}

try:
    result = checker_entry({solution_output!r}, {input_args!r})
    if result is True:
        print("PASS")
    elif result is False:
        print("FAIL")
    else:
        print("INCONCLUSIVE")
except Exception:
    print("INCONCLUSIVE")
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sandbox_code)
        temp_file = f.name

    try:
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout.strip()
        if output in ("PASS", "FAIL", "INCONCLUSIVE"):
            return output
        return "INCONCLUSIVE"
    except subprocess.TimeoutExpired:
        return "INCONCLUSIVE"
    except Exception:
        return "INCONCLUSIVE"
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass


def compute_agreement(
    spec_bundles: list[SpecBundle],
    solution_output: Any,
    input_args: Any,
) -> AgreementResult:
    """Deprecated wrapper — delegates to compute_agreement_multi with single test."""
    return compute_agreement_multi(spec_bundles, [(solution_output, input_args)])


@dataclass
class _CheckerTestCase:
    input: tuple
    expected: Any
    label: str = ""
    validation_type: str | None = None


def _sandbox_checker_code(checker_code: str) -> str | None:
    literals = _checker_literals(checker_code)
    if literals is None:
        return None
    expected, mode = literals
    return f"""\
def checker_entry(solution_output, input_args):
    EXPECTED = {expected!r}
    MODE = {mode!r}
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


def _checker_literals(checker_code: str) -> tuple[Any, str] | None:
    try:
        tree = ast.parse(checker_code)
    except SyntaxError:
        return None

    values: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in {"EXPECTED", "MODE"}:
            try:
                values[target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                return None

    mode = values.get("MODE")
    if "EXPECTED" not in values or not isinstance(mode, str):
        return None
    return values["EXPECTED"], mode

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generators.bimaristan_adaptive_fg_vp import adaptive_taxonomy_matcher
from generators.bimaristan_fake_generalizers_vp import (
    count_balanced_only,
    depth_parity_tracker,
    greedy_local_matcher,
    prefix_valid_threshold,
)
from generators.bimaristan_generator_vp import (
    VP_FIXED_SUITE,
    canonicalize_input,
    fixed_suite_inputs,
    generate_adversarial_vp,
    generate_candidates_by_family,
)
from doctor.adversarial.registry_audit import _memorization_solution
from doctor.core.sandbox_runner import run_solution_in_sandbox
from doctor.core.test_executor import TestCase


PROBLEM_ID = VP_FIXED_SUITE
PROBLEM_NAME = "Valid Parentheses"


def _load_registry_entry(problem_id: str) -> dict[str, Any]:
    registry_path = PROJECT_ROOT / "doctor" / "registry" / "problem_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    try:
        return registry[problem_id]
    except KeyError as exc:
        raise SystemExit(f"Problem {problem_id} not found in registry") from exc


def _to_test_cases(raw_cases: list[dict[str, Any]]) -> list[TestCase]:
    return [
        TestCase(
            input=tuple(case.get("input", [])),
            expected=case.get("expected"),
            label=case.get("label", ""),
            validation_type=case.get("validation_type"),
        )
        for case in raw_cases
    ]


def _run(code: str, tests: list[TestCase]):
    return run_solution_in_sandbox(
        code=code,
        problem_id=PROBLEM_ID,
        tests=tests,
        timeout_seconds=10,
        per_test_timeout_seconds=2,
    )


def _generated_variant_tests(reference_code: str, survivors: list[str]) -> list[TestCase]:
    probe_cases = [
        TestCase(input=(value,), expected=None, label=f"generated_{index}")
        for index, value in enumerate(survivors, start=1)
    ]
    oracle_probe = _run(reference_code, probe_cases)
    if not oracle_probe.ok:
        raise SystemExit(f"Reference oracle probe failed: {oracle_probe.error}")

    generated = []
    for test, result in zip(probe_cases, oracle_probe.results):
        generated.append(TestCase(input=test.input, expected=result.get("got"), label=test.label))
    return generated


def _family_survivors(fixed_cases: list[dict[str, Any]]) -> dict[str, list[str]]:
    seen = {canonicalize_input(value) for value in fixed_suite_inputs(fixed_cases)}
    by_family: dict[str, list[str]] = {}

    for family, candidates in generate_candidates_by_family().items():
        by_family[family] = []
        for candidate in candidates:
            key = canonicalize_input(candidate)
            if key in seen:
                continue
            seen.add(key)
            by_family[family].append(candidate)
    return by_family


def _fake_code(function) -> str:
    import inspect

    source = inspect.getsource(function)
    return f"{source}\n\ndef isValid(s):\n    return {function.__name__}(s)\n"


def _tests_for_values(values: list[str], expected_by_input: dict[str, Any]) -> list[TestCase]:
    return [
        TestCase(input=(value,), expected=expected_by_input[value], label=f"family_{index}")
        for index, value in enumerate(values, start=1)
    ]


def _score(code: str, tests: list[TestCase]) -> tuple[int, int]:
    run = _run(code, tests)
    if not run.ok:
        raise SystemExit(f"Candidate execution failed: {run.error}")
    return run.passed, run.total


def _score_text(score: tuple[int, int]) -> str:
    return f"{score[0]}/{score[1]}"


def _line(label: str, passed: int, total: int) -> str:
    rate = passed / total if total else 0.0
    return f"  {label:<19}: {passed}/{total}  ({rate:.2f})"


def main() -> int:
    entry = _load_registry_entry(PROBLEM_ID)
    fixed_cases = entry.get("execution", {}).get("test_cases", [])
    fixed_tests = _to_test_cases(fixed_cases)
    reference_code = entry.get("spec", {}).get("reference_solution", "")
    memorizer_code = _memorization_solution(fixed_cases)
    generated_output = generate_adversarial_vp(fixed_cases)
    generated_tests = _generated_variant_tests(reference_code, generated_output.survivors)
    expected_by_input = {test.input[0]: test.expected for test in generated_tests}
    family_survivors = _family_survivors(fixed_cases)
    fake_codes = {
        "FG1": _fake_code(count_balanced_only),
        "FG2": _fake_code(greedy_local_matcher),
        "FG3": _fake_code(prefix_valid_threshold),
        "FG4": _fake_code(adaptive_taxonomy_matcher),
        "FG5": _fake_code(depth_parity_tracker),
    }
    solver_codes = {
        "reference": reference_code,
        "FG1": fake_codes["FG1"],
        "FG2": fake_codes["FG2"],
        "FG3": fake_codes["FG3"],
        "FG4": fake_codes["FG4"],
        "FG5": fake_codes["FG5"],
        "memorizer": memorizer_code,
    }

    fixed_reference = _run(reference_code, fixed_tests)
    fixed_memorizer = _run(memorizer_code, fixed_tests)
    generated_reference = _run(reference_code, generated_tests)
    generated_fg1 = _run(fake_codes["FG1"], generated_tests)
    generated_fg2 = _run(fake_codes["FG2"], generated_tests)
    generated_fg3 = _run(fake_codes["FG3"], generated_tests)
    generated_fg4 = _run(fake_codes["FG4"], generated_tests)
    generated_fg5 = _run(fake_codes["FG5"], generated_tests)
    generated_memorizer = _run(memorizer_code, generated_tests)

    if not all(
        run.ok
        for run in (
            fixed_reference,
            fixed_memorizer,
            generated_reference,
            generated_fg1,
            generated_fg2,
            generated_fg3,
            generated_fg4,
            generated_fg5,
            generated_memorizer,
        )
    ):
        failures = [
            run.error
            for run in (
                fixed_reference,
                fixed_memorizer,
                generated_reference,
                generated_fg1,
                generated_fg2,
                generated_fg3,
                generated_fg4,
                generated_fg5,
                generated_memorizer,
            )
            if not run.ok
        ]
        raise SystemExit("Demo execution failed: " + "; ".join(failures))

    print("=== BIMARISTAN Minimal Discrimination Demo ===")
    print(f"Problem: {PROBLEM_NAME} (pid {PROBLEM_ID})")
    print()
    print(f"Fixed suite ({len(fixed_tests)} tests):")
    print(_line("reference_solution", fixed_reference.passed, fixed_reference.total))
    print(_line("memorizer", fixed_memorizer.passed, fixed_memorizer.total))
    print("  --> Fixed suite cannot distinguish genuine solver from memorizer")
    print()
    print("Generator diagnostics:")
    print(f"  total generated   : {generated_output.diagnostics.total_generated}")
    print(f"  rediscovered      : {generated_output.diagnostics.rediscovered}")
    print(f"  unique adversarial: {generated_output.diagnostics.unique_adversarial}")
    print()
    print(f"Adversarial evaluation ({len(generated_tests)} unseen inputs):")
    print(_line("reference_solution", generated_reference.passed, generated_reference.total))
    print(_line("FG1 count_balance", generated_fg1.passed, generated_fg1.total))
    print(_line("FG2 local_match", generated_fg2.passed, generated_fg2.total))
    print(_line("FG3 prefix_only", generated_fg3.passed, generated_fg3.total))
    print(_line("FG4 adaptive", generated_fg4.passed, generated_fg4.total))
    print(_line("FG5 depth_parity", generated_fg5.passed, generated_fg5.total))
    print(_line("memorizer", generated_memorizer.passed, generated_memorizer.total))
    print("  --> Dynamic generation exposes explicit memorization")
    print()
    print("Per-family breakdown:")
    print(
        f"{'Family':<22} {'real_solver':>11} {'FG1':>7} {'FG2':>7} "
        f"{'FG3':>7} {'FG4':>7} {'FG5':>7} {'memorizer':>10}"
    )
    total_scores = {name: [0, 0] for name in solver_codes}
    for family, values in family_survivors.items():
        tests = _tests_for_values(values, expected_by_input)
        scores = {name: _score(code, tests) for name, code in solver_codes.items()}
        for key, score in scores.items():
            total_scores[key][0] += score[0]
            total_scores[key][1] += score[1]
        print(
            f"{family:<22} "
            f"{_score_text(scores['reference']):>11} "
            f"{_score_text(scores['FG1']):>7} "
            f"{_score_text(scores['FG2']):>7} "
            f"{_score_text(scores['FG3']):>7} "
            f"{_score_text(scores['FG4']):>7} "
            f"{_score_text(scores['FG5']):>7} "
            f"{_score_text(scores['memorizer']):>10}"
        )
    print(
        f"{'TOTAL':<22} "
        f"{_score_text(tuple(total_scores['reference'])):>11} "
        f"{_score_text(tuple(total_scores['FG1'])):>7} "
        f"{_score_text(tuple(total_scores['FG2'])):>7} "
        f"{_score_text(tuple(total_scores['FG3'])):>7} "
        f"{_score_text(tuple(total_scores['FG4'])):>7} "
        f"{_score_text(tuple(total_scores['FG5'])):>7} "
        f"{_score_text(tuple(total_scores['memorizer'])):>10}"
    )
    print()
    print("Conclusion: adversarial generation has strictly more discriminatory power")
    print("than fixed suites against lookup-style memorization.")
    print("This is a necessary condition for a working oracle. Not sufficient.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

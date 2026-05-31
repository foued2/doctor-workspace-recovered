#!/usr/bin/env python3
"""
Doctor Problem Ingestion CLI

Usage:
    python -m doctor.ingest --file problem.json
    python -m doctor.ingest --interactive
"""
from __future__ import annotations

import argparse
import json
import sys
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def normalize_output(val):
    """Recursively sort lists for order-insensitive comparison."""
    if isinstance(val, list):
        try:
            return sorted(normalize_output(v) for v in val)
        except TypeError:
            return val
    return val


from doctor.registry.problem_registry import (
    REGISTRY_PATH,
    STATE_SEED,
    add_problem,
    get_all_keys,
    get_problem,
    is_order_sensitive,
    reload,
    validate_determinism,
    validate_entry,
    validate_structural_diversity,
)


def _run_dry_run(entry: dict) -> tuple[bool, float, str]:
    """Run reference_solution against test cases. Returns (success, pass_rate, message)."""
    ref_code = entry.get("spec", {}).get("reference_solution")
    if not ref_code:
        return False, 0.0, "no reference_solution provided"

    display_name = entry.get("spec", {}).get("display_name", "")
    suite_key = entry.get("spec", {}).get("problem_id", "")
    test_cases = entry.get("execution", {}).get("test_cases", [])

    if not test_cases:
        return False, 0.0, "no test cases"

    try:
        from doctor.normalize.solution_normalizer import (
            extract_function,
            normalize_solution,
        )
        normalized = normalize_solution(ref_code)
        func = extract_function(normalized)
        if func is None:
            return False, 0.0, "could not extract function from reference_solution"
    except Exception as e:
        logger.warning(f"reference_solution crashed: {e}")
        return False, 0.0, f"reference_solution crashed: {traceback.format_exc(limit=3)}"

    try:
        from doctor.core.execution_trace import run_test_with_trace
        from doctor.core.test_executor import _results_equal

        passed = 0
        failed_labels = []
        for tc in test_cases:
            try:
                trace = run_test_with_trace(func, tuple(tc["input"]), tc["expected"])
                if trace.get("error") is not None:
                    failed_labels.append(tc["label"])
                elif _results_equal(trace.get("output"), tc["expected"]):
                    passed += 1
                else:
                    failed_labels.append(tc["label"])
            except Exception as e:
                logger.warning(f"test case '{tc.get('label')}' threw exception: {e}")
                failed_labels.append(tc["label"])

        total = len(test_cases)
        rate = passed / total if total > 0 else 0.0

        if rate == 1.0:
            return True, rate, f"E={rate:.3f}, e={rate:.3f}"
        else:
            pct = f"{passed}/{total}"
            failed = ", ".join(failed_labels[:5])
            if len(failed_labels) > 5:
                failed += f" (+{len(failed_labels) - 5} more)"
            return False, rate, f"E={rate:.3f}, {pct} passed — failed: {failed}"
    except Exception as e:
        logger.warning(f"dry-run error: {e}")
        return False, 0.0, f"dry-run error: {traceback.format_exc(limit=3)}"


def _run_deterministic_check(entry: dict) -> tuple[bool, str]:
    """
    Runtime determinism check: run reference_solution twice on each test case.
    Reject if outputs differ between runs.
    """
    ref_code = entry.get("spec", {}).get("reference_solution")
    if not ref_code:
        return False, "REJECT: no reference_solution provided"

    test_cases = entry.get("execution", {}).get("test_cases", [])
    if not test_cases:
        return True, "skipped (no test cases)"

    try:
        from doctor.normalize.solution_normalizer import extract_function, normalize_solution
        from doctor.core.execution_trace import run_test_with_trace

        normalized = normalize_solution(ref_code)
        func = extract_function(normalized)
        if func is None:
            return False, "REJECT: could not extract function from reference_solution"

        for tc in test_cases:
            inp = tuple(tc["input"])
            try:
                t1 = run_test_with_trace(func, inp, tc["expected"])
                t2 = run_test_with_trace(func, inp, tc["expected"])
                out1, out2 = t1.get("output"), t2.get("output")
                if normalize_output(out1) != normalize_output(out2):
                    return False, f"REJECT: non-deterministic output on '{tc['label']}' — run1={out1} vs run2={out2}"
            except Exception as e:
                logger.warning(f"determinism check test case '{tc.get('label')}' error: {e}")
                return False, f"REJECT: determinism check error on '{tc.get('label')}' — {e}"

        return True, "passed"
    except Exception as e:
        logger.warning(f"determinism check inconclusive: {e}")
        return False, f"REJECT: determinism check inconclusive — {traceback.format_exc(limit=2)}"


def _apply_perturbation_check(entry: dict) -> tuple[bool, str]:
    """
    Detect overfitting via perturbation — independent of structural diversity.

    Two checks:
    1. Output diversity: if all test cases produce identical outputs, solution is
       likely a constant-returning stub.
    2. Order perturbation: if order_sensitive=False in spec, reorder first two args
       and verify output stays the same. If it changes → REJECT.

    Returns (pass, message). A False return means REJECT ingestion.
    """
    ref_code = entry.get("spec", {}).get("reference_solution")
    if not ref_code:
        return False, "REJECT: no reference_solution provided"

    test_cases = entry.get("execution", {}).get("test_cases", [])
    if len(test_cases) < 2:
        return False, "REJECT: need at least 2 test cases for perturbation check"

    try:
        from doctor.normalize.solution_normalizer import extract_function, normalize_solution
        from doctor.core.execution_trace import run_test_with_trace
        from doctor.core.test_executor import _results_equal

        normalized = normalize_solution(ref_code)
        func = extract_function(normalized)
        if func is None:
            return False, "REJECT: could not extract function from reference_solution"

        outputs: list = []
        for tc in test_cases:
            trace = run_test_with_trace(func, tuple(tc["input"]), tc["expected"])
            outputs.append(trace.get("output"))

        output_strs = [str(o) for o in outputs]
        if len(set(output_strs)) == 1:
            return False, f"REJECT: all test cases return identical output — solution may be hardcoded"

        order_insensitive_tcs = [
            tc for tc in test_cases
            if isinstance(tc.get("input"), list) and len(tc["input"]) >= 2
            and len({type(x).__name__ for x in tc["input"]}) == 1
        ]

        if order_insensitive_tcs:
            suite_key = entry.get("spec", {}).get("problem_id", "")
            sensitive = is_order_sensitive(suite_key)
            if not sensitive:
                tc = order_insensitive_tcs[0]
                inp = tc["input"]
                reordered = list(inp)
                reordered[0], reordered[1] = reordered[1], reordered[0]
                t_orig = run_test_with_trace(func, tuple(inp), tc["expected"])
                t_pert = run_test_with_trace(func, tuple(reordered), tc["expected"])
                if t_orig.get("error") is None and t_pert.get("error") is None:
                    if not _results_equal(t_orig.get("output"), t_pert.get("output")):
                        return False, "REJECT: order perturbation changes output — solution is order-sensitive but spec says order_insensitive=False"

        return True, "passed"

    except Exception as e:
        logger.warning(f"perturbation check inconclusive: {e}")
        return False, f"REJECT: perturbation check inconclusive — {traceback.format_exc(limit=2)}"


def ingest(entry: dict, dry_run_only: bool = False) -> tuple[bool, List[str], List[str], str]:
    """
    Ingest a problem entry into the registry.

    Pipeline:
        1. Schema validation
        2. Structural diversity check
        3. Determinism check
        4. Dry-run (reference_solution must pass 100%)
        5. Perturbation check
        6. [Write to registry if all pass]

    Returns: (success, errors, warnings, message)
    """
    errors: List[str] = []
    warnings: List[str] = []
    suite_key = entry.get("spec", {}).get("problem_id", "")

    def accept_without_execution_gates(message: str) -> tuple[bool, List[str], List[str], str]:
        if dry_run_only:
            return True, errors, warnings, message

        entry["provenance"] = "pre-gate"
        write_errors = add_problem(suite_key, entry, state=STATE_SEED)
        if write_errors:
            errors.extend(write_errors)
            return False, errors, warnings, f"write failed: {write_errors}"

        return True, errors, warnings, message

    if not suite_key:
        errors.append("spec.problem_id: required")
        return False, errors, warnings, "missing problem_id"

    existing = get_problem(suite_key)
    if existing:
        errors.append(f"problem '{suite_key}' already exists — remove or rename first")
        return False, errors, warnings, f"duplicate: {suite_key}"

    schema_errors = validate_entry(entry)
    if schema_errors:
        errors.extend(schema_errors)
        return False, errors, warnings, f"schema validation failed ({len(schema_errors)} error(s))"

    if entry.get("execution", {}).get("executable", True) is False:
        # Still validate schema fields, but skip dry-run, perturbation, diversity gates.
        return accept_without_execution_gates("executable=false — execution gates skipped")

    # Skip execution gates for non-verifiable entries
    if not entry.get("verifiable", True):
        return accept_without_execution_gates("non-verifiable entry accepted — execution gates skipped")

    exec_entry = entry.get("execution", {})
    div_errors = validate_structural_diversity(exec_entry)
    if div_errors:
        errors.extend(div_errors)
        return False, errors, warnings, f"structural diversity check failed"

    det_errors = validate_determinism(exec_entry.get("test_cases", []))
    if det_errors:
        errors.extend(det_errors)
        return False, errors, warnings, f"determinism check failed"

    ok, rate, msg = _run_dry_run(entry)
    if not ok:
        errors.append(f"dry-run failed: {msg}")
        return False, errors, warnings, f"dry-run E={rate:.3f} (must be 1.0)"
    warnings.append(f"dry-run: {msg}")

    det_ok, det_msg = _run_deterministic_check(entry)
    if not det_ok:
        errors.append(f"determinism: {det_msg}")
        return False, errors, warnings, "determinism check failed"
    warnings.append(f"determinism: {det_msg}")

    pert_ok, pert_msg = _apply_perturbation_check(entry)
    if not pert_ok:
        errors.append(f"perturbation check: {pert_msg}")
        return False, errors, warnings, "perturbation check failed"
    warnings.append(f"perturbation: {pert_msg}")

    from doctor.ingest.mutation_gate import run_mutation_gate

    mut_result = run_mutation_gate(entry)
    if mut_result.verdict == "FAIL":
        errors.append(f"mutation-kill gate: {mut_result.reason}")
        return False, errors, warnings, f"REJECTED: {mut_result.reason}"
    if mut_result.verdict == "INCONCLUSIVE":
        warnings.append(f"mutation-kill gate inconclusive: {mut_result.reason}")
    else:
        parts = [
            f"responsiveness={mut_result.responsiveness_kill_rate:.2f} "
            f"({mut_result.responsiveness_killed}/{mut_result.responsiveness_total})",
        ]
        if mut_result.stability_total and mut_result.stability_total > 0:
            parts.append(
                f"stability={mut_result.stability_kill_rate:.2f} "
                f"({mut_result.stability_killed}/{mut_result.stability_total})"
            )
        warnings.append(f"mutation-kill: {', '.join(parts)}")

    total = len(get_all_keys())
    count = total + 1

    from doctor.ingest.mutation_gate import RESPONSIVENESS_THRESHOLD, STABILITY_THRESHOLD

    entry["provenance"] = {
        "gate": "compositional_mutation_kill",
        "responsiveness_threshold": RESPONSIVENESS_THRESHOLD,
        "stability_threshold": STABILITY_THRESHOLD,
        "perturbation_classification": "perturbation_classification.md",
        "state_machine": "SEED -> CANDIDATE -> VERIFIED",
    }

    if dry_run_only:
        return True, errors, warnings, f"dry-run PASSED — would register '{suite_key}' ({count} problems total)"

    write_errors = add_problem(suite_key, entry)
    if write_errors:
        errors.extend(write_errors)
        return False, errors, warnings, f"write failed: {write_errors}"

    return True, errors, warnings, f"Registered: {suite_key} ({count} problems total)"


def ingest_file(path: str, dry_run_only: bool = False) -> int:
    """Load a JSON problem file and ingest it. Returns exit code."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}")
        return 1
    except Exception as e:
        print(f"Error: Could not read {path}: {e}")
        return 1

    ok, errors, warnings, msg = ingest(entry, dry_run_only=dry_run_only)

    print(msg)
    if warnings:
        for w in warnings:
            print(f"  warning: {w}")
    if errors:
        for e in errors:
            print(f"  error: {e}")

    return 0 if ok else 1


def _prompt_field(prompt: str, default: Optional[str] = None, required: bool = True) -> str:
    val = input(f"{prompt}: ").strip()
    if not val and default:
        val = default
    if required and not val:
        raise ValueError(f"{prompt} is required")
    return val


def _prompt_list(prompt: str) -> List[str]:
    val = input(f"{prompt} (comma-separated): ").strip()
    if not val:
        return []
    return [x.strip() for x in val.split(",")]


def _prompt_test_cases() -> List[dict]:
    cases = []
    n = input("Number of test cases (min 3): ").strip()
    try:
        n = int(n) if n else 3
    except ValueError:
        n = 3

    for i in range(n):
        print(f"\n  Test case {i+1}:")
        raw_input = input("    input (JSON array): ").strip()
        raw_expected = input("    expected (JSON value): ").strip()
        label = input("    label: ").strip() or f"case_{i+1}"
        source = input("    source (manual/generated/boundary) [manual]: ").strip() or "manual"

        try:
            inp = json.loads(raw_input) if raw_input else []
            expected = json.loads(raw_expected) if raw_expected else None
        except json.JSONDecodeError as e:
            print(f"  Skipping case {i+1} — invalid JSON: {e}")
            continue

        cases.append({
            "input": inp,
            "expected": expected,
            "label": label,
            "source": source,
        })

    return cases


def ingest_interactive(dry_run_only: bool = False) -> int:
    """Prompt for all fields interactively."""
    print("\n=== Doctor Problem Ingestion (interactive) ===\n")

    try:
        entry = {
            "spec": {
                "problem_id": _prompt_field("problem_id (snake_case, e.g. 'two_sum')"),
                "display_name": _prompt_field("display_name (e.g. 'Two Sum')"),
                "constraints": {},
                "difficulty": _prompt_field("difficulty (easy/medium/hard) [easy]", default="easy", required=False),
                "tags": _prompt_list("tags"),
                "notes": input("notes (optional): ").strip() or None,
            },
            "execution": {
                "test_cases": _prompt_test_cases(),
            },
            "normalization": {
                "function_names": _prompt_list("function_names (e.g. twoSum, solve)"),
            },
        }
    except (ValueError, EOFError) as e:
        print(f"\nAborted: {e}")
        return 1

    ref_code = ""
    print("\nreference_solution — paste Python code (end with empty line + Ctrl+D / Ctrl+Z):")
    lines = []
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass
    ref_code = "\n".join(lines)
    if ref_code.strip():
        entry["spec"]["reference_solution"] = ref_code

    print()
    ok, errors, warnings, msg = ingest(entry, dry_run_only=dry_run_only)

    print(msg)
    if warnings:
        for w in warnings:
            print(f"  warning: {w}")
    if errors:
        for e in errors:
            print(f"  error: {e}")

    return 0 if ok else 1


def _cmd_list():
    reload()
    problems = get_all_keys()
    print(f"Registered problems ({len(problems)}):")
    for k in sorted(problems):
        p = get_problem(k)
        spec = p.get("spec", {})
        ref = bool(spec.get("reference_solution"))
        order = spec.get("order_sensitive", True)
        diff = spec.get("difficulty", "?")
        print(f"  [{diff:6}] {k}{' (ref)' if ref else ''}{' [order_sensitive]' if order else ' [order_insensitive]'}")
    return 0


def _cmd_check(problem_id: str):
    reload()
    entry = get_problem(problem_id)
    if not entry:
        print(f"Problem '{problem_id}' not found in registry.")
        return 1
    spec = entry.get("spec", {})
    exec_ = entry.get("execution", {})
    norm = entry.get("normalization", {})
    print(f"=== {spec.get('display_name', problem_id)} ({problem_id}) ===")
    print(f"difficulty: {spec.get('difficulty', '?')}")
    print(f"reference_solution: {'yes' if spec.get('reference_solution') else 'NO'}")
    print(f"order_sensitive: {spec.get('order_sensitive', True)}")
    known_issue = spec.get("known_issue")
    if known_issue:
        print(f"KNOWN ISSUE: {known_issue}")
    print(f"test_cases: {len(exec_.get('test_cases', []))}")
    print(f"function_names: {norm.get('function_names', [])}")
    print()
    schema_errors = validate_entry(entry)
    if schema_errors:
        print("SCHEMA ERRORS:")
        for e in schema_errors:
            print(f"  {e}")
    else:
        print("schema: OK")
    div_errors = validate_structural_diversity(exec_)
    if div_errors:
        print("STRUCTURAL DIVERSITY ERRORS:")
        for e in div_errors:
            print(f"  {e}")
    else:
        print("structural diversity: OK")
    if spec.get("reference_solution"):
        ok, rate, msg = _run_dry_run(entry)
        print(f"dry-run: {msg}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Doctor problem ingestion CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to problem JSON file")
    group.add_argument("--interactive", action="store_true", help="Interactive mode")
    group.add_argument("--list", action="store_true", help="List all registered problems")
    group.add_argument("--check", type=str, metavar="PROBLEM_ID", help="Check an existing problem (read-only validation)")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing to registry")

    args = parser.parse_args()

    if args.list:
        return _cmd_list()
    elif args.check:
        return _cmd_check(args.check)
    elif args.file:
        return ingest_file(args.file, dry_run_only=args.dry_run)
    elif args.interactive:
        return ingest_interactive(dry_run_only=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

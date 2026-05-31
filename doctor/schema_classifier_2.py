#!/usr/bin/env python3
"""
Direction 2: Pipeline

Wires problem extraction, checker generation, and candidate execution.
Task 4: extract_schema + build_checker only.
Task 5: execute_candidate added.
"""
import sys
import io
import json
import os
from typing import Any

from experimental.dynamic.extractor import extract_problem
from experimental.dynamic.checker_generator import generate_checker
from experimental.dynamic.candidate_executor import run_candidate
from doctor.schema_classifier import classify_schema


def extract_schema(problem_statement: str) -> dict | None:
    """Extract schema from a problem statement. Returns schema dict or None."""
    return extract_problem(problem_statement)


def build_checker(schema: dict) -> str | None:
    """Generate and validate a checker from a schema. Returns checker source or None."""
    return generate_checker(schema)


def _derive_function_name(problem_id: str) -> list[str]:
    """Derive function names from problem_id."""
    if not problem_id:
        return []
    snake = problem_id.lower().strip()
    camel = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(snake.split("_")))
    return [camel, snake]


def _format_output_as_string(output, output_type: str) -> str | None:
    """Format an output value as the string expected by the test case format."""
    if output is None:
        return None
    if output_type == "integer" and isinstance(output, int):
        return str(output)
    if output_type == "boolean" and isinstance(output, bool):
        return str(output).lower()
    if output_type == "string" and isinstance(output, str):
        return output
    if output_type == "list" and isinstance(output, list):
        return " ".join(str(x) for x in output)
    return str(output)


def _generate_test_cases_with_agreement(
    schema: dict,
    solver_a_source: str,
    solver_b_source: str,
    existing_cases: list[dict],
    count: int = 6,
) -> tuple[list[dict], dict]:
    """Generate test cases using solver agreement for ground truth.

    Two independently generated solvers must agree on the expected output
    before a generated test case is accepted.

    Returns (test_cases, agreement_stats).
    """
    import random
    import string
    import copy

    input_structure = schema.get("input_structure", {})
    output_format = schema.get("output_format", {})
    per_case_fields = input_structure.get("per_case_format", [])
    output_type = output_format.get("type", "").lower()

    solver_a = None
    solver_b = None
    try:
        ns_a, ns_b = {}, {}
        exec(solver_a_source, ns_a, ns_a)
        exec(solver_b_source, ns_b, ns_b)
        solver_a = ns_a.get("solve")
        solver_b = ns_b.get("solve")
    except Exception:
        pass

    if solver_a is None or solver_b is None:
        return [], {"total_attempts": 0, "agreed": 0, "disagreed": 0, "traces": []}

    from experimental.dynamic.solver_agreement import compute_ground_truth

    generated = []
    seen_inputs = set()
    agreement_stats = {"total_attempts": 0, "agreed": 0, "disagreed": 0, "traces": []}

    for attempt in range(count * 20):
        if len(generated) >= count:
            break

        try:
            case_input = {}
            size_field = None

            for field in per_case_fields:
                fname = field.get("name", "")
                ftype = field.get("type", "").lower()
                if "n" == fname.lower() or "size" == fname.lower() or fname.lower().endswith("_n"):
                    size_field = fname

            size_value = random.randint(2, 6)

            for field in per_case_fields:
                fname = field.get("name", "")
                ftype = field.get("type", "").lower()

                if fname == size_field:
                    case_input[fname] = size_value
                elif "list" in ftype or "array" in ftype:
                    n = size_value if size_field else 5
                    if "list of list" in ftype or "list of lists" in ftype:
                        case_input[fname] = [[random.randint(0, n-1), random.randint(0, n-1)] for _ in range(random.randint(0, min(n, 5)))]
                    else:
                        case_input[fname] = [random.randint(1, 10) for _ in range(n)]
                elif "string" in ftype:
                    char_count = random.randint(3, 8)
                    case_input[fname] = ''.join(random.choices(string.ascii_lowercase, k=char_count))
                elif "int" in ftype or "integer" in ftype:
                    if "target" in fname.lower():
                        case_input[fname] = random.randint(1, 15)
                    else:
                        case_input[fname] = random.randint(1, 10)
                elif "float" in ftype:
                    case_input[fname] = round(random.uniform(0.1, 10.0), 2)
                else:
                    continue

            has_empty = False
            for fname, fval in case_input.items():
                if fval is None or fval == "" or (isinstance(fval, list) and len(fval) == 0):
                    has_empty = True
                    break
            if has_empty:
                continue

            input_signature = json.dumps(case_input, sort_keys=True)
            if input_signature in seen_inputs:
                continue

            agreement_stats["total_attempts"] += 1
            expected, trace = compute_ground_truth(solver_a, solver_b, case_input)
            agreement_stats["traces"].append(trace)

            if trace["agreed"]:
                agreement_stats["agreed"] += 1
            else:
                agreement_stats["disagreed"] += 1
                continue

            output_str = _format_output_as_string(expected, output_type)
            if output_str is None:
                continue

            raw_parts = []
            for field in per_case_fields:
                fname = field.get("name", "")
                if fname not in case_input:
                    continue
                v = case_input[fname]
                if isinstance(v, int):
                    raw_parts.append(str(v))
                elif isinstance(v, list):
                    if v and isinstance(v[0], list):
                        raw_parts.append(json.dumps(v))
                    else:
                        raw_parts.append(" ".join(str(x) for x in v))
                elif isinstance(v, str):
                    raw_parts.append(v)
                elif isinstance(v, float):
                    raw_parts.append(str(v))
                elif isinstance(v, bool):
                    raw_parts.append(str(v).lower())
            raw_input = "\n".join(raw_parts)

            if not raw_input.strip():
                continue

            seen_inputs.add(input_signature)
            test_case = {
                "input": raw_input,
                "expected": output_str,
                "label": f"generated_{len(generated)}",
                "source": "generated"
            }
            generated.append(test_case)

        except Exception:
            continue

    return generated, agreement_stats


def _verify_solvers_pass_all_tests(
    schema: dict,
    checker_source: str,
    solver_a_source: str,
    solver_b_source: str,
    test_cases: list[dict],
) -> tuple[bool, str]:
    """Verify at least one solver passes ALL test cases against the checker.

    This is the hard gate: a problem cannot be promoted to the registry
    until at least one solver demonstrates correct execution across every
    test case (extracted + generated).

    Returns (passed, reason).
    """
    import copy
    from experimental.dynamic.candidate_executor import (
        _parse_sample_case,
        _extract_function,
        _execute_with_timeout,
    )

    check_func = _extract_function(checker_source, "check")
    if check_func is None:
        return False, "checker_compilation_failed"

    solvers = []
    for idx, source in enumerate([solver_a_source, solver_b_source], 1):
        fn = _extract_function(source, "solve")
        if fn is not None:
            solvers.append((f"solver_{idx}", fn))

    if not solvers:
        return False, "no_solver_compiled"

    for solver_name, solver_fn in solvers:
        all_passed = True
        fail_reason = ""
        for tc in test_cases:
            raw_input = tc.get("input", "")
            raw_expected = tc.get("expected", "")

            parsed = _parse_sample_case(schema, raw_input, raw_expected)
            if parsed is None:
                all_passed = False
                fail_reason = f"parse_failed on '{raw_input[:30]}'"
                break

            input_args, _ = parsed
            try:
                actual, timed_out = _execute_with_timeout(solver_fn, (input_args,), timeout_seconds=5)
            except Exception as e:
                all_passed = False
                fail_reason = f"{solver_name} raised: {e}"
                break

            if timed_out:
                all_passed = False
                fail_reason = f"{solver_name} timeout"
                break

            accepted, reason = check_func(copy.deepcopy(input_args), actual)
            if not accepted:
                all_passed = False
                fail_reason = f"{solver_name} checker_rejected on '{raw_input[:30]}': {reason}"
                break

        if all_passed:
            return True, f"{solver_name}_passed_all_{len(test_cases)}_cases"
        else:
            print(f"  execution_gate: {solver_name} failed — {fail_reason}")

    return False, f"no_solver_passed_all_cases"


def promote_to_registry(
    schema: dict,
    checker_source: str,
    validation_output: str,
    solver_a_source: str = None,
    solver_b_source: str = None,
) -> dict | None:
    """
    Build a candidate registry entry from validated schema and checker.
    Returns the entry dict or None on failure.
    """
    try:
        problem_id = schema.get("problem_id")
        if not problem_id:
            print(f"promote_to_registry: no problem_id")
            return None

        sample_cases = schema.get("sample_cases", [])
        if not sample_cases:
            print(f"promote_to_registry: no sample_cases")
            return None

        test_cases = []
        for i, case in enumerate(sample_cases):
            test_cases.append({
                "input": case.get("input", ""),
                "expected": case.get("output", ""),
                "label": f"sample_{i}",
                "source": "extracted"
            })

        function_names = _derive_function_name(problem_id)
        agreement_stats = None

        if solver_a_source and solver_b_source:
            generated_cases, agreement_stats = _generate_test_cases_with_agreement(
                schema, solver_a_source, solver_b_source, sample_cases, count=6
            )
        else:
            print(f"promote_to_registry[{problem_id}]: no solver pair generated — cannot produce validated test cases")
            return None

        if not generated_cases:
            print(f"promote_to_registry[{problem_id}]: zero generated cases from agreement gate")
            return None

        test_cases.extend(generated_cases)

        test_cases_to_verify = test_cases
        passed, gate_reason = _verify_solvers_pass_all_tests(
            schema, checker_source, solver_a_source, solver_b_source, test_cases_to_verify
        )
        if not passed:
            print(f"promote_to_registry[{problem_id}]: execution gate failed — {gate_reason}")
            return None

        result = {"entry": None, "path": None, "ingested": False}
        result["execution_gate"] = {"passed": True, "reason": gate_reason}
        result["agreement_stats"] = agreement_stats

        ingestion_source = "dynamic_agreement"

        entry = {
            "spec": {
                "display_name": schema.get("problem_id", ""),
                "description": schema.get("validation_logic", ""),
                "constraints": {},
                "difficulty": "unknown",
                "tags": [],
                "problem_id": problem_id,
                "reference_solution": None,
            },
            "execution": {
                "test_cases": test_cases,
            },
            "normalization": {
                "function_names": function_names,
            },
            "ingestion_source": ingestion_source,
        }
        result["entry"] = entry

        scratch_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scratch")
        os.makedirs(scratch_dir, exist_ok=True)
        candidate_path = os.path.join(scratch_dir, f"candidate_{problem_id}.json")
        with open(candidate_path, "w") as f:
            json.dump(entry, f, indent=2)
        result["path"] = candidate_path

        from doctor.registry.problem_registry import ingest_candidate
        key, ingest_errors = ingest_candidate(entry)
        if ingest_errors:
            for err in ingest_errors:
                print(f"ingest_candidate[{problem_id}]: {err}")
        else:
            result["ingested"] = True
            result["registry_key"] = key
            print(f"ingest_candidate[{problem_id}]: ingested with source='{ingestion_source}'")

        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"promote_to_registry exception: {e}")
        return None


def execute_candidate(candidate_code: str, pipeline_result: dict) -> dict:
    """
    Execute a candidate solution using the pipeline result.
    Merges execution result into pipeline output contract.
    """
    schema = pipeline_result.get("schema")
    checker_source = pipeline_result.get("checker_source")
    candidate_entry = pipeline_result.get("candidate_entry")

    if schema is None or checker_source is None:
        pipeline_result["verdict"] = "incorrect"
        pipeline_result["trust"] = "unverified"
        pipeline_result["risk"] = "HIGH"
        pipeline_result["failure_mode"] = pipeline_result.get("failure_mode", "missing_schema_or_checker")
        return pipeline_result

    generated_cases = []
    if candidate_entry:
        for tc in candidate_entry.get("execution", {}).get("test_cases", []):
            if tc.get("source") == "generated":
                generated_cases.append(tc)

    provenance = "hand_verified"
    if candidate_entry and "ingestion_source" in candidate_entry:
        provenance = candidate_entry["ingestion_source"]

    exec_result = run_candidate(candidate_code, checker_source, schema, test_cases=generated_cases, provenance=provenance)

    pipeline_result["verdict"] = exec_result.get("verdict", "incorrect")
    pipeline_result["trust"] = exec_result.get("trust", "unverified")
    pipeline_result["risk"] = exec_result.get("risk", "HIGH")
    pipeline_result["failure_mode"] = exec_result.get("failure_mode")
    pipeline_result["E"] = exec_result.get("E")
    pipeline_result["e"] = exec_result.get("e")
    pipeline_result["tests_passed"] = exec_result.get("tests_passed", 0)
    pipeline_result["tests_total"] = exec_result.get("tests_total", 0)
    pipeline_result["sample_results"] = exec_result.get("sample_results")
    pipeline_result["generated_results"] = exec_result.get("generated_results")

    if exec_result.get("details"):
        pipeline_result["details"] = exec_result["details"]
    pipeline_result["provenance"] = exec_result.get("provenance", provenance)

    return pipeline_result


def run_pipeline(problem_statement: str, candidate_code: str = None) -> dict:
    """
    Run the Direction 2 pipeline: extract schema, generate checker, optionally execute.
    
    If candidate_code is provided, also executes the candidate against sample cases.
    Returns a result dict with full output contract.
    """
    result = {
        "evaluation_mode": "provisional",
        "checker_confidence": None,
        "verdict": "pending_execution",
        "trust": None,
        "risk": "MEDIUM",
        "failure_mode": None,
        "provenance": None,
        "ingested": False,
        "registry_key": None,
        "execution_gate": None,
        "warning": (
            "This verdict is not authoritative. "
            "Doctor generated its own checker for this problem. "
            "Results may be incorrect if the checker is flawed."
        ),
        "schema": None,
        "checker_source": None,
        "details": [],
        "classification": None,
        "candidate_entry": None,
        "candidate_path": None,
        "solver_agreement": None,
    }

    # Step 0: Classify the problem statement
    classification = classify_schema(problem_statement)
    result["classification"] = classification

    if not classification.get("domain") and not classification.get("paradigm") and not classification.get("confidence"):
        err = classification.get("error", "unknown")
        print(f"classification_failed: empty output — {err}")
        result["failure_mode"] = "classification_failed"
        result["risk"] = "HIGH"
        return result

    # If confidence is low, reject before extraction
    if classification.get("confidence") == "low":
        result["failure_mode"] = "unclassifiable"
        result["risk"] = "HIGH"
        return result

    schema = extract_schema(problem_statement)
    if schema is None:
        result["failure_mode"] = "extraction_failed"
        return result
    result["schema"] = schema

    from experimental.dynamic.oracle_feasibility import assess_oracle_feasibility, OracleFeasibility
    oracle_gate = assess_oracle_feasibility(schema)
    result["oracle_feasibility"] = oracle_gate.value

    if oracle_gate == OracleFeasibility.SOLVER_REQUIRED:
        result["failure_mode"] = "oracle_infeasible"
        result["risk"] = "HIGH"
        print(f"oracle_feasibility_gate: solver_required — halting pipeline")
        return result

    if oracle_gate == OracleFeasibility.UNKNOWN:
        result["risk"] = "MEDIUM"
        print(f"oracle_feasibility_gate: unknown — proceeding with low confidence")

    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        checker_source = build_checker(schema)
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()

    if checker_source is None:
        failure_mode = "extraction_failed"
        for line in output.splitlines():
            if line.startswith("failure_mode:"):
                failure_mode = line.split(":", 1)[1].strip()
                break
        result["failure_mode"] = failure_mode
        return result

    result["checker_source"] = checker_source
    result["checker_confidence"] = "MEDIUM"

    from experimental.dynamic.solver_agreement import generate_solver_pair
    solver_pair = generate_solver_pair(schema)
    if solver_pair is None:
        print("Warning: solver agreement generation failed, falling back to sample-only test cases")
        solver_a, solver_b = None, None
    else:
        solver_a, solver_b = solver_pair
        print(f"Solver agreement: generated solvers A and B successfully")

    promoted = promote_to_registry(schema, checker_source, output, solver_a, solver_b)
    if promoted:
        result["candidate_entry"] = promoted["entry"]
        result["candidate_path"] = promoted["path"]
        result["verdict"] = "candidate_ready"
        result["ingested"] = promoted.get("ingested", False)
        result["registry_key"] = promoted.get("registry_key")
        if "agreement_stats" in promoted:
            result["solver_agreement"] = promoted["agreement_stats"]
        if "execution_gate" in promoted:
            result["execution_gate"] = promoted["execution_gate"]

    if candidate_code:
        result = execute_candidate(candidate_code, result)

    return result
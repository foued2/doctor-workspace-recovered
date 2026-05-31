#!/usr/bin/env python3
"""
Direction 2: Candidate Executor

Executes a candidate solution against sample cases using a generated checker.
Task 5: Self-contained in doctor/dynamic/, no registry imports.
"""
import copy
import json
import re
import threading
from typing import Any, Callable, Optional


class _TokenCursor:
    """Token cursor that preserves line boundaries for mixed scalar/list inputs."""
    def __init__(self, text: str):
        self.lines = [re.split(r"\s+", line.strip()) for line in text.splitlines() if line.strip()]
        self.line_index = 0
        self.token_index = 0

    def consume_token(self) -> Optional[str]:
        while self.line_index < len(self.lines):
            tokens = self.lines[self.line_index]
            if self.token_index < len(tokens):
                token = tokens[self.token_index]
                self.token_index += 1
                return token
            self.line_index += 1
            self.token_index = 0
        return None

    def consume_tokens(self, count: int) -> Optional[list[str]]:
        values = []
        for _ in range(count):
            token = self.consume_token()
            if token is None:
                return None
            values.append(token)
        return values

    def consume_line_tokens(self) -> Optional[list[str]]:
        while self.line_index < len(self.lines):
            tokens = self.lines[self.line_index]
            if self.token_index < len(tokens):
                remaining = tokens[self.token_index:]
                self.line_index += 1
                self.token_index = 0
                return remaining
            self.line_index += 1
            self.token_index = 0
        return None

    def at_end(self) -> bool:
        while self.line_index < len(self.lines):
            if self.token_index < len(self.lines[self.line_index]):
                return False
            self.line_index += 1
            self.token_index = 0
        return True


def _coerce_scalar_token(token: str, field_type: str) -> Any:
    field_type = field_type.lower()
    if "int" in field_type or "integer" in field_type:
        try:
            return int(token)
        except ValueError:
            return None
    if "bool" in field_type or "boolean" in field_type:
        lowered = token.lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
        return None
    if "float" in field_type:
        try:
            return float(token)
        except ValueError:
            return None
    return token


def _coerce_list_tokens(tokens: list[str], field_type: str) -> list[Any]:
    field_type = field_type.lower()
    if "int" in field_type or "integer" in field_type:
        values = []
        for token in tokens:
            try:
                values.append(int(token))
            except ValueError:
                return tokens
        return values
    return tokens


def _infer_list_length(name: str, field_type: str, description: str, current_case: dict) -> int | None:
    text = f"{name} {field_type} {description}".lower()
    patterns = [
        r"list of ([a-z_][a-z0-9_]*)",
        r"array of ([a-z_][a-z0-9_]*)",
        r"([a-z_][a-z0-9_]*) integers",
        r"([a-z_][a-z0-9_]*) values",
        r"length ([a-z_][a-z0-9_]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        var_name = match.group(1)
        if var_name in current_case and isinstance(current_case[var_name], int):
            return current_case[var_name]
    return None


def _parse_case_from_cursor(cursor: _TokenCursor, fields: list[dict]) -> dict | None:
    case: dict[str, Any] = {}
    for field in fields:
        name = field.get("name")
        field_type = (field.get("type") or "").lower()
        description = field.get("description", "")
        if not name:
            return None

        if "list" in field_type or "array" in field_type:
            length = _infer_list_length(name, field_type, description, case)
            if length is not None:
                tokens = cursor.consume_tokens(length)
            else:
                tokens = cursor.consume_line_tokens()
            if not tokens:
                return None
            if "list of list" in field_type or "list of lists" in field_type:
                combined = " ".join(tokens).strip()
                if combined.startswith("["):
                    try:
                        case[name] = json.loads(combined)
                        continue
                    except json.JSONDecodeError:
                        pass
            case[name] = _coerce_list_tokens(tokens, field_type)
        else:
            token = cursor.consume_token()
            if token is None:
                return None
            scalar = _coerce_scalar_token(token, field_type)
            if scalar is None and "string" not in field_type:
                return None
            case[name] = token if scalar is None else scalar
    return case


def _parse_sample_case(schema: dict, raw_input: str, raw_output: str) -> tuple[dict, Any] | None:
    """Parse raw sample case into canonical input/output representation."""
    input_structure = schema.get("input_structure", {})
    per_case_format = input_structure.get("per_case_format", [])
    if not per_case_format:
        return None

    cursor = _TokenCursor(raw_input)
    if input_structure.get("type") == "multi_case":
        test_case_var = input_structure.get("test_case_count_var")
        if not test_case_var:
            return None
        test_count_token = cursor.consume_token()
        if test_count_token is None:
            return None
        try:
            test_count = int(test_count_token)
        except ValueError:
            return None

        cases = []
        for _ in range(test_count):
            case = _parse_case_from_cursor(cursor, per_case_format)
            if case is None:
                return None
            cases.append(case)

        if not cursor.at_end():
            return None

        outputs = _parse_multi_case_output(schema, raw_output, cases)
        if outputs is None:
            return None
        return {test_case_var: test_count, "cases": cases}, outputs

    case = _parse_case_from_cursor(cursor, per_case_format)
    if case is None or not cursor.at_end():
        return None
    output = _parse_single_case_output(schema.get("output_format", {}), raw_output, case)
    if output is None:
        return None
    return case, output


def _parse_single_case_output(output_format: dict, raw_output: str, case_input: dict) -> Any:
    output_type = (output_format.get("type") or "string").lower()
    trimmed = raw_output.strip()
    if not trimmed:
        return None

    if output_type == "string":
        return trimmed
    if output_type == "integer":
        tokens = _split_tokens(trimmed)
        if not tokens:
            return None
        try:
            return int(tokens[0])
        except ValueError:
            return None
    if output_type == "boolean":
        tokens = _split_tokens(trimmed)
        if not tokens:
            return None
        return _coerce_scalar_token(tokens[0], "boolean")
    if output_type == "list":
        if trimmed.startswith("["):
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError:
                pass
        tokens = _split_tokens(trimmed)
        return _coerce_list_tokens(tokens, "list")
    return trimmed


def _parse_multi_case_output(schema: dict, raw_output: str, cases: list[dict]) -> list[Any] | None:
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    if len(lines) != len(cases):
        return None

    output_format = schema.get("output_format", {})
    outputs = []
    for line, case in zip(lines, cases):
        value = _parse_case_output_value(output_format, line, case)
        if value is None:
            return None
        outputs.append(value)
    return outputs


def _parse_case_output_value(output_format: dict, line: str, case_input: dict) -> Any:
    output_type = (output_format.get("type") or "string").lower()
    if output_type == "string":
        return line.strip()
    if output_type == "integer":
        try:
            return int(_split_tokens(line)[0])
        except (IndexError, ValueError):
            return None
    if output_type == "boolean":
        tokens = _split_tokens(line)
        if not tokens:
            return None
        return _coerce_scalar_token(tokens[0], "boolean")
    if output_type == "list":
        trimmed_line = line.strip()
        if trimmed_line.startswith("["):
            try:
                return json.loads(trimmed_line)
            except json.JSONDecodeError:
                pass
        tokens = _split_tokens(line)
        if not tokens:
            return []
        return _coerce_list_tokens(tokens, "list")
    return line.strip()


def _split_tokens(text: str) -> list[str]:
    return [part for part in re.split(r"[\s,]+", text.strip()) if part]


def _extract_function(source: str, func_name: str) -> Callable | None:
    """Extract a function from source code."""
    try:
        namespace: dict[str, Any] = {}
        compiled = compile(source, "<candidate>", "exec")
        exec(compiled, namespace, namespace)
        func = namespace.get(func_name)
        if callable(func):
            return func
    except Exception:
        return None
    return None


def _execute_with_timeout(func: Callable, args: tuple, timeout_seconds: int = 5) -> tuple[Any, bool]:
    """Execute function with timeout. Uses threading for cross-platform support."""
    result = None
    timed_out = False
    exception_holder = [None]

    def target():
        try:
            nonlocal result
            result = func(*args)
        except Exception as e:
            exception_holder[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout_seconds)

    if t.is_alive():
        timed_out = True
    elif exception_holder[0] is not None:
        raise exception_holder[0]

    return result, timed_out


def _compute_evidence_score(tests_passed: int, tests_total: int) -> float:
    """Compute evidence score from sample case execution.
    
    Sample cases from schema are structurally weak (3-5 cases typically).
    Formula: min(tests_total / 10, 1.0) * 0.6 + pass_ratio * 0.4
    """
    if tests_total == 0:
        return 0.0
    volume_factor = min(tests_total / 10.0, 1.0)
    pass_ratio = tests_passed / tests_total
    return volume_factor * 0.6 + pass_ratio * 0.4


def _execute_cases(
    candidate_func: Callable,
    check_func: Callable,
    schema: dict,
    cases: list[dict],
) -> tuple[int, int, list[dict]]:
    """Execute candidate against a list of test cases. Returns (passed, total, details)."""
    tests_passed = 0
    tests_total = 0
    details = []

    for case in cases:
        raw_input = case.get("input", "")
        raw_expected = case.get("expected", "")

        parsed = _parse_sample_case(schema, raw_input, raw_expected)
        if parsed is None:
            tests_total += 1
            details.append({
                "input": raw_input,
                "expected": raw_expected,
                "actual": None,
                "passed": False,
                "error": "parse_failed"
            })
            continue

        input_args, expected_output = parsed
        tests_total += 1

        try:
            actual_output, timed_out = _execute_with_timeout(candidate_func, (input_args,), timeout_seconds=5)
        except Exception as e:
            details.append({
                "input": raw_input,
                "expected": raw_expected,
                "actual": None,
                "passed": False,
                "error": str(e)
            })
            continue

        if timed_out:
            details.append({
                "input": raw_input,
                "expected": raw_expected,
                "actual": None,
                "passed": False,
                "error": "timeout"
            })
            continue

        accepted, reason = check_func(copy.deepcopy(input_args), actual_output)
        if accepted:
            tests_passed += 1

        details.append({
            "input": raw_input,
            "expected": raw_expected,
            "actual": str(actual_output),
            "passed": accepted,
            "reason": reason if not accepted else None
        })

    return tests_passed, tests_total, details


def run_candidate(
    candidate_code: str,
    checker_source: str,
    schema: dict,
    test_cases: list[dict] | None = None,
    provenance: str = "hand_verified",
) -> dict:
    """
    Execute a candidate solution against test cases via generated checker.

    If test_cases is provided, executes those cases. Otherwise falls back to
    schema.sample_cases for backward compatibility.

    Results are split by source:
    - sample_results: extracted sample cases from the problem statement
    - generated_results: cases generated via solver agreement gate

    Stages:
    1. Extract candidate function
    2. Execute against sample cases
    3. Execute against generated cases (if provided)
    4. Check outputs via generated checker
    5. Compute E (correct oracle), e (evidence), c (model confidence)
    6. Apply provisional ceiling to trust
    7. Return result dict with separated signals
    """
    from doctor.grading.trust import compute_trust_v1

    result = {
        "verdict": None,
        "trust": None,
        "risk": None,
        "E": None,
        "e": None,
        "tests_passed": 0,
        "tests_total": 0,
        "failure_mode": None,
        "details": [],
        "sample_results": None,
        "generated_results": None,
    }

    problem_id = schema.get("problem_id", "unknown")
    candidate_func = _extract_function(candidate_code, "solve")
    if candidate_func is None:
        for alt_name in ["solution", "main", "answer", "find_answer"]:
            candidate_func = _extract_function(candidate_code, alt_name)
            if candidate_func is not None:
                break

    if candidate_func is None:
        result["failure_mode"] = "candidate_parse_failed"
        result["trust"] = "unverified"
        result["risk"] = "HIGH"
        return result

    check_func = _extract_function(checker_source, "check")
    if check_func is None:
        result["failure_mode"] = "checker_compile_failed"
        result["trust"] = "unverified"
        result["risk"] = "HIGH"
        return result

    sample_cases = schema.get("sample_cases", [])
    if not sample_cases and not test_cases:
        result["failure_mode"] = "no_test_cases"
        result["trust"] = "unverified"
        result["risk"] = "HIGH"
        return result

    sample_cases_formatted = [
        {"input": c.get("input", ""), "expected": c.get("output", ""), "label": f"sample_{i}", "source": "extracted"}
        for i, c in enumerate(sample_cases)
    ]

    total_passed = 0
    total_total = 0
    all_details = []

    if sample_cases_formatted:
        sp, st, sd = _execute_cases(candidate_func, check_func, schema, sample_cases_formatted)
        total_passed += sp
        total_total += st
        all_details.extend(sd)
        result["sample_results"] = {
            "passed": sp,
            "total": st,
            "pass_rate": sp / st if st > 0 else 0.0,
            "details": sd,
        }

    if test_cases:
        gp, gt, gd = _execute_cases(candidate_func, check_func, schema, test_cases)
        total_passed += gp
        total_total += gt
        all_details.extend(gd)
        result["generated_results"] = {
            "passed": gp,
            "total": gt,
            "pass_rate": gp / gt if gt > 0 else 0.0,
            "details": gd,
        }

    result["tests_passed"] = total_passed
    result["tests_total"] = total_total
    result["details"] = all_details

    E = 1 if total_passed == total_total else 0
    e = _compute_evidence_score(total_passed, total_total)
    c = 0.5

    result["E"] = E
    result["e"] = e

    from doctor.grading.evidence import EvidenceBundle
    evidence_bundle = EvidenceBundle(
        pass_rate=round(e, 3),
        test_volume=total_total,
        coverage=0.0,
        error_flags=[d.get("error") for d in all_details if d.get("error")],
    )

    trust_result = compute_trust_v1(E, evidence_bundle, c, provenance=provenance)

    if trust_result["type"] == "aligned_confident_correct":
        trust_result["type"] = "weakly_supported_correct"
        trust_result["risk"] = "MEDIUM"

    result["trust"] = trust_result["type"]
    result["risk"] = trust_result["risk"]

    if total_passed == total_total:
        result["verdict"] = "correct"
    elif total_passed > 0:
        result["verdict"] = "partial"
    else:
        result["verdict"] = "incorrect"

    return result
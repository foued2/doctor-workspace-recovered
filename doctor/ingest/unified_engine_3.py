#!/usr/bin/env python3
"""
Doctor - Strict Pipeline with 5 Gates

Each gate either passes or stops. No conversation, no encouragement.
"""
import os
import json

# ============================================================
# CONFIG
# ============================================================
os.environ.setdefault("LLM_PROVIDER", "openrouter")

HIGH_CONFIDENCE = 0.90
MEDIUM_CONFIDENCE = 0.70

# ============================================================
# MODIFIER CLASSES
# ============================================================
class_modifiers = [
    ("Class 1", ["ignore case", "case insensitive", "ignore whitespace", "trim"]),
    ("Class 2", ["positive only", "non-negative", "strictly greater", "at least", "maximum of"]),
    ("Class 3", ["modified", "but not", "except", "without using", "only use"]),
]

# ============================================================
# GATE 1: PROBLEM RECOGNITION
# ============================================================
def gate1_recognize(problem_statement: str) -> dict:
    """Pass/fail. Returns binding object"""
    from doctor.ingest.unified_engine import analyze_statement
    
    result = analyze_statement(problem_statement)
    trace = result.get("decision_trace", {})
    alignment = trace.get("alignment_score", 0)
    
    status = result.get("status", "unknown")
    match = result.get("matched", result.get("match", trace.get("llm_match", "none")))
    
    if alignment >= HIGH_CONFIDENCE:
        tentative = False
    elif alignment >= MEDIUM_CONFIDENCE:
        tentative = True
    else:
        return {
            "passed": False,
            "stop_reason": "Problem not recognized",
            "confidence": alignment,
            "problem_id": None,
            "tentative": False,
            "modifiers": [],
            "parsed_model": result.get("parsed_model", {})
        }

    return {
        "passed": True,
        "confidence": alignment,
        "problem_id": match if match not in ["none", "no match"] else None,
        "tentative": tentative,
        "modifiers": [],
        "parsed_model": result.get("parsed_model", {})
    }

# ============================================================
# GATE 2: MODIFIER EXTRACTION
# ============================================================
def _modifier_source_fields(parsed_model: dict) -> list[str]:
    """Gate 2 only scans parsed constraints, not the raw statement text."""
    fields = []
    for key in ("constraints", "edge_conditions"):
        values = parsed_model.get(key, [])
        if isinstance(values, list):
            fields.extend(str(value).lower() for value in values if value)
        elif values:
            fields.append(str(values).lower())
    return fields


def gate2_modifiers(parsed_model: dict, problem_id: str) -> dict:
    """Extract modifiers from parsed constraint fields and classify."""
    from doctor.registry.problem_registry import get_problems
    
    if not problem_id:
        return {"passed": True, "variant_id": None, "modifier_class": None}
    
    # Check for modifiers in parsed constraint fields only.
    found_modifiers = []
    modifier_class = None
    modifier_fields = _modifier_source_fields(parsed_model or {})
    
    for cls_name, keywords in class_modifiers:
        for kw in keywords:
            if any(kw in field for field in modifier_fields):
                found_modifiers.append(kw)
                modifier_class = cls_name
                break
    
    # Check for variant in registry
    problems = get_problems()
    variant_id = None
    
    if modifier_class == "Class 3":
        # Look for variant
        base = problem_id
        variant_candidates = [p for p in problems.keys() if base in p or p in base]
        if len(variant_candidates) > 1:  # more than base
            variant_id = variant_candidates[0]  # simplified - pick first variant
    
    if modifier_class == "Class 3" and not variant_id and found_modifiers:
        return {
            "passed": False,
            "stop_reason": "This is a variant I have no tests for",
            "modifier_class": modifier_class,
            "found_modifiers": found_modifiers
        }
    
    return {
        "passed": True,
        "variant_id": variant_id,
        "modifier_class": modifier_class,
        "found_modifiers": found_modifiers
    }

# ============================================================
# GATE 3: SOLUTION INTAKE
# ============================================================
def gate3_solution(solution_path: str) -> dict:
    """Load solution file from disk and validate Python syntax."""
    if not solution_path.strip():
        return {
            "passed": False,
            "stop_reason": "No solution file path provided",
        }

    if not os.path.isfile(solution_path):
        return {
            "passed": False,
            "stop_reason": f"Solution file not found: {solution_path}",
        }

    try:
        with open(solution_path, "r", encoding="utf-8") as f:
            solution_code = f.read()
    except OSError as e:
        return {
            "passed": False,
            "stop_reason": f"Could not read solution file: {e}",
        }

    if not solution_code.strip():
        return {
            "passed": False,
            "stop_reason": f"Solution file is empty: {solution_path}",
        }

    try:
        compile(solution_code, solution_path, "exec")
        return {
            "passed": True,
            "valid": True,
            "solution_code": solution_code,
            "solution_path": solution_path,
        }
    except SyntaxError as e:
        return {
            "passed": False,
            "stop_reason": f"Solution file is not valid Python: {solution_path}",
            "syntax_error": str(e)
        }

# ============================================================
# GATE 4: TEST VERIFICATION
# ============================================================
def gate4_tests(problem_id: str, user_tests: list) -> dict:
    """Check registry for tests"""
    from doctor.registry.problem_registry import get_problems
    
    problems = get_problems()
    
    if problem_id not in problems:
        return {"passed": False, "stop_reason": "No tests available for this problem"}
    
    registry_tests = problems[problem_id].get("execution", {}).get("test_cases", [])
    
    if not registry_tests:
        return {"passed": False, "stop_reason": "No tests available for this problem"}
    
    # User tests are supplementary only
    user_passed = 0
    user_failed = 0
    for tc in user_tests:
        # Can't verify user tests without solution, so just count
        user_failed += 1
    
    return {
        "passed": True,
        "authoritative_tests": registry_tests,
        "user_tests": user_tests,
        "user_passed": user_passed,
        "user_failed": user_failed
    }

# ============================================================
# GATE 5: EXECUTION
# ============================================================
def gate5_execute(solution_code: str, problem_id: str, tests: list, timeout: int = 30) -> dict:
    """Run solution against tests using the shared executor path."""
    from doctor.core.test_executor import TestExecutor
    
    executor = TestExecutor()
    user_provided_tests = tests if tests else []
    authoritative_report = executor.verify(problem_id, solution_code)
    
    if authoritative_report.error:
        return {"passed": False, "stop_reason": f"Execution error: {authoritative_report.error}"}
    
    results = [
        {
            "label": r.label,
            "passed": r.passed,
            "got": r.got,
            "expected": r.expected,
            "error": r.error,
            "validation_type": getattr(r, "validator_kind", None),
        }
        for r in authoritative_report.results
    ]
    
    user_results = []
    user_failed = False
    if user_provided_tests:
        for tc in user_provided_tests:
            trace = executor._run_single_test(solution_code, problem_id, tc)
            passed = trace.get("passed", False) if trace.get("error") is None else False
            if not passed:
                user_failed = True
            user_results.append({
                "label": tc.get("label", "user_test"),
                "passed": passed,
                "got": trace.get("output"),
                "expected": tc.get("expected"),
                "error": trace.get("error"),
                "source": "user_provided"
            })
    
    auth_passed = authoritative_report.verdict == "correct"
    user_failed = any(not r.get("passed") for r in user_results)
    
    return {
        "passed": authoritative_report.passed + len([r for r in user_results if r.get("passed")]),
        "total": authoritative_report.total + len(user_results),
        "results": results + user_results,
        "pass_rate": authoritative_report.pass_rate,
        "authoritative_passed": auth_passed,
        "user_tests_failed": user_failed,
        "error": authoritative_report.error
    }


def _diagnosis_line(result: dict) -> str:
    label = result.get("label", "unknown")
    got = repr(result.get("got"))
    expected = result.get("expected")
    validation_type = result.get("validation_type")
    error = result.get("error", "")

    if error:
        return f"  {label}: got {got} — {error}"

    if validation_type == "arrangement_validator":
        if result.get("got") in (None, -1):
            return f"  {label}: got {got} expected valid arrangement — algorithm returned no solution"
        return f"  {label}: got {got} expected valid arrangement — arrangement invalid"

    return f"  {label}: got {got} expected {repr(expected)}"

# ============================================================
# REPORT GENERATOR
# ============================================================
def generate_report(gate_results: dict) -> str:
    """Generate strict report - no narrative"""
    g1 = gate_results.get("gate1", {})
    g2 = gate_results.get("gate2", {})
    g3 = gate_results.get("gate3", {})
    g4 = gate_results.get("gate4", {})
    g5 = gate_results.get("gate5", {})
    
    problem_id = g1.get("problem_id", "UNKNOWN")
    confidence = g1.get("confidence", 0)
    tentative = g1.get("tentative", False)
    modifiers = g2.get("found_modifiers", [])
    modifier_class = g2.get("modifier_class")
    
    # Verdict
    if g5.get("pass_rate", 0) == 1.0 and not g4.get("user_tests"):
        verdict = "CORRECT"
        trust = "aligned_confident_correct"
        risk = "LOW"
    elif g5.get("pass_rate", 0) == 1.0 and g4.get("user_tests"):
        verdict = "PARTIAL"
        trust = "user_tests_only"
        risk = "MEDIUM"
    elif g5.get("pass_rate", 0) >= 0.5:
        verdict = "PARTIAL"
        trust = "weakly_supported_correct"
        risk = "MEDIUM"
    else:
        verdict = "INCORRECT"
        trust = "false_justified_confidence"
        risk = "HIGH"
    
    # Build report
    lines = []
    lines.append("=" * 50)
    lines.append("DOCTOR REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"PROBLEM: {problem_id}")
    lines.append(f"BINDING CONFIDENCE: {confidence:.2f}")
    lines.append(f"TENTATIVE: {'yes' if tentative else 'no'}")
    lines.append("")
    lines.append(f"VERDICT: {verdict}")
    lines.append(f"TRUST: {trust}")
    lines.append(f"RISK: {risk}")
    
    passed = g5.get("passed", 0)
    total = g5.get("total", 0)
    lines.append(f"EVIDENCE: {passed}/{total} tests passed")
    if total > 0:
        lines.append(f"E = {passed/total:.2f}")
    lines.append("")
    
    mods_str = ", ".join(modifiers) if modifiers else "NONE"
    lines.append(f"MODIFIERS APPLIED: {mods_str}")
    
    user_tests = g4.get("user_tests", [])
    if user_tests:
        lines.append(f"USER TESTS: {g4.get('user_passed', 0)}/{len(user_tests)} passed")
    else:
        lines.append("USER TESTS: NONE PROVIDED")
    lines.append("")
    
    # Diagnosis for INCORRECT/PARTIAL
    if verdict in ["INCORRECT", "PARTIAL"]:
        failed_results = [r for r in g5.get("results", []) if not r.get("passed")]
        if failed_results:
            lines.append(f"DIAGNOSIS:")
            for result in failed_results:
                lines.append(_diagnosis_line(result))
    
    # Summary - one sentence
    if verdict == "CORRECT":
        summary = f"Solution correctly solves {problem_id} with {passed}/{total} authoritative tests passing."
    else:
        summary = f"Solution failed {total - passed} of {total} authoritative tests."
    
    lines.append("")
    lines.append("SUMMARY: " + summary)
    lines.append("=" * 50)
    
    return "\n".join(lines)

# ============================================================
# MAIN PIPELINE
# ============================================================
def main():
    print("=" * 50)
    print("DOCTOR - STRICT PIPELINE")
    print("=" * 50)
    print()
    
    gate_results = {}
    
    # GATE 1
    print("[Gate 1] Problem Recognition")
    print("Paste problem statement (Enter twice to finish):")
    problem_lines = []
    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            problem_lines.append(line)
        except EOFError:
            break
    
    problem_statement = "\n".join(problem_lines)
    
    if not problem_statement.strip():
        print("STOP: No problem statement")
        return
    
    g1 = gate1_recognize(problem_statement)
    gate_results["gate1"] = g1
    
    if not g1["passed"]:
        print(f"STOP: {g1['stop_reason']}")
        print(f"Confidence: {g1['confidence']:.2f}")
        return
    
    print(f"MATCH: {g1['problem_id']}")
    print(f"Confidence: {g1['confidence']:.2f}")
    print(f"Tentative: {g1['tentative']}")
    print()
    
    # GATE 2
    print("[Gate 2] Modifier Extraction")
    g2 = gate2_modifiers(g1.get("parsed_model", {}), g1["problem_id"])
    gate_results["gate2"] = g2
    
    if not g2["passed"]:
        print(f"STOP: {g2['stop_reason']}")
        return
    
    if g2.get("found_modifiers"):
        print(f"Modifiers found: {g2['found_modifiers']}")
    print()
    
    # GATE 3
    print("[Gate 3] Solution Intake")
    print("Enter path to solution file:")
    try:
        solution_path = input().strip()
    except EOFError:
        solution_path = ""

    g3 = gate3_solution(solution_path)
    gate_results["gate3"] = g3
    
    if not g3["passed"]:
        print(f"STOP: {g3['stop_reason']}")
        return
    
    print("Solution validated as Python")
    print()
    
    # GATE 4
    print("[Gate 4] Test Verification")
    print("Provide test cases? (Enter JSON list, or Enter to skip):")
    user_test_lines = []
    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            user_test_lines.append(line)
        except EOFError:
            break
    
    user_tests = []
    if user_test_lines:
        try:
            user_tests = json.loads("\n".join(user_test_lines))
        except:
            print("Invalid JSON, skipping user tests")
    
    g4 = gate4_tests(g1["problem_id"], user_tests)
    gate_results["gate4"] = g4
    
    if not g4["passed"]:
        print(f"STOP: {g4['stop_reason']}")
        return
    
    print(f"Authoritative tests: {len(g4['authoritative_tests'])}")
    print(f"User tests: {len(user_tests)}")
    print()
    
    # GATE 5
    print("[Gate 5] Execution")
    g5 = gate5_execute(g3["solution_code"], g1["problem_id"], g4["authoritative_tests"])
    gate_results["gate5"] = g5
    
    if not g5.get("passed", 0) and g5.get("passed", 0) == 0 and g5.get("total", 0) > 0:
        if g5.get("stop_reason"):
            print(f"STOP: {g5['stop_reason']}")
            return
    
    print(f"Tests: {g5.get('passed', 0)}/{g5.get('total', 0)}")
    for r in g5.get("results", []):
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  {r['label']}: {status}")
    print()
    
    # REPORT
    print(generate_report(gate_results))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Run Doctor's recognition pipeline against benchmark cases.
Outputs results to scratch/benchmark_v1_results.json
"""
import json
import sys
from contextlib import contextmanager
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from doctor.pipeline import run_pipeline

BENCHMARK_PATH = Path("scratch/benchmark_v1_partial.json")
RESULTS_PATH = Path("scratch/benchmark_v1_results.json")
FULL_BENCHMARK_PATH = Path("scratch/full_pipeline_benchmark_v1.json")
FULL_RESULTS_PATH = Path("scratch/full_pipeline_benchmark_v1_results.json")
REPORT_BUCKETS = [
    "canonical",
    "adversarial",
    "out_of_registry",
    "unrecognized_but_executable",
    "invalid",
]
DEFAULT_UNRECOGNIZED_EXECUTABLE_CASES = [
    {
        "id": "code_only_identity",
        "input": "",
        "solution_code": "def mystery(x):\n    return x\n",
        "expected_verdict": "unrecognized_but_executable",
    },
    {
        "id": "code_only_fizzbuzz",
        "input": "",
        "solution_code": (
            "def fizzbuzz(n):\n"
            "    out = []\n"
            "    for i in range(1, n + 1):\n"
            "        if i % 15 == 0:\n"
            "            out.append('FizzBuzz')\n"
            "        elif i % 3 == 0:\n"
            "            out.append('Fizz')\n"
            "        elif i % 5 == 0:\n"
            "            out.append('Buzz')\n"
            "        else:\n"
            "            out.append(str(i))\n"
            "    return out\n"
        ),
        "expected_verdict": "unrecognized_but_executable",
    },
]


def _empty_report():
    return {bucket: {"passed": 0, "failed": 0, "cases": []} for bucket in REPORT_BUCKETS}


def _record_case(results, bucket, entry):
    entry["status"] = "pass" if entry.get("passed") else "fail"
    results[bucket]["cases"].append(entry)
    if entry["status"] == "pass":
        results[bucket]["passed"] += 1
    else:
        results[bucket]["failed"] += 1

def _case_signature(item):
    return {
        "result": item.get("result"),
        "status": item.get("status"),
        "failure_stage": item.get("failure_stage"),
    }


@contextmanager
def _mock_llm_calls():
    """Force all shared LLM entry points to return empty JSON."""
    import doctor.llm_client as llm_client

    original_with_stats = llm_client._call_llm_with_stats
    original_call = llm_client._call_llm

    def empty_with_stats(prompt: str, retries: int = 0):
        return "{}", 0

    def empty_call(prompt: str, retries: int = 0):
        return "{}"

    llm_client._call_llm_with_stats = empty_with_stats
    llm_client._call_llm = empty_call
    try:
        yield
    finally:
        llm_client._call_llm_with_stats = original_with_stats
        llm_client._call_llm = original_call


def _extract_trace(result):
    """Extract detailed trace from pipeline result."""
    recognition = result.get("trace", {}).get("recognition", {})
    matcher_trace = recognition.get("matcher_trace", {})
    parsed_model = recognition.get("parsed_model", {})
    return {
        "decision": result.get("recognition_decision"),
        "matched_class": result.get("matched"),
        "alignment_score": recognition.get("alignment_score", 0.0),
        "failure_stage": _get_failure_stage(result),
        "matcher_trace": {
            "keyword_score": matcher_trace.get("keyword_score", 0.0),
            "rule_score": matcher_trace.get("rule_score", 0.0),
            "lexical_score": matcher_trace.get("lexical_score", 0.0),
            "alignment_score": matcher_trace.get("alignment_score", 0.0),
            "source": matcher_trace.get("source", ""),
        },
        "parsed_model": {
            "input_type": parsed_model.get("input_type", ""),
            "output_type": parsed_model.get("output_type", ""),
            "objective": parsed_model.get("objective", ""),
            "infer_confidence": parsed_model.get("_inferred", {}).get("infer_confidence", ""),
        },
        "oracle_feasibility": result.get("oracle_feasibility", None),
    }


def _get_failure_stage(result):
    """Determine failure stage from pipeline result."""
    pipeline = result.get("pipeline", {})
    if pipeline.get("gate", {}).get("status") == "rejected":
        return "gate"
    decision = result.get("recognition_decision", "unknown")
    if decision == "reject":
        return "matcher"
    return "none"


def collect_benchmark_results():
    """Run recognition pipeline against all benchmark cases."""
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Benchmark file not found: {BENCHMARK_PATH}")
    
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)
    
    results = _empty_report()
    
    # Process out_of_registry_cases
    print(f"Processing {len(benchmark.get('out_of_registry_cases', []))} out-of-registry cases...")
    for case in benchmark.get("out_of_registry_cases", []):
        result = run_pipeline(case["input"])
        trace = _extract_trace(result)
        match_candidate = result.get("matched")
        passed = result.get("verdict") == "InvalidInput" and match_candidate in (None, "no match")
        entry = {
            "input": case["input"],
            "expected": case["expected"],
            "result": match_candidate,
            "actual_verdict": result.get("verdict"),
            "reason": result.get("reason"),
            "passed": passed,
            "failure_stage": trace["failure_stage"],
        }
        entry.update(trace)
        _record_case(results, "out_of_registry", entry)
    
    # Process invalid_cases
    print(f"Processing {len(benchmark.get('invalid_cases', []))} invalid cases...")
    for case in benchmark.get("invalid_cases", []):
        result = run_pipeline(case["input"])
        trace = _extract_trace(result)
        match_candidate = result.get("matched")
        passed = result.get("verdict") == "InvalidInput" and result.get("reason") != "pipeline_incomplete"
        entry = {
            "input": case["input"],
            "expected": case["expected"],
            "result": match_candidate,
            "actual_verdict": result.get("verdict"),
            "reason": result.get("reason"),
            "passed": passed,
            "failure_stage": trace["failure_stage"],
        }
        entry.update(trace)
        _record_case(results, "invalid", entry)
    
    # Process in_registry_cases
    print(f"Processing {len(benchmark.get('in_registry_cases', []))} in-registry cases...")
    for case in benchmark.get("in_registry_cases", []):
        result = run_pipeline(case["input"])
        trace = _extract_trace(result)
        expected = case["expected"]
        actual = result.get("matched")
        decision = result.get("recognition_decision", "unknown")
        bucket = case.get("benchmark_bucket", "canonical")
        if bucket not in ("canonical", "adversarial"):
            bucket = "canonical"
        passed = actual == expected
        entry = {
            "input": case["input"],
            "expected": expected,
            "result": actual,
            "actual_verdict": result.get("verdict"),
            "reason": result.get("reason"),
            "passed": passed,
            "failure_stage": trace["failure_stage"],
        }
        entry.update(trace)
        _record_case(results, bucket, entry)

    adversarial_cases = benchmark.get("adversarial_cases", [])
    print(f"Processing {len(adversarial_cases)} adversarial cases...")
    for case in adversarial_cases:
        result = run_pipeline(case["input"], case.get("solution_code"))
        trace = _extract_trace(result)
        expected = case.get("expected")
        actual = result.get("matched")
        passed = actual == expected if expected is not None else result.get("verdict") == case.get("expected_verdict")
        if passed and case.get("expected_reason") is not None:
            passed = result.get("reason") == case.get("expected_reason")
        entry = {
            "id": case.get("id"),
            "input": case["input"],
            "expected": expected if expected is not None else case.get("expected_verdict"),
            "expected_reason": case.get("expected_reason"),
            "result": actual,
            "actual_verdict": result.get("verdict"),
            "reason": result.get("reason"),
            "passed": passed,
            "failure_stage": trace["failure_stage"],
        }
        entry.update(trace)
        _record_case(results, "adversarial", entry)

    executable_cases = benchmark.get("unrecognized_but_executable_cases", DEFAULT_UNRECOGNIZED_EXECUTABLE_CASES)
    print(f"Processing {len(executable_cases)} unrecognized-but-executable cases...")
    for case in executable_cases:
        result = run_pipeline(case.get("input", ""), case["solution_code"])
        trace = _extract_trace(result)
        expected = case.get("expected_verdict", "unrecognized_but_executable")
        passed = result.get("verdict") == expected
        entry = {
            "id": case.get("id"),
            "input": case.get("input", ""),
            "expected": expected,
            "result": result.get("matched"),
            "actual_verdict": result.get("verdict"),
            "reason": result.get("reason"),
            "passed": passed,
            "failure_stage": trace["failure_stage"],
        }
        entry.update(trace)
        _record_case(results, "unrecognized_but_executable", entry)
    
    return results


def run_benchmark():
    results = collect_benchmark_results()
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {RESULTS_PATH}")
    print("Bucket results:")
    for bucket in REPORT_BUCKETS:
        summary = results[bucket]
        print(f"  {bucket}: {summary['passed']} passed, {summary['failed']} failed")
    
    return 0


def run_mock_llm_invariant():
    """Acceptance test: empty LLM outputs must not change any decision."""
    baseline = collect_benchmark_results()
    with _mock_llm_calls():
        mocked = collect_benchmark_results()

    differences = []
    for group in REPORT_BUCKETS:
        base_cases = baseline[group]["cases"]
        mock_cases = mocked[group]["cases"]
        for idx, (base_item, mock_item) in enumerate(zip(base_cases, mock_cases)):
            if _case_signature(base_item) != _case_signature(mock_item):
                differences.append(
                    {
                        "group": group,
                        "index": idx,
                        "input": base_item.get("input"),
                        "baseline": _case_signature(base_item),
                        "mocked": _case_signature(mock_item),
                    }
                )

    report = {
        "pass": not differences,
        "differences": differences,
        "baseline": baseline,
        "mocked": mocked,
    }
    output_path = Path("scratch/benchmark_v1_mock_llm_invariant.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if differences:
        print(f"Mock-LLM invariant FAILED: {len(differences)} decision changes")
        print(f"Report saved to: {output_path}")
        return 1

    print("Mock-LLM invariant PASSED: zero decision changes")
    print(f"Report saved to: {output_path}")
    return 0


def collect_full_pipeline_results():
    """Run executable benchmark cases through the full canonical pipeline."""
    if not FULL_BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Benchmark file not found: {FULL_BENCHMARK_PATH}")

    with open(FULL_BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    results = []
    for case in benchmark.get("cases", []):
        result = run_pipeline(
            "",
            case["solution_code"],
            problem_id=case["problem_id"],
            model_confidence=float(case.get("model_confidence", 1.0)),
        )
        verdict_ok = result.get("verdict") == case.get("expected_verdict")
        trust_ok = result.get("trust_type") == case.get("expected_trust_type")
        results.append(
            {
                "id": case["id"],
                "problem_id": case["problem_id"],
                "label": case.get("label"),
                "expected_verdict": case.get("expected_verdict"),
                "actual_verdict": result.get("verdict"),
                "expected_trust_type": case.get("expected_trust_type"),
                "actual_trust_type": result.get("trust_type"),
                "pass_rate": result.get("pass_rate"),
                "evidence": result.get("evidence"),
                "status": "pass" if verdict_ok and trust_ok else "fail",
            }
        )
    return results


def run_full_pipeline_benchmark():
    results = collect_full_pipeline_results()
    with open(FULL_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, indent=2, ensure_ascii=False)

    trust_types = sorted({item["actual_trust_type"] for item in results})
    missing_trust = [item["id"] for item in results if item["actual_trust_type"] is None]
    by_verdict = {}
    for item in results:
        bucket = item["expected_verdict"]
        by_verdict.setdefault(bucket, {"passed": 0, "failed": 0})
        by_verdict[bucket]["passed" if item["status"] == "pass" else "failed"] += 1

    print(f"Full pipeline benchmark saved to: {FULL_RESULTS_PATH}")
    print("  Bucket results by expected verdict:")
    for bucket in sorted(by_verdict):
        summary = by_verdict[bucket]
        print(f"    {bucket}: {summary['passed']} passed, {summary['failed']} failed")
    print(f"  Trust types: {', '.join(str(item) for item in trust_types)}")

    if missing_trust:
        print(f"  Missing trust_type: {', '.join(missing_trust)}")
    failures = [item for item in results if item["status"] != "pass"]
    if failures:
        print("  Failures:")
        for item in failures:
            print(
                "   "
                f"{item['id']}: verdict {item['actual_verdict']} "
                f"(expected {item['expected_verdict']}), trust {item['actual_trust_type']} "
                f"(expected {item['expected_trust_type']})"
            )
        return 1
    if missing_trust:
        return 1
    if len(trust_types) < 3:
        print("  Expected at least 3 distinct trust types")
        return 1
    return 0

if __name__ == "__main__":
    if "--mock-llm-invariant" in sys.argv:
        sys.exit(run_mock_llm_invariant())
    if "--full-pipeline" in sys.argv:
        sys.exit(run_full_pipeline_benchmark())
    sys.exit(run_benchmark())

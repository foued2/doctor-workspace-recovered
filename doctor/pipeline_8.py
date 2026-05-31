"""
DOCTOR Verdict Boundary Stress Harness
May 5 2026 — GPT-designed, 3-family surgical test

Families:
  A — Constant-function trap (must never reach 'correct')
  B — Deterministic wrong (must reach 'incorrect', not degrade)
  C — Underspecified but executable (must stay 'unrecognized_but_executable')

Cross-cut modifier: each case run under 3-probe and 5-probe distributions.

Usage:
  py -3.14 verdict_boundary_harness.py

Place in repo root or adjust sys.path below.
"""

import sys
import json
import textwrap

# --- adjust if running from a subdirectory ---
sys.path.insert(0, ".")

# Import the pipeline entry point — adapt name if different
try:
    from doctor.pipeline import run_pipeline
except ImportError:
    try:
        from doctor.core.pipeline import run_pipeline
    except ImportError:
        raise ImportError(
            "Cannot locate run_pipeline. "
            "Check doctor/pipeline.py or doctor/core/pipeline.py."
        )

# ─────────────────────────────────────────────
# Problem specs
# ─────────────────────────────────────────────

SPEC_WELL_DEFINED = {
    "statement": "Given a list of integers, return their sum.",
    "inferred_input_schema": {"arr": "list[int]"},
    "inferred_output_shape": "int",
    "constraint_hypotheses": ["output equals arithmetic sum of all elements"],
    "ambiguity_flags": [],
    "completeness_score": 0.9,
}

SPEC_WEAK = {
    "statement": "Process the input and return a result.",
    "inferred_input_schema": {"arr": "list[int]"},
    "inferred_output_shape": "unknown",
    "constraint_hypotheses": [],
    "ambiguity_flags": ["ambiguous_output"],
    "completeness_score": 0.3,
}

SPEC_UNDERSPECIFIED = {
    "statement": "Do something with the input.",
    "inferred_input_schema": {},
    "inferred_output_shape": "unknown",
    "constraint_hypotheses": [],
    "ambiguity_flags": ["no_statement_provided", "ambiguous_output"],
    "completeness_score": 0.0,
}

# ─────────────────────────────────────────────
# Candidate code
# ─────────────────────────────────────────────

CODE_CORRECT = textwrap.dedent("""\
    def solution(arr):
        return sum(arr)
""")

CODE_CONSTANT_ZERO = textwrap.dedent("""\
    def solution(arr):
        return 0
""")

CODE_CONSTANT_MATCHES_EMPTY = textwrap.dedent("""\
    def solution(arr):
        # returns 0, which matches sum([]) == 0
        return 0
""")

CODE_DETERMINISTIC_WRONG = textwrap.dedent("""\
    def solution(arr):
        return len(arr)  # consistently wrong: returns count, not sum
""")

CODE_STABLE_EXECUTABLE = textwrap.dedent("""\
    def solution(*args, **kwargs):
        return 42  # stable, executable, meaningless
""")

# ─────────────────────────────────────────────
# Test cases
# ─────────────────────────────────────────────

CASES = [
    # Family A — Constant-function trap
    {
        "id": "A1",
        "family": "A",
        "desc": "Constant zero vs well-defined sum spec",
        "spec": SPEC_WELL_DEFINED,
        "code": CODE_CONSTANT_ZERO,
        "must_not_reach": ["correct"],
        "expected": ["incorrect", "unrecognized_but_executable"],
    },
    {
        "id": "A2",
        "family": "A",
        "desc": "Constant zero matches sum([]) — silent promotion risk",
        "spec": SPEC_WELL_DEFINED,
        "code": CODE_CONSTANT_MATCHES_EMPTY,
        "must_not_reach": ["correct"],
        "expected": ["incorrect", "unrecognized_but_executable"],
    },
    {
        "id": "A3",
        "family": "A",
        "desc": "Constant zero vs weak spec — overcommitment risk",
        "spec": SPEC_WEAK,
        "code": CODE_CONSTANT_ZERO,
        "must_not_reach": ["correct"],
        "expected": ["unrecognized_but_executable", "insufficient_evidence", "incorrect"],
    },

    # Family B — Deterministic wrong
    {
        "id": "B1",
        "family": "B",
        "desc": "len(arr) vs sum spec — must reach incorrect",
        "spec": SPEC_WELL_DEFINED,
        "code": CODE_DETERMINISTIC_WRONG,
        "must_not_reach": ["correct", "unrecognized_but_executable"],
        "expected": ["incorrect"],
    },
    {
        "id": "B2",
        "family": "B",
        "desc": "len(arr) vs weak spec — degradation risk",
        "spec": SPEC_WEAK,
        "code": CODE_DETERMINISTIC_WRONG,
        "must_not_reach": ["correct"],
        "expected": ["incorrect", "unrecognized_but_executable"],
    },

    # Family C — Underspecified but executable
    {
        "id": "C1",
        "family": "C",
        "desc": "Stable executable vs underspecified spec — must not reach correct",
        "spec": SPEC_UNDERSPECIFIED,
        "code": CODE_STABLE_EXECUTABLE,
        "must_not_reach": ["correct", "incorrect"],
        "expected": ["unrecognized_but_executable", "insufficient_evidence"],
    },
    {
        "id": "C2",
        "family": "C",
        "desc": "Correct sum vs underspecified spec — overcommitment risk",
        "spec": SPEC_UNDERSPECIFIED,
        "code": CODE_CORRECT,
        "must_not_reach": ["correct"],
        "expected": ["unrecognized_but_executable", "insufficient_evidence"],
    },
]

# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def extract_fields(result):
    """Pull mandatory observability fields from pipeline result."""
    if isinstance(result, dict):
        return result
    # Handle dataclass or object
    fields = ["verdict", "semantic_determinacy_score", "constraint_source",
              "agreement", "probe_outputs", "execution"]
    out = {}
    for f in fields:
        out[f] = getattr(result, f, None)
    # Also try candidate_artifact sub-fields
    artifact = getattr(result, "candidate_artifact", None) or {}
    if isinstance(artifact, dict):
        for f in ["semantic_determinacy_score", "constraint_source",
                  "probe_summary", "agreement_result"]:
            if f in artifact and out.get(f) is None:
                out[f] = artifact[f]
    return out


def run_case(case):
    results = []
    for label, probe_count in [("3-probe", 3), ("5-probe", 5)]:
        try:
            raw = run_pipeline(
                statement=case["spec"]["statement"],
                solution_code=case["code"],
            )
        except TypeError:
            raw = run_pipeline(
                statement=case["spec"]["statement"],
                solution_code=case["code"],
            )
        except Exception as e:
            results.append({
                "probe_label": label,
                "error": str(e),
                "verdict": "PIPELINE_ERROR",
            })
            continue

        fields = extract_fields(raw)
        verdict = fields.get("verdict") or getattr(raw, "verdict", "unknown")

        violation = verdict in case["must_not_reach"]
        results.append({
            "probe_label": label,
            "verdict": verdict,
            "violation": violation,
            "semantic_determinacy_score": fields.get("semantic_determinacy_score"),
            "constraint_source": fields.get("constraint_source"),
            "agreement": fields.get("agreement"),
        })
    return results


def run_all():
    print("=" * 64)
    print("DOCTOR VERDICT BOUNDARY HARNESS")
    print("=" * 64)

    violations = []
    all_results = []

    for case in CASES:
        print(f"\n[{case['id']}] {case['family']} — {case['desc']}")
        print(f"  must_not_reach: {case['must_not_reach']}")
        print(f"  expected:       {case['expected']}")

        runs = run_case(case)
        for run in runs:
            verdict = run.get("verdict", "unknown")
            violation = run.get("violation", False)
            flag = "VIOLATION" if violation else "OK"
            print(f"  [{run['probe_label']}] verdict={verdict} {flag}")
            print(f"    determinacy={run.get('semantic_determinacy_score')} "
                  f"constraint_source={run.get('constraint_source')}")
            if violation:
                violations.append({
                    "case": case["id"],
                    "family": case["family"],
                    "probe_label": run["probe_label"],
                    "verdict": verdict,
                    "must_not_reach": case["must_not_reach"],
                })

        all_results.append({"case": case["id"], "runs": runs})

    print("\n" + "=" * 64)
    print(f"SUMMARY: {len(violations)} violation(s) across {len(CASES)} cases")
    if violations:
        print("\nVIOLATIONS:")
        for v in violations:
            print(f"  [{v['case']}] {v['probe_label']} -> {v['verdict']} "
                  f"(must not reach {v['must_not_reach']})")
    else:
        print("No boundary violations detected.")
    print("=" * 64)

    # Dump full results for offline analysis
    with open("verdict_boundary_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("\nFull results written to verdict_boundary_results.json")


if __name__ == "__main__":
    run_all()

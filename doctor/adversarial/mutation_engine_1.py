"""Adversarial registry audit harness.

This module treats registry entries as untrusted until they survive attacks
against spec clarity, test strength, oracle behavior, mutation resistance, and
semantic duplication. It is intentionally hostile: a single critical failure
produces a Reject verdict.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from doctor.adversarial.mutation_engine import MutationEngine
from doctor.core.sandbox_runner import run_solution_in_sandbox
from doctor.core.test_executor import TestCase, _results_equal
from doctor.registry.registry import load_registry


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "doctor" / "registry" / "problem_registry.json"
DEFAULT_JSON_OUT = ROOT / "scratch" / "adversarial_registry_audit.json"
DEFAULT_MD_OUT = ROOT / "scratch" / "adversarial_registry_audit.md"

EDGE_LABEL_HINTS = {
    "empty",
    "single",
    "zero",
    "negative",
    "overflow",
    "boundary",
    "edge",
    "min",
    "max",
    "duplicate",
    "all_same",
    "not_found",
    "one_empty",
    "both_empty",
}
MULTI_OUTPUT_HINTS = (
    "any order",
    "return all",
    "all possible",
    "all unique",
    "indices",
    "permutations",
    "combinations",
)
STOPWORDS = {
    "the",
    "and",
    "or",
    "to",
    "of",
    "a",
    "an",
    "in",
    "is",
    "are",
    "you",
    "given",
    "return",
    "with",
    "that",
    "this",
    "for",
    "as",
    "by",
    "be",
}


@dataclass
class AuditCell:
    status: str
    failures: list[str] = field(default_factory=list)


@dataclass
class AuditRow:
    problem_id: str
    spec_integrity: AuditCell
    test_strength: AuditCell
    oracle_reliability: AuditCell
    mutation_resistance: AuditCell
    duplication_risk: AuditCell
    verdict: str
    critical_failures: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "Problem ID": self.problem_id,
            "Spec Integrity": self.spec_integrity.status,
            "Test Strength": self.test_strength.status,
            "Oracle Reliability": self.oracle_reliability.status,
            "Mutation Resistance": self.mutation_resistance.status,
            "Duplication Risk": self.duplication_risk.status,
            "Verdict": self.verdict,
            "Critical Failures": self.critical_failures,
            "details": {
                "spec_integrity": self.spec_integrity.failures,
                "test_strength": self.test_strength.failures,
                "oracle_reliability": self.oracle_reliability.failures,
                "mutation_resistance": self.mutation_resistance.failures,
                "duplication_risk": self.duplication_risk.failures,
            },
        }


def _entry_tests(entry: dict) -> list[dict]:
    tests = entry.get("execution", {}).get("test_cases", [])
    return tests if isinstance(tests, list) else []


def _sandbox_tests(test_cases: list[dict]) -> list[TestCase]:
    return [
        TestCase(
            input=tuple(tc.get("input", [])),
            expected=tc.get("expected"),
            label=tc.get("label", ""),
            validation_type=tc.get("validation_type"),
        )
        for tc in test_cases
    ]


def _run_code(problem_id: str, code: str, test_cases: list[dict]) -> tuple[bool, float, list[dict], str]:
    sandbox = run_solution_in_sandbox(
        code=code,
        problem_id=problem_id,
        tests=_sandbox_tests(test_cases),
        timeout_seconds=10,
        per_test_timeout_seconds=2,
    )
    total = sandbox.total or len(test_cases)
    rate = sandbox.passed / total if total else 0.0
    return sandbox.ok, rate, sandbox.results, sandbox.error


def _py_literal(value: Any) -> str:
    return repr(copy.deepcopy(value))


def _constant_solution(expected: Any) -> str:
    return f"def audit_stub(*args):\n    return {_py_literal(expected)}\n"


def _memorization_solution(test_cases: list[dict]) -> str:
    cases = {repr(tuple(tc.get("input", []))): tc.get("expected") for tc in test_cases}
    return (
        "import copy\n"
        f"_AUDIT_CASES = {_py_literal(cases)}\n"
        "def audit_memorized(*args):\n"
        "    key = repr(args)\n"
        "    if key in _AUDIT_CASES:\n"
        "        return copy.deepcopy(_AUDIT_CASES[key])\n"
        "    return None\n"
    )


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _has_edge_label(test_cases: list[dict]) -> bool:
    for tc in test_cases:
        label = str(tc.get("label", "")).lower()
        if any(hint in label for hint in EDGE_LABEL_HINTS):
            return True
    return False


def _same_expected_for_all(test_cases: list[dict]) -> bool:
    if len(test_cases) < 2:
        return True
    first = test_cases[0].get("expected")
    return all(tc.get("expected") == first for tc in test_cases[1:])


def _probe_oracle(entry: dict, test_cases: list[dict]) -> AuditCell:
    failures: list[str] = []
    description = str(entry.get("spec", {}).get("description", "")).lower()

    for tc in test_cases:
        expected = tc.get("expected")
        if isinstance(expected, float):
            if _results_equal(expected + 1e-6, expected):
                failures.append("invalid float perturbation outside tolerance accepted")
        if isinstance(expected, list) and expected and all(isinstance(x, list) for x in expected):
            reversed_outer = list(reversed(expected))
            if "any order" in description and not _results_equal(reversed_outer, expected):
                failures.append(f"{tc.get('label', '')}: valid outer-order alternative rejected")
            if _results_equal(expected[:1], expected) and len(expected) > 1:
                failures.append(f"{tc.get('label', '')}: incomplete structured output accepted")

    if any(hint in description for hint in MULTI_OUTPUT_HINTS):
        if not any(tc.get("validation_type") for tc in test_cases):
            failures.append("multi-output semantics lack explicit validation_type")

    status = "Fail" if failures else "Pass"
    return AuditCell(status, failures)


def _attack_spec(entry: dict, test_cases: list[dict]) -> AuditCell:
    failures: list[str] = []
    spec = entry.get("spec", {})
    execution = entry.get("execution", {})
    description = str(spec.get("description", "") or "")

    if entry.get("verifiable") is False or execution.get("executable") is False:
        failures.append("entry is marked non-verifiable or non-executable")
    if len(description.strip()) < 80:
        failures.append("description too short to encode a stable contract")
    if not spec.get("reference_solution") and entry.get("verifiable", True):
        failures.append("verifiable entry has no reference_solution")
    if len(test_cases) < 3:
        failures.append(f"test suite has fewer than 3 cases ({len(test_cases)})")
    if any(hint in description.lower() for hint in MULTI_OUTPUT_HINTS):
        if not any(tc.get("validation_type") for tc in test_cases):
            failures.append("underspecified equivalence for multiple-valid-output problem")

    return AuditCell("Fail" if failures else "Pass", failures)


def _attack_tests(problem_id: str, test_cases: list[dict]) -> AuditCell:
    failures: list[str] = []
    if not test_cases:
        return AuditCell("Fail", ["no executable tests"])

    if len(test_cases) < 5:
        failures.append(f"low test count ({len(test_cases)})")
    if not _has_edge_label(test_cases):
        failures.append("no labeled boundary/edge case")
    if _same_expected_for_all(test_cases):
        failures.append("all tests share identical expected output")

    ok, rate, _, error = _run_code(problem_id, _constant_solution(test_cases[0].get("expected")), test_cases)
    if ok and math.isclose(rate, 1.0):
        failures.append("constant-return wrong solution passes all tests")
    elif error:
        failures.append(f"constant-return probe execution error: {error[:80]}")

    ok, rate, _, error = _run_code(problem_id, _memorization_solution(test_cases), test_cases)
    if ok and math.isclose(rate, 1.0):
        failures.append("exact-input memorization wrong solution passes all tests")
    elif error:
        failures.append(f"memorization probe execution error: {error[:80]}")

    return AuditCell("Fail" if any("passes all tests" in f for f in failures) else ("Warn" if failures else "Pass"), failures)


def _attack_mutations(problem_id: str, reference_code: str, test_cases: list[dict]) -> AuditCell:
    if not reference_code:
        return AuditCell("Fail", ["no reference_solution to mutate"])

    ok, baseline_rate, _, error = _run_code(problem_id, reference_code, test_cases)
    if not ok or not math.isclose(baseline_rate, 1.0):
        return AuditCell("Fail", [f"reference baseline does not pass E=1.0 (rate={baseline_rate:.3f}, error={error[:80]})"])

    mutations = MutationEngine(problem_id, num_variants_per_class=2).generate_all(reference_code)
    if not mutations:
        return AuditCell("Warn", ["no syntactic mutations generated"])

    survivors: list[str] = []
    killed = 0
    for mutation in mutations[:20]:
        ok, rate, _, _ = _run_code(problem_id, mutation.mutated_code, test_cases)
        if ok and math.isclose(rate, 1.0):
            survivors.append(f"{mutation.mutation_class}:{mutation.variant_index}:{mutation.description}")
        else:
            killed += 1

    failures = []
    if survivors:
        failures.append(f"{len(survivors)} mutated incorrect solution(s) survived")
        failures.extend(survivors[:5])
    failures.append(f"mutation kill rate {killed}/{min(len(mutations), 20)}")
    return AuditCell("Fail" if survivors else "Pass", failures)


def _duplication_index(registry: dict[str, dict]) -> dict[str, tuple[str, float]]:
    tokenized = {
        pid: _tokens(str(entry.get("spec", {}).get("description", "")))
        for pid, entry in registry.items()
        if isinstance(entry, dict)
    }
    result: dict[str, tuple[str, float]] = {}
    for pid, toks in tokenized.items():
        best_pid = ""
        best_score = 0.0
        for other_pid, other_toks in tokenized.items():
            if pid == other_pid:
                continue
            score = _jaccard(toks, other_toks)
            if score > best_score:
                best_pid = other_pid
                best_score = score
        result[pid] = (best_pid, best_score)
    return result


def _attack_duplication(problem_id: str, duplicate_scores: dict[str, tuple[str, float]]) -> AuditCell:
    other, score = duplicate_scores.get(problem_id, ("", 0.0))
    if score >= 0.70:
        return AuditCell("Fail", [f"near-duplicate of {other} (jaccard={score:.3f})"])
    if score >= 0.50:
        return AuditCell("Warn", [f"possible duplicate of {other} (jaccard={score:.3f})"])
    return AuditCell("Pass", [])


def _verdict(cells: list[AuditCell]) -> str:
    if any(cell.status == "Fail" for cell in cells):
        return "Reject"
    if any(cell.status == "Warn" for cell in cells):
        return "Unstable"
    return "Accept"


def audit_registry(registry: dict[str, dict], limit: int | None = None) -> list[AuditRow]:
    duplicate_scores = _duplication_index(registry)
    rows: list[AuditRow] = []

    for problem_id in sorted(registry.keys(), key=lambda x: (str(x).isdigit(), int(x) if str(x).isdigit() else str(x))):
        entry = registry[problem_id]
        if not isinstance(entry, dict):
            continue
        if limit is not None and len(rows) >= limit:
            break

        test_cases = _entry_tests(entry)
        reference_code = str(entry.get("spec", {}).get("reference_solution") or "")

        spec = _attack_spec(entry, test_cases)
        tests = _attack_tests(problem_id, test_cases)
        oracle = _probe_oracle(entry, test_cases)
        mutation = _attack_mutations(problem_id, reference_code, test_cases)
        duplication = _attack_duplication(problem_id, duplicate_scores)

        cells = [spec, tests, oracle, mutation, duplication]
        verdict = _verdict(cells)
        critical = []
        for cell in cells:
            if cell.status == "Fail":
                critical.extend(cell.failures)

        rows.append(AuditRow(
            problem_id=problem_id,
            spec_integrity=spec,
            test_strength=tests,
            oracle_reliability=oracle,
            mutation_resistance=mutation,
            duplication_risk=duplication,
            verdict=verdict,
            critical_failures=critical,
        ))

    return rows


def format_markdown(rows: list[AuditRow]) -> str:
    header = (
        "| Problem ID | Spec Integrity | Test Strength | Oracle Reliability | "
        "Mutation Resistance | Duplication Risk | Verdict | Critical Failures |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    lines = [header]
    for row in rows:
        failures = "; ".join(row.critical_failures[:4])
        if len(row.critical_failures) > 4:
            failures += f"; +{len(row.critical_failures) - 4} more"
        lines.append(
            f"| {row.problem_id} | {row.spec_integrity.status} | {row.test_strength.status} | "
            f"{row.oracle_reliability.status} | {row.mutation_resistance.status} | "
            f"{row.duplication_risk.status} | {row.verdict} | {failures} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run adversarial registry audit")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--limit", type=int, default=0, help="Audit first N entries only")
    parser.add_argument("--json-out", default=str(DEFAULT_JSON_OUT))
    parser.add_argument("--md-out", default=str(DEFAULT_MD_OUT))
    args = parser.parse_args()

    registry = load_registry(args.registry)
    rows = audit_registry(registry, limit=args.limit or None)

    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps([row.as_dict() for row in rows], indent=2), encoding="utf-8")
    md_path.write_text(format_markdown(rows), encoding="utf-8")

    print(format_markdown(rows))
    print()
    print(f"Audited: {len(rows)}")
    print(f"Reject: {sum(1 for row in rows if row.verdict == 'Reject')}")
    print(f"Unstable: {sum(1 for row in rows if row.verdict == 'Unstable')}")
    print(f"Accept: {sum(1 for row in rows if row.verdict == 'Accept')}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

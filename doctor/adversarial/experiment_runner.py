"""Experiment runner — executes solver populations against probe sets.

RECONSTRUCTED — original unrecoverable from PhotoRec.
Provides ExperimentSolver, ExperimentSpec, run_experiment, write_experiment_artifacts
for lc45_bimaristan.py (imported via wildcard).

Contract: output record must pass validate_run_record from experiment_contract.py.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from doctor.adversarial.experiment_contract import (
    ExperimentInput,
    SolverClassification,
    canonical_json,
    validate_run_record,
)
from doctor.adversarial.transition_gate import write_gated_artifact


@dataclass(frozen=True)
class ExperimentSolver:
    solver_id: str
    run: Callable[..., Any]


@dataclass(frozen=True)
class ExperimentSpec:
    problem_id: str
    solver_set_id: str
    manifold_set_id: str
    probe_set_id: str
    failure_class_version: str
    inputs: tuple[ExperimentInput, ...]
    solvers: tuple[ExperimentSolver, ...]
    classify: Callable[..., tuple[SolverClassification, ...]]
    status: str
    notes: str = ""


@dataclass(frozen=True)
class ExecutionRow:
    solver_id: str
    input_id: str
    observed: int
    expected: int
    passed: bool
    failure_record: dict[str, Any] | None = None


def _execution_hash(inputs: list[dict[str, Any]], solvers: list[str]) -> str:
    return hashlib.sha256(canonical_json({"inputs": inputs, "solvers": solvers}).encode()).hexdigest()


def run_experiment(spec: ExperimentSpec) -> dict[str, Any]:
    """Execute all solvers on all inputs, classify, return validated record."""
    input_dicts = [
        {
            "input_id": inp.input_id,
            "manifold_id": inp.manifold_id,
            "payload": inp.payload,
            "expected": inp.expected,
        }
        for inp in spec.inputs
    ]

    executions: list[dict[str, Any]] = []
    for solver in spec.solvers:
        for inp in spec.inputs:
            try:
                observed = solver.run(**inp.payload)
            except Exception as exc:
                observed = -999999
                failure_record = {"exception": type(exc).__name__, "message": str(exc)}
            else:
                failure_record = None

            passed = observed == inp.expected
            executions.append(
                {
                    "solver_id": solver.solver_id,
                    "input_id": inp.input_id,
                    "observed": int(observed),
                    "expected": int(inp.expected),
                    "passed": bool(passed),
                    "failure_record": failure_record,
                }
            )

    classifications = spec.classify(spec.inputs, executions)
    classification_dicts = [
        {
            "solver_id": c.solver_id,
            "label": c.label,
            "failure_class": c.failure_class,
            "mechanism": c.mechanism,
            "evidence_input_ids": list(c.evidence_input_ids),
        }
        for c in classifications
    ]

    record = {
        "descriptor": {
            "problem_id": spec.problem_id,
            "solver_set_id": spec.solver_set_id,
            "manifold_set_id": spec.manifold_set_id,
            "probe_set_id": spec.probe_set_id,
            "label_schema_version": "1.0.0",
            "execution_hash": _execution_hash(input_dicts, [s.solver_id for s in spec.solvers]),
            "failure_class_version": spec.failure_class_version,
        },
        "inputs": input_dicts,
        "executions": executions,
        "classifications": classification_dicts,
    }

    validate_run_record(record)
    return record


def write_experiment_artifacts(
    *,
    report: dict[str, Any],
    report_path: Path,
    record: dict[str, Any],
    record_path: Path,
) -> None:
    """Write report and record JSON files through SSC-v2 transition gate."""
    write_gated_artifact(report_path, report, "META", "ARTIFACT_WRITE", ("META",))
    write_gated_artifact(record_path, record, "META", "ARTIFACT_WRITE", ("META",))

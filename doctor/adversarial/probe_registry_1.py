"""Shared experiment-run contract for adversarial Doctor runs."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


LABEL_SCHEMA_VERSION = "optc-labels-v1"
RUN_RECORD_SCHEMA_VERSION = "doctor-experiment-run-v1"
PROVENANCE_SCHEMA_VERSION = "k-provenance-v1"

ClassificationLabel = Literal["BROKEN", "SURVIVOR", "UNKNOWN"]

VALID_LABELS = {"BROKEN", "SURVIVOR", "UNKNOWN"}
REQUIRED_ERD_FIELDS = {
    "problem_id",
    "solver_set_id",
    "manifold_set_id",
    "probe_set_id",
    "label_schema_version",
    "execution_hash",
    "failure_class_version",
}
REQUIRED_PROVENANCE_FIELDS = {
    "oracle_name",
    "oracle_version",
    "comparator_name",
    "comparator_version",
    "representation_name",
    "representation_version",
    "perturbation_family",
    "proof_card_id",
    "evaluated_at",
    "base_input_hash",
    "perturbed_input_hash",
    "perturbation_class",
}


class ExperimentContractError(ValueError):
    pass


@dataclass(frozen=True)
class ExperimentRunDescriptor:
    problem_id: str
    solver_set_id: str
    manifold_set_id: str
    probe_set_id: str
    label_schema_version: str
    execution_hash: str
    failure_class_version: str
    run_record_schema_version: str = RUN_RECORD_SCHEMA_VERSION
    status: str = "experimental"
    notes: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentInput:
    input_id: str
    manifold_id: str
    payload: dict[str, Any]
    expected: Any


@dataclass(frozen=True)
class SolverExecution:
    solver_id: str
    input_id: str
    observed: Any
    expected: Any
    passed: bool
    failure_record: dict[str, Any] | None = None


@dataclass(frozen=True)
class SolverClassification:
    solver_id: str
    label: ClassificationLabel
    failure_class: str | None = None
    mechanism: str | None = None
    adversarial_completeness_definition: str | None = None
    evidence_input_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExperimentRunRecord:
    descriptor: ExperimentRunDescriptor
    inputs: tuple[ExperimentInput, ...]
    executions: tuple[SolverExecution, ...]
    classifications: tuple[SolverClassification, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "descriptor": self.descriptor.to_dict(),
            "inputs": [asdict(row) for row in self.inputs],
            "executions": [asdict(row) for row in self.executions],
            "classifications": [asdict(row) for row in self.classifications],
        }


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def execution_hash(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def validate_descriptor(descriptor: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_ERD_FIELDS - set(descriptor))
    if missing:
        raise ExperimentContractError(f"ERD missing required fields: {missing}")
    if descriptor["label_schema_version"] != LABEL_SCHEMA_VERSION:
        raise ExperimentContractError(
            f"unsupported label_schema_version: {descriptor['label_schema_version']}"
        )
    if not isinstance(descriptor["execution_hash"], str) or len(descriptor["execution_hash"]) != 64:
        raise ExperimentContractError("execution_hash must be a sha256 hex string")
    if not descriptor["failure_class_version"]:
        raise ExperimentContractError("failure_class_version must be non-empty")
    try:
        from doctor.adversarial.probe_registry import ProbeRegistryError, load_probe_registry

        load_probe_registry().validate_binding(descriptor)
    except ProbeRegistryError as exc:
        raise ExperimentContractError(str(exc)) from exc


def validate_classifications(classifications: list[dict[str, Any]]) -> None:
    for row in classifications:
        label = row.get("label")
        if label not in VALID_LABELS:
            raise ExperimentContractError(f"invalid classification label: {label}")
        failure_class = row.get("failure_class")
        mechanism = row.get("mechanism")
        evidence = row.get("evidence_input_ids") or []
        if label == "BROKEN" and not evidence:
            raise ExperimentContractError(f"BROKEN row lacks evidence: {row.get('solver_id')}")
        if label == "SURVIVOR" and (not failure_class or not mechanism):
            raise ExperimentContractError(
                f"SURVIVOR row lacks failure class or mechanism: {row.get('solver_id')}"
            )
        if label == "UNKNOWN" and (failure_class or mechanism):
            raise ExperimentContractError(
                f"UNKNOWN row must not carry failure class/mechanism: {row.get('solver_id')}"
            )
        if row.get("promotes_correctness"):
            raise ExperimentContractError("correctness promotion is outside OPT-C label schema")


def validate_run_record(record: dict[str, Any]) -> None:
    validate_descriptor(record.get("descriptor", {}))
    validate_classifications(record.get("classifications", []))


def validate_provenance(result: dict[str, Any]) -> None:
    provenance = result.get("k_provenance")
    if provenance is None:
        raise ExperimentContractError("result missing k_provenance block")
    missing = sorted(REQUIRED_PROVENANCE_FIELDS - set(provenance))
    if missing:
        raise ExperimentContractError(f"k_provenance missing required fields: {missing}")
    if not isinstance(provenance.get("evaluated_at"), str) or not provenance["evaluated_at"]:
        raise ExperimentContractError("k_provenance.evaluated_at must be a non-empty string")
    if not isinstance(provenance.get("oracle_version"), str) or not provenance["oracle_version"]:
        raise ExperimentContractError("k_provenance.oracle_version must be a non-empty string")


def assert_no_posthoc_relabeling(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> None:
    previous_descriptor = previous["descriptor"]
    current_descriptor = current["descriptor"]
    previous_versions = (
        previous_descriptor["label_schema_version"],
        previous_descriptor["failure_class_version"],
    )
    current_versions = (
        current_descriptor["label_schema_version"],
        current_descriptor["failure_class_version"],
    )
    previous_labels = _labels_by_solver(previous.get("classifications", []))
    current_labels = _labels_by_solver(current.get("classifications", []))
    changed = {
        solver_id
        for solver_id, label in previous_labels.items()
        if solver_id in current_labels and current_labels[solver_id] != label
    }
    if changed and previous_versions == current_versions:
        raise ExperimentContractError(
            "classification labels changed without label_schema_version or "
            f"failure_class_version bump: {sorted(changed)}"
        )
    _assert_unknown_promotion_rule(previous, current)


def _labels_by_solver(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {str(row["solver_id"]): str(row["label"]) for row in rows}


def _assert_unknown_promotion_rule(previous: dict[str, Any], current: dict[str, Any]) -> None:
    previous_by_solver = {str(row["solver_id"]): row for row in previous.get("classifications", [])}
    current_by_solver = {str(row["solver_id"]): row for row in current.get("classifications", [])}
    for solver_id, old_row in previous_by_solver.items():
        if old_row.get("label") != "UNKNOWN" or solver_id not in current_by_solver:
            continue
        new_row = current_by_solver[solver_id]
        if new_row.get("label") == "UNKNOWN":
            continue
        if not new_row.get("adversarial_completeness_definition"):
            raise ExperimentContractError(
                f"UNKNOWN cannot be upgraded without adversarial completeness definition: {solver_id}"
            )


def load_run_record(path: str | Path) -> dict[str, Any]:
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_run_record(record)
    return record

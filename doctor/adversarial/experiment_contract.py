from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest


LABEL_SCHEMA_VERSION = "1.0.0"

_REGISTERED_PROBE_SETS = frozenset({
    "lc45-six-manifold-probe-set-v1",
})


class ExperimentContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExperimentInput:
    input_id: str
    manifold_id: str
    payload: dict[str, Any]
    expected: int


@dataclass(frozen=True)
class SolverClassification:
    solver_id: str
    label: str
    failure_class: str | None = None
    mechanism: str | None = None
    evidence_input_ids: tuple[str, ...] = ()


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def execution_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(record).encode()).hexdigest()


REQUIRED_PROVENANCE_FIELDS: tuple[str, ...] = ()


def validate_provenance(record: dict[str, Any]) -> list[str]:
    return []


def validate_run_record(record: dict[str, Any]) -> None:
    descriptor = record.get("descriptor")
    if not descriptor:
        raise ExperimentContractError("record missing descriptor")

    required = {"problem_id", "solver_set_id", "manifold_set_id",
                "probe_set_id", "label_schema_version", "execution_hash",
                "failure_class_version"}
    missing = required - set(descriptor)
    if missing:
        raise ExperimentContractError(f"descriptor missing required fields: {missing}")

    probe_set_id = descriptor.get("probe_set_id", "")
    if probe_set_id not in _REGISTERED_PROBE_SETS:
        raise ExperimentContractError(f"unknown probe_set_id: {probe_set_id!r}")

    for entry in record.get("classifications", []):
        label = entry.get("label", "")
        if label == "BROKEN":
            if not entry.get("evidence_input_ids"):
                raise ExperimentContractError(
                    f"BROKEN row lacks evidence for solver_id={entry.get('solver_id')}"
                )
        elif label == "SURVIVOR":
            if not entry.get("failure_class") or not entry.get("mechanism"):
                raise ExperimentContractError(
                    f"SURVIVOR row lacks failure_class/mechanism for solver_id={entry.get('solver_id')}"
                )
        elif label == "UNKNOWN":
            if entry.get("failure_class"):
                raise ExperimentContractError(
                    f"UNKNOWN row must not carry failure_class for solver_id={entry.get('solver_id')}"
                )


def assert_no_posthoc_relabeling(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> None:
    prev_labels = {
        e["solver_id"]: e["label"]
        for e in previous.get("classifications", [])
    }
    curr_labels = {
        e["solver_id"]: e["label"]
        for e in current.get("classifications", [])
    }
    prev_version = previous["descriptor"]["failure_class_version"]
    curr_version = current["descriptor"]["failure_class_version"]

    labels_changed = any(
        prev_labels.get(sid) != curr_labels.get(sid)
        for sid in set(prev_labels) | set(curr_labels)
    )

    if labels_changed and prev_version == curr_version:
        raise ExperimentContractError(
            "labels changed without version bump in failure_class_version"
        )

    for sid in set(prev_labels) & set(curr_labels):
        if prev_labels[sid] == "UNKNOWN" and curr_labels[sid] != "UNKNOWN":
            curr_entry = next(
                e for e in current.get("classifications", []) if e["solver_id"] == sid
            )
            if not curr_entry.get("adversarial_completeness_definition"):
                raise ExperimentContractError(
                    f"UNKNOWN cannot be upgraded without adversarial_completeness_definition "
                    f"for solver_id={sid}"
                )


def load_run_record(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    validate_run_record(record)
    return record


def _record(*, failure_class_version: str = "lc45-optc-failure-classes-v1", label: str = "UNKNOWN"):
    return {
        "descriptor": {
            "problem_id": "lc45",
            "solver_set_id": "lc45-llm-population-v1",
            "manifold_set_id": "lc45-six-manifold-probe-set-v1",
            "probe_set_id": "lc45-six-manifold-probe-set-v1",
            "label_schema_version": LABEL_SCHEMA_VERSION,
            "execution_hash": execution_hash({"inputs": ["i1"], "solvers": ["s1"]}),
            "failure_class_version": failure_class_version,
        },
        "inputs": [
            {
                "input_id": "i1",
                "manifold_id": "m1",
                "payload": {"nums": [2, 3, 1, 1, 4]},
                "expected": 2,
            }
        ],
        "executions": [
            {
                "solver_id": "s1",
                "input_id": "i1",
                "observed": 2,
                "expected": 2,
                "passed": True,
                "failure_record": None,
            }
        ],
        "classifications": [
            {
                "solver_id": "s1",
                "label": label,
                "failure_class": None,
                "mechanism": None,
                "adversarial_completeness_definition": None,
                "evidence_input_ids": [],
            }
        ],
    }


def test_valid_unknown_record_passes():
    validate_run_record(_record())


def test_descriptor_requires_erd_fields():
    record = _record()
    del record["descriptor"]["failure_class_version"]
    with pytest.raises(ExperimentContractError, match="missing required fields"):
        validate_run_record(record)


def test_descriptor_requires_registered_probe_set():
    record = _record()
    record["descriptor"]["probe_set_id"] = "missing-probe-set"
    with pytest.raises(ExperimentContractError, match="unknown probe_set_id"):
        validate_run_record(record)


def test_broken_requires_evidence():
    record = _record(label="BROKEN")
    with pytest.raises(ExperimentContractError, match="BROKEN row lacks evidence"):
        validate_run_record(record)


def test_survivor_requires_failure_class_and_mechanism():
    record = _record(label="SURVIVOR")
    with pytest.raises(ExperimentContractError, match="SURVIVOR row lacks"):
        validate_run_record(record)


def test_unknown_cannot_carry_failure_class():
    record = _record()
    record["classifications"][0]["failure_class"] = "search_resource_truncation"
    with pytest.raises(ExperimentContractError, match="UNKNOWN row must not carry"):
        validate_run_record(record)


def test_relabeling_requires_version_bump():
    previous = _record(label="UNKNOWN")
    current = _record(label="BROKEN")
    current["classifications"][0]["evidence_input_ids"] = ["i1"]
    with pytest.raises(ExperimentContractError, match="labels changed without"):
        assert_no_posthoc_relabeling(previous, current)


def test_unknown_upgrade_requires_adversarial_completeness_definition_even_with_version_bump():
    previous = _record(label="UNKNOWN")
    current = _record(label="BROKEN", failure_class_version="lc45-optc-failure-classes-v2")
    current["classifications"][0]["evidence_input_ids"] = ["i1"]
    with pytest.raises(ExperimentContractError, match="UNKNOWN cannot be upgraded"):
        assert_no_posthoc_relabeling(previous, current)


def test_unknown_upgrade_allowed_with_version_bump_and_completeness_definition():
    previous = _record(label="UNKNOWN")
    current = _record(label="BROKEN", failure_class_version="lc45-optc-failure-classes-v2")
    current["classifications"][0]["evidence_input_ids"] = ["i1"]
    current["classifications"][0][
        "adversarial_completeness_definition"
    ] = "bounded exhaustive check over declared LC45 OPT-C surface"
    assert_no_posthoc_relabeling(previous, current)


def test_checked_in_experiment_descriptors_validate():
    descriptor_dir = Path("data/experiment_run_descriptors")
    paths = sorted(descriptor_dir.glob("*.json"))
    assert paths
    for path in paths:
        load_run_record(path)

from __future__ import annotations

from pathlib import Path

import pytest

from doctor.adversarial.experiment_contract import (
    LABEL_SCHEMA_VERSION,
    ExperimentContractError,
    assert_no_posthoc_relabeling,
    execution_hash,
    load_run_record,
    validate_run_record,
)


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

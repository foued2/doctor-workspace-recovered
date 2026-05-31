from __future__ import annotations

import json
from pathlib import Path

import pytest

from doctor.v03.hash_utils import hash_json_object, hash_manifest_chain
from doctor.v03.manifest_schema import ManifestValidationError, validate_manifest
from doctor.v03.stop_rules import V03HardStop, V03StopState, hard_stop
from doctor.v03.validation_skeleton import BuildNotApprovedError, run_hidden_validation_once


TEMPLATE_DIR = Path("manifests/v03/templates")


def test_templates_parse_as_json() -> None:
    for path in TEMPLATE_DIR.glob("*.template.json"):
        with path.open(encoding="utf-8") as handle:
            json.load(handle)


def test_schema_validator_rejects_missing_required_fields() -> None:
    manifest = {
        "schema_version": "1.0.0",
        "protocol_version": "v0.3",
        "manifest_kind": "benchmark_pool",
        "repo_commit": "abc123",
    }
    with pytest.raises(ManifestValidationError, match="missing required fields"):
        validate_manifest(manifest)


def test_schema_validator_rejects_scoreable_invalid_perturbations() -> None:
    manifest = {
        "schema_version": "1.0.0",
        "protocol_version": "v0.3",
        "manifest_kind": "perturbation",
        "repo_commit": "abc123",
        "entries": [
            {
                "problem_id": "P",
                "perturbation_id": "bad",
                "perturbation_class": "invalid",
                "perturbation_hash": "h",
                "scoreable": True,
            }
        ],
    }
    with pytest.raises(ManifestValidationError, match="cannot score"):
        validate_manifest(manifest)


def test_schema_validator_requires_proof_card_for_output_preserving() -> None:
    manifest = {
        "schema_version": "1.0.0",
        "protocol_version": "v0.3",
        "manifest_kind": "perturbation",
        "repo_commit": "abc123",
        "entries": [
            {
                "problem_id": "P",
                "perturbation_id": "preserve",
                "perturbation_class": "output_preserving",
                "perturbation_hash": "h",
                "scoreable": True,
            }
        ],
    }
    with pytest.raises(ManifestValidationError, match="requires proof_card_reference"):
        validate_manifest(manifest)


def test_hidden_sealed_entries_cannot_expose_raw_content() -> None:
    manifest = {
        "schema_version": "1.0.0",
        "protocol_version": "v0.3",
        "manifest_kind": "benchmark_pool",
        "repo_commit": "abc123",
        "sealed": True,
        "hidden_opened": False,
        "entries": [
            {
                "problem_id": "P",
                "family_id": "dp",
                "split_id": "hidden",
                "problem_definition_hash": "h1",
                "generator_id": "g",
                "generator_hash": "h2",
                "oracle_id": "o",
                "oracle_hash": "h3",
                "comparator_id": "c",
                "comparator_hash": "h4",
                "problem_definition": "raw hidden text",
            }
        ],
    }
    with pytest.raises(ManifestValidationError, match="exposes sealed content"):
        validate_manifest(manifest)


def test_stop_rules_are_hard_errors() -> None:
    with pytest.raises(V03HardStop, match=V03StopState.HIDDEN_ORACLE_DISAGREEMENT.value):
        hard_stop(V03StopState.HIDDEN_ORACLE_DISAGREEMENT, "duel mismatch")


def test_hidden_validation_refuses_without_separate_approval() -> None:
    with pytest.raises(BuildNotApprovedError, match="blocked pending separate explicit approval"):
        run_hidden_validation_once()


def test_hash_json_object_is_stable_under_key_order_changes() -> None:
    left = {"b": [2, 1], "a": {"z": 3}}
    right = {"a": {"z": 3}, "b": [2, 1]}
    assert hash_json_object(left) == hash_json_object(right)


def test_manifest_chain_hash_changes_if_content_changes() -> None:
    first = [{"manifest_kind": "solver", "entries": [{"solver_id": "a"}]}]
    second = [{"manifest_kind": "solver", "entries": [{"solver_id": "b"}]}]
    assert hash_manifest_chain(first) != hash_manifest_chain(second)


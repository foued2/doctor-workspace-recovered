from __future__ import annotations

import pytest

from doctor.adversarial.bimaristan_schema import RelationConstraint
from doctor.adversarial.oracle_evaluator import LC11OracleEvaluator, OracleCeilingError, evaluation_surface
from doctor.adversarial.synthesizer_contract import GenerationStrategy, SynthesizedCandidate


def _candidate(array, generator_id="test"):
    return SynthesizedCandidate(tuple(array), (), GenerationStrategy.INTERIOR_SPIKE, generator_id)


def test_known_good_lc11_array_answer_49():
    candidate = _candidate([1, 8, 6, 2, 5, 4, 8, 3, 7])
    surface = evaluation_surface(candidate, (RelationConstraint("max_area", "==", "49"),), "test")
    result = LC11OracleEvaluator().evaluate(surface)
    values = {value.symbol_name: value.value for value in result.oracle_dependent_values}
    assert values["global_max_pair_area"] == 49
    assert result.passed
    assert result.violated_predicate_ids == ()


def test_known_fail_move_taller_boundary_predicate():
    candidate = _candidate([3, 1, 4, 2, 1], "short_left_tall_right_hidden_left_partner")
    predicate = RelationConstraint("hidden_partner_area", ">", "current_area")
    result = LC11OracleEvaluator().evaluate(evaluation_surface(candidate, (predicate,), candidate.provenance_generator_id))
    assert not result.passed
    assert result.violated_predicate_ids == ("short_left_tall_right_hidden_left_partner:validation_predicates[0]",)


def test_oracle_ceiling_error_for_large_array():
    candidate = _candidate([1] * 1001)
    with pytest.raises(OracleCeilingError):
        LC11OracleEvaluator().evaluate(evaluation_surface(candidate, (), "test"))


def test_input_array_is_not_modified_after_evaluation():
    source = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    candidate = _candidate(source)
    LC11OracleEvaluator().evaluate(evaluation_surface(candidate, (RelationConstraint("max_area", "==", "49"),), "test"))
    assert source == [1, 8, 6, 2, 5, 4, 8, 3, 7]
    assert candidate.raw_array == (1, 8, 6, 2, 5, 4, 8, 3, 7)
artial"
            ],
            "C": [
              "partial",
              "partial"
            ]
          }
        },
        {
          "family_id": "OP-SEM-177",
          "generator": "ops_sheet",
          "conflict_type": "semantic_ambiguity",
          "case_kind": "compromise",
          "density": 3,
          "nesting_depth": 3,
          "dependency_depth": 3,
          "oracle_label": "partial",
          "majority_label": "partial",
          "outputs_by_layer": {
            "A": [
              "partial",
              "partial"
            ],
            "B": [
              "partial",
              "partial"
            ],
            "C": [
              "partial",
              "partial"
            ]
          }
        },
        {
          "family_id": "IN-SEM-077",
          "generator": "incident_report",
          "conflict_type": "semantic_ambiguity",
          "case_kind": "undecidable",
          "density": 1,
          "nesting_depth": 1,
          "dependency_depth": 1,
          "oracle_label": "undefined",
          "majority_label": "partial",
          "outputs_by_layer": {
            "A": [
              "partial",
              "partial"
            ],
            "B": [
              "partial",
              "partial"
            ],
            "C": [
              "partial",
              "partial"
            ]
          }
        },
        {
          "family_id": "IN-MUT-030",
          "generator": "incident_report",
          "conflict_type": "mutual_exclusion",
          "case_kind": "undecidable",
          "density": 2,
          "nesting_depth": 2,
          "dependency_depth": 2,
          "oracle_label": "undefined",
          "majority_label": "partial",
          "outputs_by_layer": {
            "A": [
              "partial",
              "partial"
            ],
            "B": [
              "partial",
              "partial"
            ],
            "C": [
       from __future__ import annotations

import json
from pathlib import Path

import pytest

from doctor.adversarial.probe_registry import (
    ProbeRegistryError,
    compute_probe_set_hash,
    load_probe_registry,
)


def test_probe_registry_loads_checked_in_probe_sets():
    registry = load_probe_registry()
    assert registry.probe_set_ids() == [
        "lc322-closed-six-family-basis-v1",
        "lc322-expanded-eight-family-basis-v1",
        "lc322-search-resource-truncation-v1",
        "lc45-six-manifold-probe-set-v1",
    ]


def test_probe_set_hashes_are_content_bound():
    for path in Path("doctor/adversarial/probe_sets").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["version_hash"] == compute_probe_set_hash(data)


def test_probe_registry_validates_descriptor_binding():
    registry = load_probe_registry()
    registry.validate_binding(
        {
            "problem_id": "lc45",
            "manifold_set_id": "lc45-six-manifold-probe-set-v1",
            "probe_set_id": "lc45-six-manifold-probe-set-v1",
        }
    )
    with pytest.raises(ProbeRegistryError, match="manifold_set_id"):
        registry.validate_binding(
            {
                "problem_id": "lc45",
                "manifold_set_id": "wrong",
                "probe_set_id": "lc45-six-manifold-probe-set-v1",
            }
        )

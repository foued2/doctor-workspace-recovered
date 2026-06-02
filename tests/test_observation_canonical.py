"""Property tests for the canonical Observation form.

Asserts the three design invariants from `doctor/core/observation.py`:

  A. Layer coverage: brute_force / symbol / schema all populate Observation.
  B. Layer visibility: evaluation_layer is required and explicit.
  C. No implicit cross-problem comparability: two observations from
     different problem_ids are not equivalent just because their
     canonical_form is identical. Downstream code must declare its
     equivalence assumptions.

These tests pin the data model of Observation. They do NOT assert that
production code uses Observation — only that when Observation IS used,
the invariants hold. The test-locality of Observation is a separate
architectural commitment, recorded in `doctor/core/observation.py`.
"""
from __future__ import annotations

import os
import sys
import unittest

os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.core.observation import (
    EVALUATION_LAYERS,
    Observation,
    from_brute_force,
    from_schema,
    from_symbol,
)


class TestPropertyA_LayerCoverage(unittest.TestCase):
    def test_brute_force_populates_observation(self):
        obs = from_brute_force(
            problem_id="lc45",
            candidate_id="cand_001",
            projection_level=1,
            classification="SUCCESS",
            seed=20260602,
            sample_size=1000,
        )
        self.assertEqual(obs.evaluation_layer, "brute_force")
        self.assertEqual(obs.canonical_form, ("SUCCESS",))

    def test_symbol_populates_observation(self):
        obs = from_symbol(
            problem_id="lc45",
            candidate_id="cand_001",
            projection_level=2,
            symbol_name="naive_diverges",
            symbol_value=True,
            passed=True,
            seed=20260602,
            sample_size=1000,
        )
        self.assertEqual(obs.evaluation_layer, "symbol")
        self.assertEqual(obs.canonical_form, ("naive_diverges", "True", "PASS"))

    def test_schema_populates_observation(self):
        obs = from_schema(
            problem_id="lc11",
            candidate_id="cand_001",
            projection_level=3,
            schema_id="lc11_schema_v1",
            violated=("predicate_a", "predicate_b"),
            seed=20260602,
            sample_size=1000,
        )
        self.assertEqual(obs.evaluation_layer, "schema")
        self.assertEqual(obs.canonical_form, ("lc11_schema_v1", ("predicate_a", "predicate_b")))

    def test_all_three_layers_supported(self):
        self.assertEqual(EVALUATION_LAYERS, frozenset({"brute_force", "symbol", "schema"}))


class TestPropertyB_LayerVisibility(unittest.TestCase):
    def test_evaluation_layer_is_required_field(self):
        obs = from_brute_force(
            problem_id="lc45", candidate_id="c", projection_level=1,
            classification="X", seed=1, sample_size=1,
        )
        self.assertIn("evaluation_layer", obs.__dataclass_fields__)

    def test_evaluation_layer_rejects_unknown_value(self):
        with self.assertRaises(ValueError):
            Observation(
                problem_id="lc45",
                candidate_id="c",
                projection_level=1,
                evaluation_layer="magic_layer",
                canonical_form=("X",),
                seed=1,
                sample_size=1,
            )

    def test_evaluation_layer_is_hashable(self):
        obs1 = from_brute_force(
            problem_id="lc45", candidate_id="c", projection_level=1,
            classification="SUCCESS", seed=1, sample_size=1,
        )
        obs2 = from_symbol(
            problem_id="lc45", candidate_id="c", projection_level=1,
            symbol_name="s", symbol_value=True, passed=True,
            seed=1, sample_size=1,
        )
        self.assertEqual(obs1.evaluation_layer, "brute_force")
        self.assertEqual(obs2.evaluation_layer, "symbol")
        self.assertNotEqual(obs1, obs2)

    def test_same_canonical_form_different_layers_not_equal(self):
        brute = from_brute_force(
            problem_id="lc45", candidate_id="c", projection_level=1,
            classification="SUCCESS", seed=1, sample_size=1,
        )
        symbol = from_symbol(
            problem_id="lc45", candidate_id="c", projection_level=1,
            symbol_name="X", symbol_value="SUCCESS", passed=True,
            seed=1, sample_size=1,
        )
        self.assertNotEqual(brute, symbol)
        self.assertNotEqual(brute.canonical_form, symbol.canonical_form)


class TestPropertyC_NoImplicitCrossProblemComparability(unittest.TestCase):
    def test_different_problem_ids_with_same_canonical_form_are_not_fused(self):
        brute_lc45 = from_brute_force(
            problem_id="lc45", candidate_id="c", projection_level=1,
            classification="SUCCESS", seed=1, sample_size=1,
        )
        brute_lc322 = from_brute_force(
            problem_id="lc322", candidate_id="c", projection_level=1,
            classification="SUCCESS", seed=1, sample_size=1,
        )
        self.assertNotEqual(brute_lc45, brute_lc322)
        self.assertEqual(brute_lc45.canonical_form, brute_lc322.canonical_form)

    def test_no_equivalent_to_or_compares_to_method(self):
        obs = from_brute_force(
            problem_id="lc45", candidate_id="c", projection_level=1,
            classification="SUCCESS", seed=1, sample_size=1,
        )
        self.assertFalse(hasattr(obs, "equivalent_to"))
        self.assertFalse(hasattr(obs, "compares_to"))
        self.assertFalse(hasattr(obs, "is_compatible_with"))

    def test_observation_is_hashable_by_full_content(self):
        obs_set = {
            from_brute_force(
                problem_id="lc45", candidate_id="c1", projection_level=1,
                classification="SUCCESS", seed=1, sample_size=1,
            ),
            from_brute_force(
                problem_id="lc45", candidate_id="c2", projection_level=1,
                classification="SUCCESS", seed=1, sample_size=1,
            ),
            from_brute_force(
                problem_id="lc322", candidate_id="c1", projection_level=1,
                classification="SUCCESS", seed=1, sample_size=1,
            ),
        }
        self.assertEqual(len(obs_set), 3)


class TestDataclassInvariants(unittest.TestCase):
    def test_projection_level_must_be_1_to_4(self):
        for bad in (0, 5, -1):
            with self.assertRaises(ValueError):
                Observation(
                    problem_id="p", candidate_id="c", projection_level=bad,
                    evaluation_layer="brute_force", canonical_form=("X",),
                    seed=1, sample_size=1,
                )

    def test_canonical_form_must_be_tuple(self):
        with self.assertRaises(TypeError):
            Observation(
                problem_id="p", candidate_id="c", projection_level=1,
                evaluation_layer="brute_force", canonical_form="not a tuple",
                seed=1, sample_size=1,
            )

    def test_candidate_id_must_be_nonempty(self):
        with self.assertRaises(ValueError):
            Observation(
                problem_id="p", candidate_id="", projection_level=1,
                evaluation_layer="brute_force", canonical_form=("X",),
                seed=1, sample_size=1,
            )

    def test_sample_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            Observation(
                problem_id="p", candidate_id="c", projection_level=1,
                evaluation_layer="brute_force", canonical_form=("X",),
                seed=1, sample_size=0,
            )


if __name__ == "__main__":
    unittest.main()

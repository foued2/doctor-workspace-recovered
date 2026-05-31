from __future__ import annotations

import operator
from dataclasses import replace

import pytest

from doctor.adversarial.perturbation_validity import (
    PerturbationClass,
    PerturbationDeclaration,
    SCORING_ALLOWED_CLASSES,
    PERTURBATION_VALIDITY_REGISTRY,
    get_declaration,
    is_scoring_allowed,
    validate,
)
from doctor.adversarial.ingestion_gate import (
    ingestion_gate,
    _compute_per_solver_stability,
)
from doctor.adversarial.experiment_runner import PerturbationScoringBlocked, evaluate_perturbed


# ── B1: PerturbationClass taxonomy ──────────────────────────────────────────

class TestPerturbationClassTaxonomy:
    def test_all_four_classes_exist(self):
        assert PerturbationClass.OUTPUT_PRESERVING.value == "output_preserving"
        assert PerturbationClass.OUTPUT_CHANGING_PREDICTABLE.value == "output_changing_predictable"
        assert PerturbationClass.INVALID.value == "invalid"
        assert PerturbationClass.UNKNOWN_UNTIL_ORACLE_RECOMPUTE.value == "unknown_until_oracle_recompute"

    def test_scoring_allowed_classes(self):
        assert PerturbationClass.OUTPUT_PRESERVING in SCORING_ALLOWED_CLASSES
        assert PerturbationClass.OUTPUT_CHANGING_PREDICTABLE in SCORING_ALLOWED_CLASSES
        assert PerturbationClass.INVALID not in SCORING_ALLOWED_CLASSES
        assert PerturbationClass.UNKNOWN_UNTIL_ORACLE_RECOMPUTE not in SCORING_ALLOWED_CLASSES

    def test_every_registry_entry_has_perturbation_class(self):
        for key, decl in PERTURBATION_VALIDITY_REGISTRY.items():
            assert isinstance(decl, PerturbationDeclaration), f"{key} is not a PerturbationDeclaration"
            assert isinstance(decl.perturbation_class, PerturbationClass), f"{key} missing perturbation_class"

    def test_every_output_preserving_entry_has_proof_card(self):
        for key, decl in PERTURBATION_VALIDITY_REGISTRY.items():
            if decl.perturbation_class == PerturbationClass.OUTPUT_PRESERVING:
                assert decl.proof_card_id is not None, f"{key} is OUTPUT_PRESERVING but has no proof_card_id"
                assert len(decl.proof_card_id) > 0, f"{key} has empty proof_card_id"

    def test_validate_accepts_valid_entry(self):
        validate("LC322", "multiset_invariant")

    def test_validate_rejects_undeclared(self):
        with pytest.raises(ValueError, match="undeclared perturbation validity"):
            validate("LC999", "nonexistent")

    def test_is_scoring_allowed_for_output_preserving(self):
        assert is_scoring_allowed("LC322", "multiset_invariant") is True

    def test_get_declaration_unknown_returns_correct_class(self):
        for key, decl in PERTURBATION_VALIDITY_REGISTRY.items():
            if decl.perturbation_class == PerturbationClass.OUTPUT_PRESERVING:
                assert get_declaration(key[0], key[1]) is decl
                break


# ── B1: experiment_runner — evaluate_perturbed ──────────────────────────────

class TestEvaluatePerturbed:
    def test_output_preserving_with_proof_card_succeeds(self):
        def oracle(x):
            return sum(x)
        result = evaluate_perturbed(
            problem_id="LC322",
            perturbation_family="multiset_invariant",
            solver=lambda x: sum(x),
            base_input={"coins": [1, 2, 5], "amount": 11},
            perturbed_input={"coins": [5, 1, 2], "amount": 11},
            oracle=oracle,
            apply_solver=lambda s, t: s(t["coins"]),
            apply_oracle=lambda o, t: o(t["coins"]),
        )
        assert result["perturbation_class"] == "output_preserving"
        assert result["proof_card_id"] is not None
        assert result["expected_base"] == result["expected_perturbed"]

    def test_undeclared_perturbation_raises(self):
        def oracle(x):
            return 0
        with pytest.raises(ValueError, match="undeclared perturbation"):
            evaluate_perturbed(
                problem_id="LC999",
                perturbation_family="nonexistent",
                solver=lambda x: 0,
                base_input={},
                perturbed_input={},
                oracle=oracle,
                apply_solver=lambda s, t: 0,
                apply_oracle=lambda o, t: 0,
            )

    def test_invalid_class_blocks_scoring(self):
        decl = PerturbationDeclaration(
            perturbation_class=PerturbationClass.INVALID,
            justification="test",
            proof_card_id=None,
        )
        import doctor.adversarial.perturbation_validity as pv
        orig = pv.PERTURBATION_VALIDITY_REGISTRY.get(("TEST", "invalid_test"))
        pv.PERTURBATION_VALIDITY_REGISTRY[("TEST", "invalid_test")] = decl
        try:
            with pytest.raises(PerturbationScoringBlocked, match="scoring blocked"):
                evaluate_perturbed(
                    problem_id="TEST",
                    perturbation_family="invalid_test",
                    solver=lambda x: 0,
                    base_input={},
                    perturbed_input={},
                    oracle=lambda x: 0,
                    apply_solver=lambda s, t: 0,
                    apply_oracle=lambda o, t: 0,
                )
        finally:
            if orig is not None:
                pv.PERTURBATION_VALIDITY_REGISTRY[("TEST", "invalid_test")] = orig
            else:
                del pv.PERTURBATION_VALIDITY_REGISTRY[("TEST", "invalid_test")]


# ── B1: ingestion gate — oracle recomputation ───────────────────────────────

class TestIngestionGateOracleRecomputation:
    def test_perturbed_oracle_is_recomputed(self):
        call_log: list[str] = []

        def tracking_oracle(t: dict) -> int:
            call_log.append(t["_label"])
            return sum(t["nums"])

        def solver(nums: list[int]) -> int:
            return sum(nums)

        def apply_solver(s, t):
            return s(t["nums"])

        def apply_oracle(o, t):
            return o(t)

        def perturb_strategy(t, n):
            nums = t["nums"]
            return [{"nums": list(reversed(nums)), "_label": f"perturbed_{t['_label']}"}]

        result = ingestion_gate(
            problem_id="LC322",
            reference_tests=[
                {"nums": [1, 2, 3], "_label": "base_1"},
                {"nums": [4, 5, 6], "_label": "base_2"},
            ],
            solvers=[solver],
            oracle=tracking_oracle,
            apply_solver=apply_solver,
            apply_oracle=apply_oracle,
            perturbation_strategy=perturb_strategy,
            perturbation_family="multiset_invariant",
            perturbation_samples=1,
        )

        oracle_calls_for_perturbed = [c for c in call_log if c.startswith("perturbed_")]
        assert len(oracle_calls_for_perturbed) == 2, (
            f"expected 2 oracle calls for perturbed inputs, got {len(oracle_calls_for_perturbed)}: {call_log}"
        )

    def test_output_preserving_stability_unchanged(self):
        def oracle(t):
            return sum(t["nums"])

        def solver(nums):
            return sum(nums)

        def apply_solver(s, t):
            return s(t["nums"])

        def apply_oracle(o, t):
            return o(t)

        def perturb_strategy(t, n):
            return [{"nums": list(reversed(t["nums"]))}]

        result = ingestion_gate(
            problem_id="LC322",
            reference_tests=[{"nums": [1, 2, 3]}],
            solvers=[solver],
            oracle=oracle,
            apply_solver=apply_solver,
            apply_oracle=apply_oracle,
            perturbation_strategy=perturb_strategy,
            perturbation_family="multiset_invariant",
            perturbation_samples=1,
        )
        assert result["ingest"] is True

    def test_ingestion_blocked_for_unknown_class(self):
        import doctor.adversarial.perturbation_validity as pv
        unknown_decl = pv.PerturbationDeclaration(
            perturbation_class=PerturbationClass.UNKNOWN_UNTIL_ORACLE_RECOMPUTE,
            justification="test",
            proof_card_id=None,
        )
        orig = pv.PERTURBATION_VALIDITY_REGISTRY.get(("TEST", "unknown_family"))
        pv.PERTURBATION_VALIDITY_REGISTRY[("TEST", "unknown_family")] = unknown_decl
        try:
            with pytest.raises(PerturbationScoringBlocked):
                ingestion_gate(
                    problem_id="TEST",
                    reference_tests=[{"nums": [1, 2, 3]}],
                    solvers=[lambda x: 0],
                    oracle=lambda x: 0,
                    apply_solver=lambda s, t: 0,
                    apply_oracle=lambda o, t: 0,
                    perturbation_strategy=lambda t, n: [{"nums": [0]}],
                    perturbation_family="unknown_family",
                    perturbation_samples=1,
                )
        finally:
            if orig is not None:
                pv.PERTURBATION_VALIDITY_REGISTRY[("TEST", "unknown_family")] = orig
            else:
                del pv.PERTURBATION_VALIDITY_REGISTRY[("TEST", "unknown_family")]


# ── B1: _compute_per_solver_stability with perturbed oracles ────────────────

class TestPerSolverStability:
    def test_compares_against_perturbed_oracle(self):
        baseline = [{0: 5, 1: 10}]
        perturbed = [[{0: 5, 1: 10}]]
        perturbed_oracles = [[5]]  # perturbed oracle matches base
        stability = _compute_per_solver_stability(baseline, perturbed, perturbed_oracles)
        assert stability["solver_0"] == 1.0

    def test_perturbed_oracle_mismatch_detected(self):
        baseline = [{0: 5}]
        perturbed = [[{0: 5}]]  # solver output unchanged
        perturbed_oracles = [[10]]  # but oracle says answer changed
        stability = _compute_per_solver_stability(baseline, perturbed, perturbed_oracles)
        assert stability["solver_0"] == 0.0

    def test_empty_inputs(self):
        assert _compute_per_solver_stability([], [], []) == {}


# ── B2: typed comparator abstraction ────────────────────────────────────────

class TestBoolIntRejection:
    def test_exact_int_rejects_bool(self):
        from doctor.adversarial.comparators import ExactIntComparator, ComparatorTypeMismatch
        c = ExactIntComparator()
        with pytest.raises(ComparatorTypeMismatch):
            c.compare(1, True)
        with pytest.raises(ComparatorTypeMismatch):
            c.compare(True, 1)

    def test_exact_int_accepts_int(self):
        from doctor.adversarial.comparators import ExactIntComparator
        c = ExactIntComparator()
        result = c.compare(42, 42)
        assert result.equal is True
        assert result.type_match is True

    def test_exact_int_inequal(self):
        from doctor.adversarial.comparators import ExactIntComparator
        c = ExactIntComparator()
        result = c.compare(1, 2)
        assert result.equal is False

    def test_exact_int_rejects_non_int(self):
        from doctor.adversarial.comparators import ExactIntComparator
        c = ExactIntComparator()
        result = c.compare("1", 1)
        assert result.equal is False
        assert result.type_match is False


class TestComparators:
    def test_exact_bool(self):
        from doctor.adversarial.comparators import ExactBoolComparator
        c = ExactBoolComparator()
        assert c.compare(True, True).equal is True
        assert c.compare(False, False).equal is True
        assert c.compare(True, False).equal is False
        result = c.compare(1, True)
        assert result.equal is False
        assert result.type_match is False

    def test_exact_string(self):
        from doctor.adversarial.comparators import ExactStringComparator
        c = ExactStringComparator()
        assert c.compare("hello", "hello").equal is True
        assert c.compare("hello", "world").equal is False
        result = c.compare("hello", 42)
        assert result.equal is False
        assert result.type_match is False

    def test_exact_list(self):
        from doctor.adversarial.comparators import ExactListComparator
        c = ExactListComparator()
        assert c.compare([1, 2, 3], [1, 2, 3]).equal is True
        assert c.compare([1, 2, 3], [3, 2, 1]).equal is False
        result = c.compare([1, 2], [1])
        assert result.equal is False
        result = c.compare([1, "a"], [1, 2])
        assert result.equal is False
        assert result.type_match is False

    def test_exact_int_sequence_rejects_bool_int_coercion(self):
        from doctor.adversarial.comparators import ExactIntSequenceComparator

        c = ExactIntSequenceComparator()
        assert c.compare([1, 2, 3], [1, 2, 3]).equal is True
        assert c.compare([1], [True]).equal is False
        assert c.compare([True], [1]).equal is False
        assert c.compare([1, 2], [1]).equal is False

    def test_multiset(self):
        from doctor.adversarial.comparators import MultisetComparator
        c = MultisetComparator()
        assert c.compare([1, 2, 3], [3, 2, 1]).equal is True
        assert c.compare([1, 2, 2], [2, 1, 2]).equal is True
        assert c.compare([1, 2], [1, 2, 3]).equal is False

    def test_float_tolerance(self):
        from doctor.adversarial.comparators import FloatToleranceComparator
        c = FloatToleranceComparator(epsilon=0.01)
        assert c.compare(1.0, 1.0).equal is True
        assert c.compare(1.0, 1.005).equal is True
        assert c.compare(1.0, 1.02).equal is False
        result = c.compare(1.0, 1)
        assert result.equal is False
        assert result.type_match is False

    def test_structured_dict(self):
        from doctor.adversarial.comparators import StructuredComparator
        c = StructuredComparator()
        assert c.compare({"a": 1, "b": 2}, {"a": 1, "b": 2}).equal is True
        assert c.compare({"a": 1}, {"a": 2}).equal is False
        result = c.compare({"a": 1}, {"b": 1})
        assert result.equal is False

    def test_structured_nested(self):
        from doctor.adversarial.comparators import StructuredComparator
        c = StructuredComparator()
        a = {"x": [1, {"y": 2}], "z": 3}
        b = {"x": [1, {"y": 2}], "z": 3}
        assert c.compare(a, b).equal is True
        b["x"][1]["y"] = 99
        assert c.compare(a, b).equal is False

    def test_get_comparator(self):
        from doctor.adversarial.comparators import get_comparator
        c = get_comparator("ExactIntComparator")
        assert c.name == "ExactIntComparator"
        with pytest.raises(ValueError, match="unknown comparator"):
            get_comparator("NonExistent")

    def test_exact_scalar_is_recursive_typed_equality(self):
        from doctor.adversarial.comparators import get_comparator

        c = get_comparator("exact_scalar")
        assert c.compare([[1, 2], [3]], [[1, 2], [3]]).equal is True
        assert c.compare([[1]], [[True]]).equal is False


# ── Semantic drift CI tests ────────────────────────────────────────────────

class TestSemanticDriftCI:
    def test_all_23_drivers_explicitly_declare_comparator(self):
        from doctor.adversarial.driver_contract import DRIVER_CONTRACTS, validate_all_driver_contracts
        from doctor.adversarial.comparators import get_comparator

        validate_all_driver_contracts()
        assert len(DRIVER_CONTRACTS) == 23
        for problem_id, contract in DRIVER_CONTRACTS.items():
            assert contract.comparator
            assert contract.comparator != "StrictTypeComparator"
            assert get_comparator(contract.comparator).version
            assert contract.driver_file.endswith(f"{problem_id.lower()}_ingestion_gate.py")

    def test_missing_comparator_declaration_fails_contract_validation(self):
        from doctor.adversarial.driver_contract import (
            DRIVER_CONTRACTS,
            DriverContractError,
            validate_driver_contract,
        )

        broken = replace(DRIVER_CONTRACTS["LC322"], comparator="")
        with pytest.raises(DriverContractError, match="missing explicit comparator"):
            validate_driver_contract(broken)

    def test_perturbed_input_hash_differs_when_input_differs(self):
        from doctor.adversarial.provenance import build_provenance

        def oracle(t):
            return sum(t["nums"])

        base = {"nums": [1, 2, 3]}
        perturbed = {"nums": [3, 2, 1]}
        prov = build_provenance(
            oracle=oracle,
            oracle_name="oracle_test",
            comparator_name="exact_scalar",
            comparator_version="1.0.0",
            representation_name="ordering_invariant",
            representation_version="1.0.0",
            perturbation_family="ordering_invariant",
            proof_card_id="test",
            base_input=base,
            perturbed_input=perturbed,
            perturbation_class="output_preserving",
        )
        assert prov.base_input_hash != prov.perturbed_input_hash

    def test_null_transform_hash_can_match_only_when_inputs_identical(self):
        from doctor.adversarial.provenance import build_provenance

        def oracle(t):
            return sum(t["nums"])

        base = {"nums": [1, 2, 3]}
        prov = build_provenance(
            oracle=oracle,
            oracle_name="oracle_test",
            comparator_name="exact_scalar",
            comparator_version="1.0.0",
            representation_name="syntax_only",
            representation_version="1.0.0",
            perturbation_family="syntax_only",
            proof_card_id="test",
            base_input=base,
            perturbed_input=dict(base),
            perturbation_class="output_preserving",
        )
        assert prov.base_input_hash == prov.perturbed_input_hash

        changed = build_provenance(
            oracle=oracle,
            oracle_name="oracle_test",
            comparator_name="exact_scalar",
            comparator_version="1.0.0",
            representation_name="syntax_only",
            representation_version="1.0.0",
            perturbation_family="syntax_only",
            proof_card_id="test",
            base_input=base,
            perturbed_input={"nums": [1, 2, 3], "_note": "copy"},
            perturbation_class="output_preserving",
        )
        assert changed.base_input_hash != changed.perturbed_input_hash

    def test_ingestion_gate_uses_shared_scoring_helper(self, monkeypatch):
        import doctor.adversarial.experiment_runner as runner
        import doctor.adversarial.ingestion_gate as gate

        calls: list[tuple[str, str]] = []
        original = runner.validate_scoring_gate

        def tracking(problem_id, perturbation_family):
            calls.append((problem_id, perturbation_family))
            return original(problem_id, perturbation_family)

        monkeypatch.setattr(runner, "validate_scoring_gate", tracking)
        monkeypatch.setattr(gate, "validate_scoring_gate", tracking)

        ingestion_gate(
            problem_id="LC322",
            reference_tests=[{"nums": [1, 2, 3]}],
            solvers=[lambda nums: sum(nums)],
            oracle=lambda t: sum(t["nums"]),
            apply_solver=lambda s, t: s(t["nums"]),
            apply_oracle=lambda o, t: o(t),
            perturbation_strategy=lambda t, n: [{"nums": list(reversed(t["nums"]))}],
            perturbation_family="multiset_invariant",
            perturbation_samples=1,
        )

        assert calls == [("LC322", "multiset_invariant")]

    def test_no_unperturbed_oracle_comparison(self):
        call_log: list[str] = []

        def tracking_oracle(t):
            call_log.append("oracle")
            return sum(t["nums"])

        def solver(nums):
            return sum(nums)

        def apply_solver(s, t):
            return s(t["nums"])

        def apply_oracle(o, t):
            return o(t)

        def perturb_strategy(t, n):
            return [{"nums": list(reversed(t["nums"]))}]

        ingestion_gate(
            problem_id="LC322",
            reference_tests=[{"nums": [1, 2, 3]}],
            solvers=[solver],
            oracle=tracking_oracle,
            apply_solver=apply_solver,
            apply_oracle=apply_oracle,
            perturbation_strategy=perturb_strategy,
            perturbation_family="multiset_invariant",
            perturbation_samples=1,
        )

        oracle_call_count = len(call_log)
        assert oracle_call_count >= 2, (
            f"oracle called only {oracle_call_count} time(s); "
            f"expected at least 2 (1 for base, 1 for perturbed)"
        )

    def test_no_invalid_class_in_scoring_path(self):
        import doctor.adversarial.perturbation_validity as pv
        invalid_decl = pv.PerturbationDeclaration(
            perturbation_class=PerturbationClass.INVALID,
            justification="test invalid",
            proof_card_id=None,
        )
        pv.PERTURBATION_VALIDITY_REGISTRY[("TEST_INVALID", "bad")] = invalid_decl
        try:
            with pytest.raises((ValueError, PerturbationScoringBlocked)):
                ingestion_gate(
                    problem_id="TEST_INVALID",
                    reference_tests=[{"nums": [1]}],
                    solvers=[lambda x: 0],
                    oracle=lambda x: 0,
                    apply_solver=lambda s, t: 0,
                    apply_oracle=lambda o, t: 0,
                    perturbation_strategy=lambda t, n: [{"nums": [0]}],
                    perturbation_family="bad",
                    perturbation_samples=1,
                )
        finally:
            del pv.PERTURBATION_VALIDITY_REGISTRY[("TEST_INVALID", "bad")]

    def test_proof_card_required_for_output_preserving(self):
        import doctor.adversarial.perturbation_validity as pv
        no_proof = pv.PerturbationDeclaration(
            perturbation_class=PerturbationClass.OUTPUT_PRESERVING,
            justification="test no proof card",
            proof_card_id=None,
        )
        pv.PERTURBATION_VALIDITY_REGISTRY[("TEST_NOPROOF", "no_proof")] = no_proof
        try:
            with pytest.raises(PerturbationScoringBlocked, match="proof_card_id"):
                ingestion_gate(
                    problem_id="TEST_NOPROOF",
                    reference_tests=[{"nums": [1]}],
                    solvers=[lambda x: 0],
                    oracle=lambda x: 0,
                    apply_solver=lambda s, t: 0,
                    apply_oracle=lambda o, t: 0,
                    perturbation_strategy=lambda t, n: [{"nums": [0]}],
                    perturbation_family="no_proof",
                    perturbation_samples=1,
                )
        finally:
            del pv.PERTURBATION_VALIDITY_REGISTRY[("TEST_NOPROOF", "no_proof")]

    def test_provenance_required_on_result(self):
        def solver(nums):
            return sum(nums)

        def apply_solver(s, t):
            return s(t["nums"])

        def apply_oracle(o, t):
            return o(t)

        def perturb_strategy(t, n):
            return [{"nums": list(reversed(t["nums"]))}]

        result = ingestion_gate(
            problem_id="LC322",
            reference_tests=[{"nums": [1, 2, 3]}],
            solvers=[solver],
            oracle=lambda t: sum(t["nums"]),
            apply_solver=apply_solver,
            apply_oracle=apply_oracle,
            perturbation_strategy=perturb_strategy,
            perturbation_family="multiset_invariant",
            perturbation_samples=1,
        )
        assert "k_provenance" in result
        prov = result["k_provenance"]
        assert prov["oracle_name"] == "oracle_lc322"
        assert prov["comparator_name"] == "exact_scalar"
        assert prov["perturbation_class"] == "output_preserving"
        assert prov["proof_card_id"] is not None
        assert prov["base_input_hash"] != ""
        assert prov["perturbed_input_hash"] != ""
        assert prov["base_input_hash"] != prov["perturbed_input_hash"]
        assert "1.0.0" != prov["oracle_version"]
        assert prov["evaluated_at"] != ""

    def test_provenance_has_all_required_fields(self):
        from doctor.adversarial.experiment_contract import REQUIRED_PROVENANCE_FIELDS, validate_provenance

        def solver(nums):
            return sum(nums)

        def apply_solver(s, t):
            return s(t["nums"])

        def apply_oracle(o, t):
            return o(t)

        def perturb_strategy(t, n):
            return [{"nums": list(reversed(t["nums"]))}]

        result = ingestion_gate(
            problem_id="LC322",
            reference_tests=[{"nums": [1, 2, 3]}],
            solvers=[solver],
            oracle=lambda t: sum(t["nums"]),
            apply_solver=apply_solver,
            apply_oracle=apply_oracle,
            perturbation_strategy=perturb_strategy,
            perturbation_family="multiset_invariant",
            perturbation_samples=1,
        )
        prov = result["k_provenance"]
        for field in REQUIRED_PROVENANCE_FIELDS:
            assert field in prov, f"missing provenance field: {field}"

    def test_provenance_missing_block_fails_validation(self):
        from doctor.adversarial.experiment_contract import ExperimentContractError, validate_provenance
        with pytest.raises(ExperimentContractError, match="missing k_provenance"):
            validate_provenance({"metrics": {}})

    def test_stale_provenance_fails_ci(self):
        from doctor.adversarial.provenance import check_provenance_stale, ProvenanceError, oracle_identity

        def oracle_v1(t):
            return sum(t["nums"])

        def oracle_v2(t):
            return sum(t["nums"]) + 1

        current_identity = oracle_identity(oracle_v2)
        stale_identity = oracle_identity(oracle_v1)
        assert current_identity != "1.0.0"
        assert stale_identity != current_identity
        with pytest.raises(ProvenanceError, match="stale oracle_version"):
            check_provenance_stale({"oracle_version": stale_identity}, expected_oracle_version=current_identity)

    def test_provenance_input_hash_consistent(self):
        from doctor.adversarial.provenance import input_hash
        h1 = input_hash({"nums": [1, 2, 3]})
        h2 = input_hash({"nums": [1, 2, 3]})
        h3 = input_hash({"nums": [3, 2, 1]})
        assert h1 == h2
        assert h1 != h3

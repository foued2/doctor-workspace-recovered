from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from doctor.v03.interfaces import (
    AbstractV03Generator,
    AbstractV03Oracle,
    GeneratedCase,
    GeneratorOraclePairSpec,
    GeneratorSpec,
    OracleResult,
    OracleSpec,
    ParameterEnvelope,
    V03ExternalDependencyError,
    V03GeneratorError,
    V03OracleError,
    V03SchemaError,
    assert_no_external_dependency,
    validate_generated_case,
    validate_generator_oracle_pair,
    validate_generator_spec,
    validate_oracle_result,
    validate_oracle_spec,
)

_VALID_PARAM_ENVELOPE = ParameterEnvelope(
    family_id="test_family",
    bounds={"n": (1, 100)},
    description="Test parameter envelope",
)

_VALID_GENERATOR_SPEC = GeneratorSpec(
    family_id="test_family",
    generator_id="test_gen",
    generator_version="1.0.0",
    generator_hash="abc123",
    deterministic_seed_policy="fixed_seed_per_case_id",
    parameter_envelope=_VALID_PARAM_ENVELOPE,
    input_schema={"type": "object"},
    output_case_schema={"type": "object"},
    no_external_dependency=True,
    no_llm_dependency=True,
)

_VALID_ORACLE_SPEC = OracleSpec(
    family_id="test_family",
    oracle_id="test_oracle",
    oracle_version="1.0.0",
    oracle_hash="def456",
    supported_input_schema={"type": "object"},
    supported_parameter_envelope=_VALID_PARAM_ENVELOPE,
    exactness_claim="exact for all cases within parameter envelope",
    expected_output_schema={"type": "integer"},
    comparator_id="exact_scalar",
    no_external_dependency=True,
    no_llm_dependency=True,
)

_VALID_CASE = GeneratedCase(
    family_id="test_family",
    case_id="case_001",
    input_payload={"n": 5},
    parameter_envelope_hash="hash_env",
    generator_id="test_gen",
    generator_hash="abc123",
    seed_hash="seed_hash_001",
)

_VALID_RESULT = OracleResult(
    family_id="test_family",
    case_id="case_001",
    expected_output=15,
    expected_output_hash="out_hash_001",
    oracle_id="test_oracle",
    oracle_hash="def456",
    comparator_id="exact_scalar",
)

_VALID_PAIR = GeneratorOraclePairSpec(
    family_id="test_family",
    generator_id="test_gen",
    oracle_id="test_oracle",
    comparator_id="exact_scalar",
    parameter_bounds={"n": (1, 100)},
    valid_case_predicate_id="n_within_bounds",
    ambiguity_policy="reject_on_ambiguity",
)


class TestGeneratorSpecValidation:
    def test_accepts_complete_local_no_llm_spec(self) -> None:
        validate_generator_spec(_VALID_GENERATOR_SPEC)

    def test_rejects_external_dependency(self) -> None:
        spec = GeneratorSpec(
            family_id="test_family",
            generator_id="bad_gen",
            generator_version="1.0.0",
            generator_hash="abc",
            deterministic_seed_policy="fixed",
            parameter_envelope=_VALID_PARAM_ENVELOPE,
            input_schema={"type": "object"},
            output_case_schema={"type": "object"},
            no_external_dependency=False,
        )
        with pytest.raises(V03ExternalDependencyError, match="external dependency"):
            validate_generator_spec(spec)

    def test_rejects_llm_dependency(self) -> None:
        spec = GeneratorSpec(
            family_id="test_family",
            generator_id="bad_gen",
            generator_version="1.0.0",
            generator_hash="abc",
            deterministic_seed_policy="fixed",
            parameter_envelope=_VALID_PARAM_ENVELOPE,
            input_schema={"type": "object"},
            output_case_schema={"type": "object"},
            no_llm_dependency=False,
        )
        with pytest.raises(V03ExternalDependencyError, match="LLM dependency"):
            validate_generator_spec(spec)

    def test_rejects_empty_fields(self) -> None:
        spec = GeneratorSpec(
            family_id="",
            generator_id="",
            generator_version="",
            generator_hash="",
            deterministic_seed_policy="",
            parameter_envelope=_VALID_PARAM_ENVELOPE,
            input_schema={},
            output_case_schema={},
        )
        with pytest.raises(V03GeneratorError, match="validation failed"):
            validate_generator_spec(spec)

    def test_assert_no_external_dependency_passes(self) -> None:
        assert_no_external_dependency(_VALID_GENERATOR_SPEC)

    def test_assert_no_external_dependency_raises(self) -> None:
        spec = GeneratorSpec(
            family_id="f",
            generator_id="g",
            generator_version="1.0.0",
            generator_hash="h",
            deterministic_seed_policy="p",
            parameter_envelope=_VALID_PARAM_ENVELOPE,
            input_schema={"type": "object"},
            output_case_schema={"type": "object"},
            no_external_dependency=False,
        )
        with pytest.raises(V03ExternalDependencyError):
            assert_no_external_dependency(spec)


class TestOracleSpecValidation:
    def test_accepts_complete_local_no_llm_spec(self) -> None:
        validate_oracle_spec(_VALID_ORACLE_SPEC)

    def test_rejects_missing_exactness_claim(self) -> None:
        spec = OracleSpec(
            family_id="test_family",
            oracle_id="bad_oracle",
            oracle_version="1.0.0",
            oracle_hash="abc",
            supported_input_schema={"type": "object"},
            supported_parameter_envelope=_VALID_PARAM_ENVELOPE,
            exactness_claim="",
            expected_output_schema={"type": "integer"},
            comparator_id="exact_scalar",
        )
        with pytest.raises(V03OracleError, match="exactness_claim"):
            validate_oracle_spec(spec)

    def test_rejects_external_dependency(self) -> None:
        spec = OracleSpec(
            family_id="test_family",
            oracle_id="bad_oracle",
            oracle_version="1.0.0",
            oracle_hash="abc",
            supported_input_schema={"type": "object"},
            supported_parameter_envelope=_VALID_PARAM_ENVELOPE,
            exactness_claim="exact",
            expected_output_schema={"type": "integer"},
            comparator_id="exact_scalar",
            no_external_dependency=False,
        )
        with pytest.raises(V03ExternalDependencyError, match="external dependency"):
            validate_oracle_spec(spec)

    def test_rejects_empty_comparator_id(self) -> None:
        spec = OracleSpec(
            family_id="test_family",
            oracle_id="bad_oracle",
            oracle_version="1.0.0",
            oracle_hash="abc",
            supported_input_schema={"type": "object"},
            supported_parameter_envelope=_VALID_PARAM_ENVELOPE,
            exactness_claim="exact",
            expected_output_schema={"type": "integer"},
            comparator_id="",
        )
        with pytest.raises(V03OracleError, match="comparator_id"):
            validate_oracle_spec(spec)


class TestGeneratedCaseValidation:
    def test_accepts_matching_case(self) -> None:
        validate_generated_case(_VALID_CASE, _VALID_GENERATOR_SPEC)

    def test_rejects_generator_hash_mismatch(self) -> None:
        case = GeneratedCase(
            family_id="test_family",
            case_id="case_001",
            input_payload={"n": 5},
            parameter_envelope_hash="hash_env",
            generator_id="test_gen",
            generator_hash="WRONG_HASH",
            seed_hash="seed_hash_001",
        )
        with pytest.raises(V03SchemaError, match="generator_hash"):
            validate_generated_case(case, _VALID_GENERATOR_SPEC)

    def test_rejects_family_id_mismatch(self) -> None:
        case = GeneratedCase(
            family_id="other_family",
            case_id="case_001",
            input_payload={"n": 5},
            parameter_envelope_hash="hash_env",
            generator_id="test_gen",
            generator_hash="abc123",
            seed_hash="seed_hash_001",
        )
        with pytest.raises(V03SchemaError, match="family_id"):
            validate_generated_case(case, _VALID_GENERATOR_SPEC)

    def test_rejects_empty_case_id(self) -> None:
        case = GeneratedCase(
            family_id="test_family",
            case_id="",
            input_payload={"n": 5},
            parameter_envelope_hash="hash_env",
            generator_id="test_gen",
            generator_hash="abc123",
            seed_hash="seed_hash_001",
        )
        with pytest.raises(V03SchemaError, match="case_id"):
            validate_generated_case(case, _VALID_GENERATOR_SPEC)


class TestOracleResultValidation:
    def test_accepts_matching_result(self) -> None:
        validate_oracle_result(_VALID_CASE, _VALID_RESULT, _VALID_ORACLE_SPEC)

    def test_rejects_oracle_hash_mismatch(self) -> None:
        result = OracleResult(
            family_id="test_family",
            case_id="case_001",
            expected_output=15,
            expected_output_hash="out_hash_001",
            oracle_id="test_oracle",
            oracle_hash="WRONG_HASH",
            comparator_id="exact_scalar",
        )
        with pytest.raises(V03SchemaError, match="oracle_hash"):
            validate_oracle_result(_VALID_CASE, result, _VALID_ORACLE_SPEC)

    def test_rejects_comparator_mismatch(self) -> None:
        result = OracleResult(
            family_id="test_family",
            case_id="case_001",
            expected_output=15,
            expected_output_hash="out_hash_001",
            oracle_id="test_oracle",
            oracle_hash="def456",
            comparator_id="WRONG_COMPARATOR",
        )
        with pytest.raises(V03SchemaError, match="comparator_id"):
            validate_oracle_result(_VALID_CASE, result, _VALID_ORACLE_SPEC)

    def test_rejects_case_id_mismatch(self) -> None:
        result = OracleResult(
            family_id="test_family",
            case_id="other_case",
            expected_output=15,
            expected_output_hash="out_hash_001",
            oracle_id="test_oracle",
            oracle_hash="def456",
            comparator_id="exact_scalar",
        )
        with pytest.raises(V03SchemaError, match="case_id"):
            validate_oracle_result(_VALID_CASE, result, _VALID_ORACLE_SPEC)


class TestPairValidation:
    def test_accepts_matching_pair(self) -> None:
        validate_generator_oracle_pair(
            _VALID_PAIR, _VALID_GENERATOR_SPEC, _VALID_ORACLE_SPEC
        )

    def test_rejects_family_mismatch(self) -> None:
        pair = GeneratorOraclePairSpec(
            family_id="other_family",
            generator_id="test_gen",
            oracle_id="test_oracle",
            comparator_id="exact_scalar",
            parameter_bounds={"n": (1, 100)},
            valid_case_predicate_id="n_within_bounds",
            ambiguity_policy="reject_on_ambiguity",
        )
        with pytest.raises(V03SchemaError, match="family_id"):
            validate_generator_oracle_pair(
                pair, _VALID_GENERATOR_SPEC, _VALID_ORACLE_SPEC
            )

    def test_rejects_empty_parameter_bounds(self) -> None:
        pair = GeneratorOraclePairSpec(
            family_id="test_family",
            generator_id="test_gen",
            oracle_id="test_oracle",
            comparator_id="exact_scalar",
            parameter_bounds={},
            valid_case_predicate_id="n_within_bounds",
            ambiguity_policy="reject_on_ambiguity",
        )
        with pytest.raises(V03SchemaError, match="parameter_bounds"):
            validate_generator_oracle_pair(
                pair, _VALID_GENERATOR_SPEC, _VALID_ORACLE_SPEC
            )


class TestAbstractBaseClasses:
    def test_generator_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            AbstractV03Generator()  # type: ignore[abstract]

    def test_oracle_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            AbstractV03Oracle()  # type: ignore[abstract]

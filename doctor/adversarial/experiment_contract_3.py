"""ERD-enforcing execution wrapper for Doctor experiments."""
from __future__ import annotations

import json
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from doctor.adversarial.experiment_contract import (
    LABEL_SCHEMA_VERSION,
    ExperimentInput,
    ExperimentRunDescriptor,
    ExperimentRunRecord,
    SolverClassification,
    SolverExecution,
    execution_hash,
    validate_run_record,
)
from doctor.adversarial.perturbation_validity import (
    PerturbationClass,
    PerturbationDeclaration,
    SCORING_ALLOWED_CLASSES,
    get_declaration,
    validate_proof_card_reference,
)
from doctor.adversarial.comparators import ComparatorResult, get_comparator
from doctor.adversarial.provenance import build_provenance


STRICT_INTERFACE_MODE = True

SolverCallable = Callable[[list[int]], int]
ClassifierCallable = Callable[
    [tuple[ExperimentInput, ...], tuple[SolverExecution, ...]],
    tuple[SolverClassification, ...],
]


class PerturbationScoringBlocked(Exception):
    pass


@dataclass(frozen=True)
class ExperimentSolver:
    solver_id: str
    run: SolverCallable


class SolverInterfaceContractError(TypeError):
    pass


def validate_scoring_gate(problem_id: str, perturbation_family: str) -> PerturbationDeclaration:
    declaration = get_declaration(problem_id, perturbation_family)
    if declaration.perturbation_class not in SCORING_ALLOWED_CLASSES:
        raise PerturbationScoringBlocked(
            f"scoring blocked: perturbation_class={declaration.perturbation_class.value} "
            f"for ({problem_id}, {perturbation_family})"
        )
    if declaration.perturbation_class == PerturbationClass.OUTPUT_PRESERVING and declaration.proof_card_id is None:
        raise PerturbationScoringBlocked(
            f"scoring blocked: OUTPUT_PRESERVING without proof_card_id "
            f"for ({problem_id}, {perturbation_family})"
        )
    if declaration.proof_card_id is not None:
        try:
            validate_proof_card_reference(declaration.proof_card_id)
        except ValueError as exc:
            raise PerturbationScoringBlocked(
                f"scoring blocked: invalid proof_card_id for ({problem_id}, {perturbation_family}): {exc}"
            ) from exc
    return declaration


def recompute_oracles(
    oracle: Callable[[Any], Any],
    base_input: Any,
    perturbed_input: Any,
    apply_oracle: Callable[[Callable, Any], Any],
) -> tuple[Any, Any]:
    return apply_oracle(oracle, base_input), apply_oracle(oracle, perturbed_input)


def dispatch_comparator(comparator_name: str, actual: Any, expected: Any) -> ComparatorResult:
    return get_comparator(comparator_name).compare(actual, expected)


def construct_evaluation_provenance(
    *,
    problem_id: str,
    perturbation_family: str,
    oracle: Callable,
    comparator_name: str,
    comparator_version: str,
    base_input: Any,
    perturbed_input: Any,
    declaration: PerturbationDeclaration,
):
    return build_provenance(
        oracle=oracle,
        oracle_name=f"oracle_{problem_id.lower()}",
        comparator_name=comparator_name,
        comparator_version=comparator_version,
        representation_name=perturbation_family,
        representation_version="1.0.0",
        perturbation_family=perturbation_family,
        proof_card_id=declaration.proof_card_id,
        base_input=base_input,
        perturbed_input=perturbed_input,
        perturbation_class=declaration.perturbation_class.value,
    )


@dataclass(frozen=True)
class ExperimentSpec:
    problem_id: str
    solver_set_id: str
    manifold_set_id: str
    probe_set_id: str
    failure_class_version: str
    inputs: tuple[ExperimentInput, ...]
    solvers: tuple[ExperimentSolver, ...]
    classify: ClassifierCallable
    status: str = "experimental"
    notes: str = ""
    label_schema_version: str = LABEL_SCHEMA_VERSION


def run_experiment(spec: ExperimentSpec) -> ExperimentRunRecord:
    _validate_spec(spec)
    executions: list[SolverExecution] = []
    for solver in spec.solvers:
        for experiment_input in spec.inputs:
            observed = solver.run(list(experiment_input.payload["nums"]))
            passed = observed == experiment_input.expected
            executions.append(
                SolverExecution(
                    solver_id=solver.solver_id,
                    input_id=experiment_input.input_id,
                    observed=observed,
                    expected=experiment_input.expected,
                    passed=passed,
                    failure_record=None
                    if passed
                    else {
                        "solver_id": solver.solver_id,
                        "input_id": experiment_input.input_id,
                        "manifold_id": experiment_input.manifold_id,
                        "payload": experiment_input.payload,
                        "expected": experiment_input.expected,
                        "observed": observed,
                    },
                )
            )

    inputs = tuple(spec.inputs)
    execution_rows = tuple(executions)
    classifications = spec.classify(inputs, execution_rows)
    descriptor = ExperimentRunDescriptor(
        problem_id=spec.problem_id,
        solver_set_id=spec.solver_set_id,
        manifold_set_id=spec.manifold_set_id,
        probe_set_id=spec.probe_set_id,
        label_schema_version=spec.label_schema_version,
        execution_hash=execution_hash(
            {
                "problem_id": spec.problem_id,
                "solver_set_id": spec.solver_set_id,
                "manifold_set_id": spec.manifold_set_id,
                "probe_set_id": spec.probe_set_id,
                "failure_class_version": spec.failure_class_version,
                "inputs": [row.__dict__ for row in inputs],
                "executions": [row.__dict__ for row in execution_rows],
                "classifications": [row.__dict__ for row in classifications],
            }
        ),
        failure_class_version=spec.failure_class_version,
        status=spec.status,
        notes=spec.notes,
    )
    record = ExperimentRunRecord(
        descriptor=descriptor,
        inputs=inputs,
        executions=execution_rows,
        classifications=classifications,
    )
    validate_run_record(record.to_dict())
    return record


def write_experiment_record(record: ExperimentRunRecord, path: str | Path) -> None:
    record_dict = record.to_dict()
    validate_run_record(record_dict)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(record_dict, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def write_experiment_artifacts(
    *,
    report: dict[str, Any],
    report_path: str | Path,
    record: ExperimentRunRecord,
    record_path: str | Path,
) -> None:
    write_experiment_record(record, record_path)
    output_path = Path(report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _validate_spec(spec: ExperimentSpec) -> None:
    if spec.label_schema_version != LABEL_SCHEMA_VERSION:
        raise ValueError(f"unsupported label schema: {spec.label_schema_version}")
    if not spec.inputs:
        raise ValueError("experiment inputs must be non-empty")
    if not spec.solvers:
        raise ValueError("experiment solvers must be non-empty")
    if not spec.failure_class_version:
        raise ValueError("failure_class_version must be non-empty")
    if not spec.probe_set_id:
        raise ValueError("probe_set_id must be non-empty")
    input_ids = [row.input_id for row in spec.inputs]
    if len(input_ids) != len(set(input_ids)):
        raise ValueError("experiment input_id values must be unique")
    solver_ids = [row.solver_id for row in spec.solvers]
    if len(solver_ids) != len(set(solver_ids)):
        raise ValueError("experiment solver_id values must be unique")
    for experiment_input in spec.inputs:
        nums = experiment_input.payload.get("nums")
        if not isinstance(nums, list) or not all(isinstance(value, int) for value in nums):
            raise SolverInterfaceContractError("experiment input payload must contain nums: list[int]")
    if STRICT_INTERFACE_MODE:
        for solver in spec.solvers:
            _validate_solver_interface(solver)


def _validate_solver_interface(solver: ExperimentSolver) -> None:
    signature = inspect.signature(solver.run)
    required_positionals = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.default is inspect.Parameter.empty
        and parameter.kind
        in {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        }
    ]
    variadics = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind
        in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }
    ]
    if len(required_positionals) != 1 or variadics:
        raise SolverInterfaceContractError(
            f"{solver.solver_id} must expose solve(nums: list[int]) -> int"
        )
    parameter = required_positionals[0]
    if not _is_list_int_annotation(parameter.annotation) or not _is_int_annotation(signature.return_annotation):
        raise SolverInterfaceContractError(
            f"{solver.solver_id} must expose solve(nums: list[int]) -> int"
        )


def _is_list_int_annotation(annotation: object) -> bool:
    return annotation in {list[int], "list[int]"}


def _is_int_annotation(annotation: object) -> bool:
    return annotation in {int, "int"}


def evaluate_perturbed(
    problem_id: str,
    perturbation_family: str,
    solver: Callable,
    base_input: Any,
    perturbed_input: Any,
    oracle: Callable[[Any], Any],
    apply_solver: Callable[[Callable, Any], Any],
    apply_oracle: Callable[[Callable, Any], Any],
) -> dict[str, Any]:
    declaration = validate_scoring_gate(problem_id, perturbation_family)
    expected_base, expected_perturbed = recompute_oracles(
        oracle, base_input, perturbed_input, apply_oracle
    )
    observed = apply_solver(solver, perturbed_input)

    return {
        "expected_base": expected_base,
        "expected_perturbed": expected_perturbed,
        "observed": observed,
        "perturbation_class": declaration.perturbation_class.value,
        "proof_card_id": declaration.proof_card_id,
    }


def evaluate_perturbed_batch(
    problem_id: str,
    perturbation_family: str,
    solvers: list[Callable],
    base_inputs: list[Any],
    perturbed_inputs: list[list[Any]],
    oracle: Callable[[Any], Any],
    apply_solver: Callable[[Callable, Any], Any],
    apply_oracle: Callable[[Callable, Any], Any],
) -> list[list[list[dict[str, Any]]]]:
    result: list[list[list[dict[str, Any]]]] = []
    for tidx, base in enumerate(base_inputs):
        per_test: list[list[dict[str, Any]]] = []
        for pidx, perturbed in enumerate(perturbed_inputs[tidx]):
            per_perturb: list[dict[str, Any]] = []
            for sidx, solver in enumerate(solvers):
                per_perturb.append(
                    evaluate_perturbed(
                        problem_id=problem_id,
                        perturbation_family=perturbation_family,
                        solver=solver,
                        base_input=base,
                        perturbed_input=perturbed,
                        oracle=oracle,
                        apply_solver=apply_solver,
                        apply_oracle=apply_oracle,
                    )
                )
            per_test.append(per_perturb)
        result.append(per_test)
    return result

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from doctor.adversarial.driver_contract import (
    DRIVER_CONTRACTS,
    DriverContractError,
    validate_driver_contract,
)
from doctor.adversarial.experiment_runner import PerturbationScoringBlocked, validate_scoring_gate
from doctor.adversarial.perturbation_validity import (
    PerturbationClass,
    PerturbationDeclaration,
    validate_proof_card_reference,
)
from doctor.adversarial.provenance import (
    ProvenanceError,
    build_provenance,
    check_provenance_stale,
    input_hash,
    oracle_identity,
    validate_provenance_input_hashes,
)


ROOT = Path(__file__).resolve().parents[1]


def _phase1_oracle(case: dict[str, int]) -> int:
    return case["amount"]


def test_d6_stale_oracle_version_is_rejected() -> None:
    base = {"amount": 11}
    provenance = build_provenance(
        oracle=_phase1_oracle,
        oracle_name="phase1_oracle",
        comparator_name="exact_scalar",
        comparator_version="1.0.0",
        representation_name="identity",
        representation_version="1.0.0",
        perturbation_family="identity",
        proof_card_id="findings/FINDINGS_157.md",
        base_input=base,
        perturbed_input=base,
        perturbation_class="output_preserving",
    ).to_dict()
    provenance["oracle_version"] = "stale-oracle-version"

    with pytest.raises(ProvenanceError, match="stale oracle_version"):
        check_provenance_stale(provenance, expected_oracle_version=oracle_identity(_phase1_oracle))


def test_d7_bad_perturbed_input_hash_is_rejected() -> None:
    base = {"coins": [1, 2, 5], "amount": 11}
    perturbed = {"coins": [5, 2, 1], "amount": 11}
    correct_base_hash = input_hash(base)
    correct_perturbed_hash = input_hash(perturbed)
    assert correct_base_hash != correct_perturbed_hash

    provenance = {
        "base_input_hash": correct_base_hash,
        "perturbed_input_hash": correct_base_hash,
    }
    with pytest.raises(ProvenanceError, match="perturbed_input_hash mismatch"):
        validate_provenance_input_hashes(provenance, base_input=base, perturbed_input=perturbed)

    provenance["perturbed_input_hash"] = correct_perturbed_hash
    validate_provenance_input_hashes(provenance, base_input=base, perturbed_input=perturbed)


def test_d8_missing_comparator_declaration_is_rejected() -> None:
    valid = DRIVER_CONTRACTS["LC322"]
    validate_driver_contract(valid)

    implicit = replace(valid, comparator="")
    with pytest.raises(DriverContractError, match="missing explicit comparator"):
        validate_driver_contract(implicit)


@pytest.mark.parametrize(
    "proof_card_id,match",
    [
        ("findings/FINDINGS_999999.md", "missing file"),
        ("findings/FINDINGS_154.md:999999", "invalid line anchor"),
        ("not-a-proof-card", "invalid proof_card_id format"),
    ],
)
def test_d9_spoofed_proof_card_references_are_rejected(proof_card_id: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        validate_proof_card_reference(proof_card_id, repo_root=ROOT)


def test_d9_scoring_gate_blocks_spoofed_proof_card_reference() -> None:
    import doctor.adversarial.perturbation_validity as pv

    key = ("TRACK_D_PHASE1", "spoofed_proof_card")
    original = pv.PERTURBATION_VALIDITY_REGISTRY.get(key)
    pv.PERTURBATION_VALIDITY_REGISTRY[key] = PerturbationDeclaration(
        perturbation_class=PerturbationClass.OUTPUT_PRESERVING,
        justification="Track D Phase 1 mutant: spoofed proof-card reference",
        proof_card_id="findings/FINDINGS_999999.md",
    )
    try:
        with pytest.raises(PerturbationScoringBlocked, match="invalid proof_card_id"):
            validate_scoring_gate(*key)
    finally:
        if original is None:
            del pv.PERTURBATION_VALIDITY_REGISTRY[key]
        else:
            pv.PERTURBATION_VALIDITY_REGISTRY[key] = original


def test_d11_generator_weakening_mutant_is_flagged() -> None:
    data = json.loads((ROOT / "data" / "lc3928_doctor_probe.json").read_text(encoding="utf-8"))
    rows = data["result_rows"]
    for solver in ("lc3928_naive_local_price", "lc3928_greedy_nearest_shop"):
        included = _aggregate_solver(rows, solver, include_adversarial=True)
        removed = _aggregate_solver(rows, solver, include_adversarial=False)
        assert included["pass_count"] == 3503
        assert included["fail_count"] == 99
        assert included["case_count"] == 3602
        assert removed["pass_count"] == 3503
        assert removed["fail_count"] == 33
        assert removed["case_count"] == 3536
        assert removed["pass_rate"] > included["pass_rate"]
        assert removed["fail_count"] < included["fail_count"]


def _aggregate_solver(rows: list[dict], solver: str, *, include_adversarial: bool) -> dict[str, float | int]:
    selected = [
        row
        for row in rows
        if row["solver_name"] == solver
        and (include_adversarial or row["suite"] != "adversarial_tradeoff")
    ]
    pass_count = sum(int(row["pass_count"]) for row in selected)
    fail_count = sum(int(row["fail_count"]) for row in selected)
    case_count = sum(int(row["case_count"]) for row in selected)
    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "case_count": case_count,
        "pass_rate": pass_count / case_count,
    }

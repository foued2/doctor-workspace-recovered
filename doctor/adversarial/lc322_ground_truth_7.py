from __future__ import annotations

import random
from datetime import date
from pathlib import Path
from typing import Any

from doctor.adversarial.lc322_ground_truth import lc322_brute_force, GroundTruthDomainError

from external_anchors.anchoring import (
    DisagreementKind,
    ExternalAnchorResult,
    ExternalAnchorRunner,
    ProvenanceRecord,
)


ROOT = Path(__file__).resolve().parents[2]


def _lc322_random_small_cases(rng_seed: int = 32220260519, count: int = 100) -> list[dict[str, Any]]:
    rng = random.Random(rng_seed)
    cases = []
    for index in range(count):
        coin_count = rng.randint(1, 5)
        coins = sorted({rng.randint(1, 15) for _ in range(coin_count)})
        amount = rng.randint(0, 30)
        cases.append({
            "case_id": f"lc322_ext_anchor_random_{index + 1:03d}",
            "coins": coins,
            "amount": amount,
        })
    return cases


def _lc322_edge_cases() -> list[dict[str, Any]]:
    return [
        {"case_id": "lc322_ext_anchor_edge_amount_zero", "coins": [1, 2, 5], "amount": 0},
        {"case_id": "lc322_ext_anchor_edge_single_coin_exact", "coins": [7], "amount": 21},
        {"case_id": "lc322_ext_anchor_edge_single_coin_unreachable", "coins": [7], "amount": 20},
        {"case_id": "lc322_ext_anchor_edge_unreachable_amount", "coins": [2], "amount": 3},
        {"case_id": "lc322_ext_anchor_edge_duplicate_values", "coins": [1, 1, 2, 5], "amount": 11},
        {"case_id": "lc322_ext_anchor_edge_large_coin", "coins": [9, 10], "amount": 8},
        {"case_id": "lc322_ext_anchor_edge_gcd_unreachable", "coins": [6, 10, 14], "amount": 25},
        {"case_id": "lc322_ext_anchor_edge_canonical", "coins": [1, 2, 5], "amount": 11},
        {"case_id": "lc322_ext_anchor_edge_no_solution", "coins": [2], "amount": 3},
        {"case_id": "lc322_ext_anchor_edge_greedy_trap", "coins": [1, 3, 4], "amount": 6},
    ]


def _lc322_external_validation_manifest_cases() -> list[dict[str, Any]]:
    import json
    path = ROOT / "EXTERNAL_VALIDATION_MANIFEST.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for case in payload["cases"]:
        inp = case["input"]
        cases.append({
            "case_id": case["case_id"],
            "coins": list(inp["coins"]),
            "amount": int(inp["amount"]),
        })
    return cases


class LC322ExternalRunner(ExternalAnchorRunner):
    def __init__(self, provenance: ProvenanceRecord) -> None:
        super().__init__(problem="LC322", provenance=provenance)
        from external_anchors.lc322.solver_1 import lc322_reference_bfs
        self._reference = lc322_reference_bfs

    def generate_cases(self) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        cases.extend(_lc322_edge_cases())
        cases.extend(_lc322_random_small_cases())
        cases.extend(_lc322_external_validation_manifest_cases())
        return cases

    def run_doctor(self, case: dict[str, Any]) -> Any:
        try:
            return lc322_brute_force(case["coins"], case["amount"])
        except GroundTruthDomainError:
            return None

    def run_external(self, case: dict[str, Any]) -> Any:
        return self._reference(case["coins"], case["amount"])


def run_lc322_external_anchoring() -> ExternalAnchorResult:
    prov = ProvenanceRecord(
        source="Independently written reference implementation (LLM agent session)",
        author="LLM agent (open code big-pickle)",
        date_accessed=date(2026, 5, 20),
        problem="LC322 — Coin Change",
        reason_independent="Reference solver uses BFS on state graph — algorithmically distinct from Doctor's DFS and DP oracles",
        accepted_status="Standard BFS shortest-path algorithm for coin change",
        license_note="Free use for research validation",
    )
    runner = LC322ExternalRunner(prov)
    return runner.execute()

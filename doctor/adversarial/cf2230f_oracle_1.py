from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path
from typing import Any

from doctor.adversarial.cf2230f_oracle import cf2230f_scores_small, CF2230FOracleLimitError

from external_anchors.anchoring import (
    ExternalAnchorResult,
    ExternalAnchorRunner,
    ProvenanceRecord,
)


ROOT = Path(__file__).resolve().parents[2]
DUEL_ARTIFACT = ROOT / "data" / "track_d_phase2_cf2230f_oracle_duel.json"
SAMPLE_PARENTS = [1, 1, 3, 3, 1, 2, 1, 2, 8]


def _cf2230f_selected_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for q in range(1, 7):
        cases.append({
            "case_id": f"cf2230f_ext_anchor_sample_q{q}",
            "parents": SAMPLE_PARENTS[:q],
        })
    shape_cases = [
        {"case_id": "cf2230f_ext_anchor_shape_path", "parents": [1, 2, 3, 4, 5, 6]},
        {"case_id": "cf2230f_ext_anchor_shape_star", "parents": [1, 1, 1, 1, 1, 1]},
        {"case_id": "cf2230f_ext_anchor_shape_balanced", "parents": [1, 1, 2, 2, 3, 3]},
    ]
    cases.extend(shape_cases)
    rng = random.Random(2230_20260519)
    seen = {tuple(c["parents"]) for c in cases}
    for idx in range(10):
        while True:
            q = rng.randint(1, 6)
            parents = [rng.randint(1, i) for i in range(1, q + 1)]
            key = tuple(parents)
            if key not in seen:
                seen.add(key)
                break
        cases.append({
            "case_id": f"cf2230f_ext_anchor_random_{idx + 1:03d}",
            "parents": parents,
        })
    return cases


class CF2230FExternalRunner(ExternalAnchorRunner):
    def __init__(self, provenance: ProvenanceRecord) -> None:
        super().__init__(problem="CF2230F", provenance=provenance)
        from external_anchors.cf2230f.solver_1 import cf2230f_reference_minimax
        self._reference = cf2230f_reference_minimax

    def generate_cases(self) -> list[dict[str, Any]]:
        return _cf2230f_selected_cases()

    def run_doctor(self, case: dict[str, Any]) -> Any:
        try:
            return cf2230f_scores_small(case["parents"], max_q=6)
        except CF2230FOracleLimitError:
            return None

    def run_external(self, case: dict[str, Any]) -> Any:
        return self._reference(case["parents"])


def run_cf2230f_external_anchoring(use_solver: str = "minimax") -> ExternalAnchorResult:
    alg_name = {"minimax": "explicit game tree minimax", "minimax_opt": "compressed-state minimax"}.get(use_solver, use_solver)
    prov = ProvenanceRecord(
        source="Independently written reference implementation (LLM agent session)",
        author="LLM agent (open code big-pickle)",
        date_accessed=date(2026, 5, 20),
        problem="CF2230F — Game on Tree (min-max score)",
        reason_independent=f"Reference solver uses {alg_name} — structurally different encoding from Doctor's bitmask and frozenset minimax oracles",
        accepted_status="Standard minimax game tree evaluation",
        license_note="Free use for research validation",
    )
    runner = CF2230FExternalRunner(prov)
    if use_solver == "minimax_opt":
        from external_anchors.cf2230f.solver_2 import cf2230f_reference_minimax_opt  # noqa: F811
        runner._reference = cf2230f_reference_minimax_opt  # type: ignore
    return runner.execute()

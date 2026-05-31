from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generators.lc875_universal_generator import generate_inputs
from doctor.adversarial.lc875_candidates import lc875_reference


def _round(x: float) -> float:
    return round(float(x), 6)


def can_finish(piles: Sequence[int], h: int, speed: int) -> bool:
    total = sum((p + speed - 1) // speed for p in piles)
    return total <= h


def main() -> None:
    records = generate_inputs(seed=42, small_per_n=16, large_count=180)

    boundary_conditions = {
        "native_binary_search": None,
        "lower_shifted": None,
        "upper_shifted": None,
    }

    for bc_name in boundary_conditions:
        results = []
        for rec in records:
            n = int(rec["n"])
            piles = [int(v) for v in rec["piles"]]
            h = int(rec["h"])

            lo, hi = 1, max(piles)
            if bc_name == "lower_shifted":
                lo = max(1, (sum(piles) + h - 1) // h)
            elif bc_name == "upper_shifted":
                hi = max(piles) * 2

            ref = lc875_reference(n, piles, h)

            bc_ref = None
            lo_c, hi_c = lo, hi
            while lo_c < hi_c:
                mid = (lo_c + hi_c) // 2
                if can_finish(piles, h, mid):
                    hi_c = mid
                else:
                    lo_c = mid + 1
            bc_ref = lo_c

            results.append({
                "input_id": rec["input_id"],
                "n": n,
                "ref_output": ref,
                f"{bc_name}_output": bc_ref,
                f"{bc_name}_matches_ref": bc_ref == ref,
            })

        boundary_conditions[bc_name] = results

    # Aggregate
    agg = {}
    for bc_name, bc_results in boundary_conditions.items():
        n_total = len(bc_results)
        n_match = sum(1 for r in bc_results if r[f"{bc_name}_matches_ref"])
        agg[bc_name] = {
            "total": n_total,
            "matches_ref": n_match,
            "match_rate": _round(n_match / n_total),
        }

    # AUC proxy: match_rate difference between boundary conditions
    match_rates = {bc: agg[bc]["match_rate"] for bc in boundary_conditions}
    max_delta = max(match_rates.values()) - min(match_rates.values())
    varies = max_delta > 0.01

    report = {
        "prediction_id": 4,
        "class": "C (Boundary leakage)",
        "problem": "LC875 Koko Eating Bananas",
        "total_inputs": len(records),
        "boundary_conditions": agg,
        "max_match_rate_delta": _round(max_delta),
        "auc_varies_across_boundaries": varies,
        "boundary_dependence_detected": varies,
        "prediction_met_drift_expected": varies,
    }

    output_path = PROJECT_ROOT / "data" / "tier2_boundary_lc875.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    report_path = PROJECT_ROOT / "findings" / "TIER2_BOUNDARY_LC875.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TIER 2: Boundary Leakage — LC875 (Koko Eating Bananas)",
        "",
        "**Prediction 4 — Unanticipated null (drift expected but may fail)**",
        f"**Boundary dependence detected:** {varies}",
        f"**Max match-rate delta:** {report['max_match_rate_delta']}",
        f"**AUC varies across boundaries:** {varies}",
        "",
        "## Per-boundary results",
        "",
        "| Boundary condition | Match rate | Total |",
        "|---|---:|---:|",
    ]
    for bc, v in agg.items():
        lines.append(f"| `{bc}` | {v['match_rate']:.6f} | {v['total']} |")
    lines.extend([
        "",
        "## Interpretation",
        f"Boundary dependence {'DETECTED' if varies else 'NOT DETECTED'} in LC875 (Binary Search).",
        "",
        "If null (no boundary dependence): 'The framework's prediction was wrong — boundary dependence does not replicate to monotonic search domains.'",
        "",
        "This outcome is admissible as an unanticipated null and cannot be reclassified.",
    ])
    lines.append("")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "boundary_dependence_detected": varies,
        "max_match_rate_delta": report["max_match_rate_delta"],
    }, indent=2))
    print(f"Wrote: {output_path}")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    main()

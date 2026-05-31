from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generators.lc312_universal_generator import generate_inputs
from doctor.adversarial.lc312_candidates import (
    lc312_reference,
    lc312_greedy_immediate,
    lc312_greedy_smallest,
    lc312_left_to_right,
    lc312_alternating,
)


SOLVERS = {
    "reference": lc312_reference,
    "greedy_immediate": lc312_greedy_immediate,
    "greedy_smallest": lc312_greedy_smallest,
    "left_to_right": lc312_left_to_right,
    "alternating": lc312_alternating,
}


def main() -> None:
    records = generate_inputs(seed=42, small_per_n=16, large_count=180)
    pass_variations = 0
    per_input: list[dict[str, Any]] = []

    for rec in records:
        n = int(rec["n"])
        nums = [int(v) for v in rec["nums"]]

        outputs = {}
        for name, fn in SOLVERS.items():
            started = perf_counter()
            try:
                outputs[name] = {
                    "output": fn(n, nums),
                    "runtime_ms": round((perf_counter() - started) * 1000, 3),
                    "status": "ok",
                }
            except Exception as exc:
                outputs[name] = {"output": None, "runtime_ms": 0, "status": "error", "error": str(exc)}

        ref = outputs["reference"]["output"]
        ok_outs = {k: v["output"] for k, v in outputs.items() if v["status"] == "ok"}
        n_vary = sum(1 for v in ok_outs.values() if v != ref)
        uniform = n_vary == 0
        if not uniform:
            pass_variations += 1

        per_input.append({
            "input_id": rec["input_id"],
            "n": n,
            "pass_rate_uniform": uniform,
            "outputs": outputs,
        })

    total = len(records)
    uniform_rate = (total - pass_variations) / total

    report = {
        "problem": "LC312 Burst Balloons",
        "class": "A (Equivalence) — within-DP test",
        "total_inputs": total,
        "pass_rate_uniform": pass_variations == 0,
        "inputs_with_variation": pass_variations,
        "uniform_rate": round(uniform_rate, 6),
        "result": "Equivalence collapse generalizes within DP paradigm"
            if pass_variations == 0
            else "Equivalence collapse does NOT hold within DP paradigm"
            if uniform_rate < 0.95
            else "Equivalence collapse partially holds within DP paradigm",
    }

    output_path = PROJECT_ROOT / "data" / "tier2_equivalence_lc312.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    report_path = PROJECT_ROOT / "findings" / "TIER2_EQUIVALENCE_LC312.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TIER 2: Equivalence Collapse — LC312 (Burst Balloons, within-DP test)",
        "",
        f"**Total inputs:** {total}",
        f"**Pass rate uniform:** {report['pass_rate_uniform']}",
        f"**Inputs with variation:** {pass_variations}/{total}",
        f"**Uniform rate:** {uniform_rate:.4f}",
        "",
        f"**Result:** {report['result']}",
        "",
        "This tests whether equivalence collapse (observable in LC322/DP) generalizes",
        "to another DP problem (LC312 Burst Balloons, Interval DP).",
        "Same algorithmic paradigm, different problem structure.",
    ]
    lines.append("")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "pass_rate_uniform": report["pass_rate_uniform"],
        "inputs_with_variation": pass_variations,
        "total": total,
        "uniform_rate": report["uniform_rate"],
    }, indent=2))
    print(f"Wrote: {output_path}")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    main()

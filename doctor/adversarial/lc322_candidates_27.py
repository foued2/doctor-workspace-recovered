from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_candidates import (
    lc322_bfs_coin_count_cutoff,
    lc322_modulo_memo_alias,
    lc322_reachability_lookahead,
)
from doctor.adversarial.lc322_ground_truth import lc322_brute_force
from doctor.adversarial.lc322_synthesizer import _candidate_space


OUTPUT_PATH = PROJECT_ROOT / "data" / "lc322_opt_c_survivor_local_dominance.json"

LOCAL_DOMINANCE_FAMILIES = (
    "lc322_greedy_trap_no_subdivision",
    "lc322_large_coin_dominance_decoy",
    "lc322_dual_medium_dominance",
)
CONTROL_FAMILIES = ("lc322_unreachable_greedy_confusion",)

SURVIVORS: tuple[tuple[str, Callable[[list[int], int], int]], ...] = (
    ("lc322_bfs_coin_count_cutoff", lc322_bfs_coin_count_cutoff),
    ("lc322_modulo_memo_alias", lc322_modulo_memo_alias),
    ("lc322_reachability_lookahead", lc322_reachability_lookahead),
)


def _instances(generator_id: str) -> list[dict[str, object]]:
    instances = []
    for index, (coins, amount) in enumerate(_candidate_space(generator_id), start=1):
        instances.append(
            {
                "input_id": f"{generator_id}_{index:03d}",
                "coins": list(coins),
                "amount": amount,
                "truth": lc322_brute_force(list(coins), amount),
            }
        )
        if len(instances) >= 12:
            break
    return instances


def _evaluate_family(generator_id: str, family_class: str) -> dict[str, object]:
    instances = _instances(generator_id)
    survivor_rows = []
    for solver_id, solver in SURVIVORS:
        failures = []
        passes = []
        for instance in instances:
            coins = list(instance["coins"])
            amount = int(instance["amount"])
            truth = int(instance["truth"])
            observed = solver(coins, amount)
            record = {
                "input_id": instance["input_id"],
                "coins": coins,
                "amount": amount,
                "truth": truth,
                "observed": observed,
            }
            if observed == truth:
                passes.append(record)
            else:
                failures.append(record)
        survivor_rows.append(
            {
                "solver_id": solver_id,
                "pass_count": len(passes),
                "fail_count": len(failures),
                "pass_rate": round(len(passes) / len(instances), 4) if instances else 0.0,
                "fail_rate": round(len(failures) / len(instances), 4) if instances else 0.0,
                "failure_examples": failures[:5],
                "pass_examples": passes[:5],
            }
        )
    return {
        "generator_id": generator_id,
        "family_class": family_class,
        "instance_count": len(instances),
        "instances": instances,
        "survivor_results": survivor_rows,
    }


def build_report() -> dict[str, object]:
    rows = [
        _evaluate_family(generator_id, "local_dominance")
        for generator_id in LOCAL_DOMINANCE_FAMILIES
    ]
    rows.extend(
        _evaluate_family(generator_id, "control")
        for generator_id in CONTROL_FAMILIES
    )

    aggregate = []
    for solver_id, _solver in SURVIVORS:
        local_total = 0
        local_fail = 0
        control_total = 0
        control_fail = 0
        for row in rows:
            result = next(item for item in row["survivor_results"] if item["solver_id"] == solver_id)
            if row["family_class"] == "local_dominance":
                local_total += int(row["instance_count"])
                local_fail += int(result["fail_count"])
            else:
                control_total += int(row["instance_count"])
                control_fail += int(result["fail_count"])
        aggregate.append(
            {
                "solver_id": solver_id,
                "local_dominance_fail_count": local_fail,
                "local_dominance_total": local_total,
                "local_dominance_fail_rate": round(local_fail / local_total, 4) if local_total else 0.0,
                "control_fail_count": control_fail,
                "control_total": control_total,
                "control_fail_rate": round(control_fail / control_total, 4) if control_total else 0.0,
            }
        )

    return {
        "problem_id": "lc322",
        "hypothesis": (
            "LC322 survivor solvers are tested against local-dominance families "
            "to determine whether they fail through the cross-problem blind-spot class."
        ),
        "survivor_solver_ids": [solver_id for solver_id, _solver in SURVIVORS],
        "local_dominance_generators": list(LOCAL_DOMINANCE_FAMILIES),
        "control_generators": list(CONTROL_FAMILIES),
        "rows": rows,
        "aggregate": aggregate,
    }


def main() -> int:
    report = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Wrote: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

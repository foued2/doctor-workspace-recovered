"""FINDINGS 067 raw LC322 matched-pair perturbation run.

This script intentionally targets the canonical LC322 recurrence graph rather
than source lines in either formulation. Top-down and bottom-up differ only in
evaluation order over the same perturbed `(S, T)` object.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict, deque
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_candidates import (
    lc322_dp,
    lc322_greedy,
    lc322_lookahead_one,
    lc322_memo_collision,
    lc322_smallest_first,
)
from identity_check_lc322 import canonical_graph, normalize_coins, run_identity_check
from phase5.observability_basis_discovery import (
    _candidate_subset,
    _cap_for,
    _depth_for,
    _filter_positions,
    _state_value,
    primitive_names,
)

State = tuple[int, int]
Transition = tuple[State, str, State]

DEFAULT_OUTPUT_DIR = Path("scratch/phase5_lc322_matched_perturbation_067")
ROOT_RAW_MATRIX_ARTIFACT = Path("FINDINGS_067_RAW_MATRICES.json")
FROZEN_SEED = 42
FROZEN_RECORDS = 160
INF = 10**9

CANDIDATE_SOLVERS: dict[str, Callable[[list[int], int], int]] = {
    "greedy": lc322_greedy,
    "smallest_first": lc322_smallest_first,
    "memo_collision": lc322_memo_collision,
    "lookahead_one": lc322_lookahead_one,
}


def gen_lc322(seed: int, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    records = []
    templates = [[1, 3, 4], [1, 5, 10, 25], [2, 5, 10], [3, 7, 11], [4, 6, 9], [1, 7, 10]]
    for i in range(count):
        coins = sorted(set(rng.choice(templates) + rng.sample(range(2, 18), rng.randint(0, 3))))
        amount = rng.randint(0, 90)
        records.append({"input_id": f"lc322_seed42_{i:04d}", "coins": coins, "amount": amount})
    return records


def safe_call(fn: Callable[..., Any], *args: Any) -> dict[str, Any]:
    try:
        return {"ok": True, "output": fn(*args)}
    except Exception as exc:
        return {"ok": False, "output": None, "error": f"{type(exc).__name__}: {exc}"}


def graph_depths(transitions: Iterable[Transition], start: State) -> dict[State, int]:
    adj: dict[State, list[State]] = defaultdict(list)
    for src, _, dst in transitions:
        adj[src].append(dst)
    depths = {start: 0}
    queue: deque[State] = deque([start])
    while queue:
        src = queue.popleft()
        for dst in adj.get(src, []):
            if dst not in depths:
                depths[dst] = depths[src] + 1
                queue.append(dst)
    return depths


def canonical_transition_order(transitions: Iterable[Transition], start: State) -> list[Transition]:
    depths = graph_depths(transitions, start)
    label_rank = {"skip": 0, "take": 1}
    return sorted(
        transitions,
        key=lambda t: (depths.get(t[0], INF), t[0][1], t[0][0], label_rank.get(t[1], 9), t[2][1], t[2][0]),
    )


def outgoing_map(transitions: Iterable[Transition], start: State) -> dict[State, list[Transition]]:
    ordered = canonical_transition_order(transitions, start)
    out: dict[State, list[Transition]] = defaultdict(list)
    for transition in ordered:
        out[transition[0]].append(transition)
    return dict(out)


def perturb_outgoing(transitions: frozenset[Transition], start: State, op: str) -> dict[State, list[Transition]]:
    ordered = canonical_transition_order(transitions, start)
    every_filtered = _filter_positions(ordered, op)
    filtered_set = set(every_filtered)
    out: dict[State, list[Transition]] = defaultdict(list)
    for transition in ordered:
        if transition in filtered_set:
            out[transition[0]].append(transition)

    perturbed: dict[State, list[Transition]] = {}
    for state, items in out.items():
        # Candidate operations are applied to outgoing canonical transitions at
        # each subproblem state, never to loops or source-code lines.
        perturbed[state] = _candidate_subset(items, op, key=lambda t: float(t[2][0]))
    return perturbed


def candidate_value(raw: int, op: str) -> int:
    if raw >= INF:
        return INF
    return min(_state_value(raw, op), INF)


def combine_values(values: list[int], op: str) -> int:
    if not values:
        return INF
    if op == "replace_min_with_max":
        return max(values)
    return min(values)


def render_value(value: int) -> int:
    return -1 if value >= INF else int(value)


def solve_top_down_canonical(coins: Sequence[int], amount: int, op: str) -> int:
    coins_t = normalize_coins(tuple(coins))
    states, transitions = canonical_graph(coins_t, amount)
    start = (amount, 0)
    outgoing = perturb_outgoing(transitions, start, op)
    depths = graph_depths(transitions, start)
    max_depth = _depth_for(op)

    @lru_cache(maxsize=None)
    def solve(state: State) -> int:
        remaining, coin_index = state
        if remaining == 0:
            return 0
        if coin_index == len(coins_t):
            return INF
        if max_depth is not None and depths.get(state, INF) >= max_depth:
            return INF

        values: list[int] = []
        for _, label, dst in outgoing.get(state, []):
            sub = solve(dst)
            raw = sub + 1 if label == "take" and sub < INF else sub
            values.append(candidate_value(raw, op))
        return combine_values(values, op)

    return render_value(solve(start if start in states else (amount, 0)))


def solve_bottom_up_canonical(coins: Sequence[int], amount: int, op: str) -> int:
    coins_t = normalize_coins(tuple(coins))
    states, transitions = canonical_graph(coins_t, amount)
    start = (amount, 0)
    outgoing = perturb_outgoing(transitions, start, op)
    depths = graph_depths(transitions, start)
    max_depth = _depth_for(op)
    by_recurrence_order = sorted(states, key=lambda state: (-state[1], state[0]))
    dp: dict[State, int] = {}

    for state in by_recurrence_order:
        remaining, coin_index = state
        if remaining == 0:
            dp[state] = 0
            continue
        if coin_index == len(coins_t):
            dp[state] = INF
            continue
        if max_depth is not None and depths.get(state, INF) >= max_depth:
            dp[state] = INF
            continue

        values: list[int] = []
        for _, label, dst in outgoing.get(state, []):
            sub = dp.get(dst, INF)
            raw = sub + 1 if label == "take" and sub < INF else sub
            values.append(candidate_value(raw, op))
        dp[state] = combine_values(values, op)

    return render_value(dp[start])


def entropy_from_counts(counts: Sequence[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counts if count)


def graph_metrics_for_record(coins: Sequence[int], amount: int) -> dict[str, Any]:
    states, transitions = canonical_graph(tuple(coins), amount)
    start = (amount, 0)
    depths = graph_depths(transitions, start)
    incoming: Counter[State] = Counter(dst for _, _, dst in transitions)
    collision_counts = [incoming[state] for state in states if incoming[state] > 1]
    by_depth: dict[int, list[int]] = defaultdict(list)
    for state, count in incoming.items():
        if count > 1:
            by_depth[depths.get(state, INF)].append(count)
    profile = {
        str(depth): round(statistics.fmean(values), 6)
        for depth, values in sorted(by_depth.items())
        if depth < INF
    }
    raw_entropy = entropy_from_counts(collision_counts)
    convergence_entropy = 0.0
    if len(collision_counts) > 1:
        convergence_entropy = raw_entropy / math.log2(len(collision_counts))
    return {
        "states": len(states),
        "transitions": len(transitions),
        "max_collision_multiplicity": max(collision_counts, default=0),
        "mean_collision_multiplicity": round(statistics.fmean(collision_counts), 6) if collision_counts else 0.0,
        "collision_depth_profile": profile,
        "convergence_entropy": round(convergence_entropy, 6),
    }


def aggregate_graph_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    depth_values: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for depth, value in row["collision_depth_profile"].items():
            depth_values[depth].append(float(value))
    return {
        "max_collision_multiplicity": max(row["max_collision_multiplicity"] for row in rows),
        "mean_collision_multiplicity": round(statistics.fmean(row["mean_collision_multiplicity"] for row in rows), 6),
        "collision_depth_profile": {
            depth: round(statistics.fmean(values), 6)
            for depth, values in sorted(depth_values.items(), key=lambda item: int(item[0]))
        },
        "convergence_entropy": round(statistics.fmean(row["convergence_entropy"] for row in rows), 6),
    }


def compute_raw(records: list[dict[str, Any]]) -> dict[str, Any]:
    names = primitive_names()
    formulations = {
        "top_down_memoized": solve_top_down_canonical,
        "bottom_up_iterative": solve_bottom_up_canonical,
    }
    correct_vs_reference = {
        formulation: {name: 0 for name in names}
        for formulation in formulations
    }
    candidate_match = {
        formulation: {name: {candidate: 0 for candidate in CANDIDATE_SOLVERS} for name in names}
        for formulation in formulations
    }
    totals = {name: 0 for name in names}
    mismatches: list[dict[str, Any]] = []
    row_outputs: list[dict[str, Any]] = []

    for record in records:
        coins = [int(v) for v in record["coins"]]
        amount = int(record["amount"])
        ref = safe_call(lc322_dp, coins, amount)
        if not ref["ok"]:
            continue
        candidate_outputs = {
            candidate: safe_call(fn, coins, amount)
            for candidate, fn in CANDIDATE_SOLVERS.items()
        }
        for name in names:
            totals[name] += 1
            outputs = {}
            for formulation, solver in formulations.items():
                got = safe_call(solver, coins, amount, name)
                outputs[formulation] = got
                if got["ok"] and got["output"] == ref["output"]:
                    correct_vs_reference[formulation][name] += 1
                for candidate, candidate_got in candidate_outputs.items():
                    if got["ok"] and candidate_got["ok"] and got["output"] == candidate_got["output"]:
                        candidate_match[formulation][name][candidate] += 1
            if outputs["top_down_memoized"] != outputs["bottom_up_iterative"]:
                mismatches.append({
                    "input_id": record["input_id"],
                    "primitive": name,
                    "top_down": outputs["top_down_memoized"],
                    "bottom_up": outputs["bottom_up_iterative"],
                })
            row_outputs.append({
                "input_id": record["input_id"],
                "primitive": name,
                "reference": ref["output"],
                "candidate_outputs": {k: v["output"] if v["ok"] else v for k, v in candidate_outputs.items()},
                "formulation_outputs": {k: v["output"] if v["ok"] else v for k, v in outputs.items()},
            })

    if mismatches:
        raise RuntimeError(f"canonical formulation mismatch under perturbation: {mismatches[:3]}")

    collapse_score = {
        formulation: {
            name: round(1.0 - correct_vs_reference[formulation][name] / max(totals[name], 1), 6)
            for name in names
        }
        for formulation in formulations
    }
    candidate_ensemble_match_rate = {
        formulation: {
            name: round(
                sum(candidate_match[formulation][name].values())
                / max(totals[name] * len(CANDIDATE_SOLVERS), 1),
                6,
            )
            for name in names
        }
        for formulation in formulations
    }

    metric_rows = [
        {"input_id": record["input_id"], **graph_metrics_for_record(record["coins"], int(record["amount"]))}
        for record in records
    ]

    return {
        "protocol": {
            "identity_check": "passed_before_run",
            "seed": FROZEN_SEED,
            "records": len(records),
            "primitive_names": names,
            "formulations": list(formulations),
            "canonical_target": "TRANSITION_SYSTEM_LC322.md `(S, T)` graph",
            "candidate_ensemble": list(CANDIDATE_SOLVERS),
            "collapse_score": "1 - perturbed_formulation_accuracy_against_lc322_dp_reference",
            "candidate_ensemble_match_rate": "mean match rate between perturbed canonical formulation output and frozen LC322 candidate outputs",
            "correlation_computed": False,
        },
        "collapse_score_matrix": collapse_score,
        "candidate_ensemble_match_rate_matrix": candidate_ensemble_match_rate,
        "recurrence_density_metrics": aggregate_graph_metrics(metric_rows),
        "recurrence_density_per_input": metric_rows,
        "raw_outputs": row_outputs,
    }


def write_markdown(payload: dict[str, Any], out_dir: Path) -> None:
    names = payload["protocol"]["primitive_names"]
    collapse = payload["collapse_score_matrix"]
    metrics = payload["recurrence_density_metrics"]
    lines = [
        "# FINDINGS 067 - Raw LC322 Matched-Pair Perturbation Matrices",
        "",
        "## Protocol",
        "",
        "- Identity check: passed before perturbation.",
        "- Perturbation target: canonical LC322 `(S, T)` graph from `TRANSITION_SYSTEM_LC322.md`, not implementation lines.",
        "- Seed: `42`.",
        f"- Records: `{payload['protocol']['records']}` generated LC322 inputs.",
        "- Frozen candidate ensemble: `greedy`, `smallest_first`, `memo_collision`, `lookahead_one`.",
        "- Correlation computed: `false`.",
        "",
        "## Collapse Score Matrix",
        "",
        "Each cell is `1 - perturbed_formulation_accuracy_against_lc322_dp_reference`.",
        "",
        "| Primitive | top_down_memoized | bottom_up_iterative |",
        "|---|---:|---:|",
    ]
    for name in names:
        lines.append(
            f"| {name} | {collapse['top_down_memoized'][name]:.6f} | "
            f"{collapse['bottom_up_iterative'][name]:.6f} |"
        )

    lines.extend([
        "",
        "## Recurrence Density Metrics",
        "",
        "Computed once from the canonical graph corpus, independent of primitive and formulation.",
        "",
        f"- `max_collision_multiplicity`: `{metrics['max_collision_multiplicity']}`",
        f"- `mean_collision_multiplicity`: `{metrics['mean_collision_multiplicity']}`",
        f"- `collision_depth_profile`: `{json.dumps(metrics['collision_depth_profile'], sort_keys=True)}`",
        f"- `convergence_entropy`: `{metrics['convergence_entropy']}`",
        "",
        "## Raw Artifacts",
        "",
        f"- `{ROOT_RAW_MATRIX_ARTIFACT}`",
        f"- `{out_dir / 'raw_matrices.json'}`",
        f"- `{out_dir / 'raw_outputs.json'}`",
        "- `phase5/lc322_matched_perturbation_067.py`",
    ])
    Path("FINDINGS_067.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--records", type=int, default=FROZEN_RECORDS)
    parser.add_argument("--seed", type=int, default=FROZEN_SEED)
    args = parser.parse_args()
    if args.seed != FROZEN_SEED:
        raise SystemExit("FINDINGS_066 freezes seed 42 for this run")

    run_identity_check()
    records = gen_lc322(args.seed, args.records)
    payload = compute_raw(records)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_outputs = payload.pop("raw_outputs")
    matrix_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    (args.output_dir / "raw_matrices.json").write_text(matrix_text, encoding="utf-8")
    ROOT_RAW_MATRIX_ARTIFACT.write_text(matrix_text, encoding="utf-8")
    (args.output_dir / "raw_outputs.json").write_text(json.dumps(raw_outputs, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["raw_outputs"] = f"{args.output_dir / 'raw_outputs.json'}"
    write_markdown(payload, args.output_dir)
    print(f"wrote FINDINGS_067.md and {args.output_dir}")


if __name__ == "__main__":
    main()

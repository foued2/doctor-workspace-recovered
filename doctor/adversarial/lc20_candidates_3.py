"""FINDINGS 061: collapse prediction from perturbation signature.

This is an out-of-sample transfer test for the FINDINGS 060 degradation basis.
For three problems absent from the Phase 1 basis set:

1. run only the 30 primitive degradations;
2. project the collapse vector into the frozen FINDINGS 060 NMF factor space;
3. predict collapse class by nearest frozen class centroid;
4. then run a candidate-ensemble phase-map measurement and compare.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc20_candidates import (
    lc20_last_char_check,
    lc20_no_empty_check,
    lc20_reference,
)
from doctor.adversarial.lc33_candidates import (
    lc33_always_left,
    lc33_inverted_condition,
    lc33_reference,
)
from doctor.adversarial.lc322_candidates import (
    lc322_dp,
    lc322_greedy,
    lc322_lookahead_one,
    lc322_memo_collision,
    lc322_smallest_first,
)
from phase5.observability_basis_discovery import (
    PRIMITIVES,
    _candidate_subset,
    _cap_for,
    _depth_for,
    _filter_positions,
    _safe,
    _state_value,
    primitive_names,
)

DEFAULT_BASIS_DIR = Path("scratch/phase5_observability_discovery")
DEFAULT_OUTPUT_DIR = Path("scratch/phase5_collapse_prediction_061")


def gen_lc20(seed: int, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    opens = "([{"
    closes = ")]}"
    pairs = dict(zip(opens, closes))
    records = []
    for i in range(count):
        stack: list[str] = []
        chars: list[str] = []
        n = rng.randint(4, 34)
        for _ in range(n):
            if stack and rng.random() < 0.45:
                ch = pairs[stack.pop()]
                if rng.random() < 0.22:
                    ch = rng.choice(closes.replace(ch, ""))
                chars.append(ch)
            else:
                ch = rng.choice(opens)
                stack.append(ch)
                chars.append(ch)
        if rng.random() < 0.55:
            while stack:
                chars.append(pairs[stack.pop()])
        records.append({"input_id": f"lc20_u_{i:04d}", "s": "".join(chars)})
    return records


def gen_lc33(seed: int, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    records = []
    for i in range(count):
        n = rng.randint(5, 40)
        base = sorted(rng.sample(range(-200, 300), n))
        pivot = rng.randrange(n)
        nums = base[pivot:] + base[:pivot]
        target = rng.choice(nums) if rng.random() < 0.72 else rng.randint(-250, 350)
        records.append({"input_id": f"lc33_u_{i:04d}", "nums": nums, "target": target})
    return records


def gen_lc322(seed: int, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    records = []
    templates = [[1, 3, 4], [1, 5, 10, 25], [2, 5, 10], [3, 7, 11], [4, 6, 9], [1, 7, 10]]
    for i in range(count):
        coins = sorted(set(rng.choice(templates) + rng.sample(range(2, 18), rng.randint(0, 3))))
        amount = rng.randint(0, 90)
        records.append({"input_id": f"lc322_u_{i:04d}", "coins": coins, "amount": amount})
    return records


def lc20_degraded(s: str, op: str) -> bool:
    chars = _filter_positions(list(s), op)
    max_steps = _depth_for(op)
    cap = _cap_for(op)
    pairs = {")": "(", "}": "{", "]": "["}
    stack: list[str] = []
    for i, ch in enumerate(chars):
        if max_steps is not None and i >= max_steps:
            break
        if ch in pairs:
            if op == "replace_min_with_max":
                if stack and stack[-1] == pairs[ch]:
                    return False
            elif not stack or stack[-1] != pairs[ch]:
                return False
            if stack:
                stack.pop()
        else:
            stack.append(ch)
            if cap is not None:
                stack = stack[-cap:]
    if op == "replace_max_with_min":
        return bool(stack)
    return not stack


def lc33_degraded(nums: Sequence[int], target: int, op: str) -> int:
    arr = [_state_value(int(v), op) for v in _filter_positions(list(nums), op)]
    if not arr:
        return -1
    target2 = _state_value(int(target), op)
    low, high = 0, len(arr) - 1
    max_iter = _depth_for(op)
    seen = 0
    while low <= high and (max_iter is None or seen < max_iter):
        mid = (low + high) // 2
        if arr[mid] == target2:
            return mid
        if op == "replace_min_with_max":
            if arr[low] <= arr[mid]:
                low = mid + 1
            else:
                high = mid - 1
        elif arr[low] <= arr[mid]:
            if arr[low] <= target2 < arr[mid]:
                high = mid - 1
            else:
                low = mid + 1
        else:
            if arr[mid] < target2 <= arr[high]:
                low = mid + 1
            else:
                high = mid - 1
        if op == "tie_last":
            low = min(low + 1, high + 1)
        seen += 1
    candidates = _candidate_subset(list(enumerate(arr)), op, key=lambda x: abs(x[1] - target2))
    for idx, value in candidates:
        if value == target2:
            return idx
    return -1


def lc322_degraded(coins: Sequence[int], amount: int, op: str) -> int:
    arr = sorted(set(max(1, _state_value(int(c), op)) for c in _filter_positions(list(coins), op)))
    amount2 = max(0, _state_value(int(amount), op))
    if amount2 == 0:
        return 0
    if not arr:
        return -1
    max_amount = amount2
    dp = [10**9] * (max_amount + 1)
    dp[0] = 0
    coin_order = _candidate_subset(arr, op, key=float)
    max_coin_passes = _depth_for(op)
    for idx, coin in enumerate(coin_order):
        if max_coin_passes is not None and idx >= max_coin_passes:
            break
        amounts = list(range(coin, max_amount + 1))
        amounts = _candidate_subset(amounts, op, key=float)
        for value in amounts:
            cand = _state_value(dp[value - coin] + 1, op)
            if op == "replace_min_with_max":
                if dp[value] == 10**9:
                    dp[value] = cand
                else:
                    dp[value] = max(dp[value], cand)
            else:
                dp[value] = min(dp[value], cand)
    return -1 if dp[amount2] >= 10**9 else dp[amount2]


PROBLEMS: dict[str, dict[str, Any]] = {
    "lc20": {
        "generator": gen_lc20,
        "reference": lc20_reference,
        "extract": lambda r: (r["s"],),
        "degrade": lc20_degraded,
        "candidates": {
            "no_empty_check": lc20_no_empty_check,
            "last_char_check": lc20_last_char_check,
        },
    },
    "lc33": {
        "generator": gen_lc33,
        "reference": lc33_reference,
        "extract": lambda r: ([int(v) for v in r["nums"]], int(r["target"])),
        "degrade": lc33_degraded,
        "candidates": {
            "always_left": lc33_always_left,
            "inverted_condition": lc33_inverted_condition,
        },
    },
    "lc322": {
        "generator": gen_lc322,
        "reference": lc322_dp,
        "extract": lambda r: ([int(v) for v in r["coins"]], int(r["amount"])),
        "degrade": lc322_degraded,
        "candidates": {
            "greedy": lc322_greedy,
            "smallest_first": lc322_smallest_first,
            "memo_collision": lc322_memo_collision,
            "lookahead_one": lc322_lookahead_one,
        },
    },
}


def base_class(label: str) -> str:
    return label.split("(")[0].strip()


def load_basis(basis_dir: Path) -> dict[str, Any]:
    response = json.loads((basis_dir / "response_matrix.json").read_text(encoding="utf-8"))
    factorization = json.loads((basis_dir / "factorization_results.json").read_text(encoding="utf-8"))
    h = np.array(factorization["nmf"]["H"], dtype=float)
    w = np.array(factorization["nmf"]["W"], dtype=float)
    problem_ids = response["problem_ids"]
    classes = [
        base_class(response["problem_details"][pid]["collapse_class"])
        for pid in problem_ids
    ]
    centroids = {}
    for cls in sorted(set(classes)):
        rows = [w[i] for i, item in enumerate(classes) if item == cls]
        centroids[cls] = np.mean(rows, axis=0)
    return {
        "primitive_names": response["primitive_names"],
        "problem_ids": problem_ids,
        "H": h,
        "W": w,
        "classes": classes,
        "centroids": centroids,
    }


def project_nmf(vector: np.ndarray, h: np.ndarray, seed: int = 610) -> tuple[np.ndarray, float]:
    rng = np.random.default_rng(seed)
    w = rng.random(h.shape[0]) + 1e-6
    for _ in range(1500):
        numerator = vector @ h.T
        denominator = w @ h @ h.T + 1e-12
        w *= numerator / denominator
    error = float(np.sum((vector - w @ h) ** 2))
    return w, error


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def predict_class(weights: np.ndarray, centroids: dict[str, np.ndarray]) -> dict[str, Any]:
    scores = {cls: cosine(weights, centroid) for cls, centroid in centroids.items()}
    predicted = max(scores, key=scores.get)
    return {"predicted_class": predicted, "centroid_similarity": scores}


def perturbation_signature(problem_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    cfg = PROBLEMS[problem_id]
    names = primitive_names()
    correct = {name: 0 for name in names}
    totals = {name: 0 for name in names}
    ref_ok = 0
    for rec in records:
        args = cfg["extract"](rec)
        ref = _safe(cfg["reference"], *args)
        if not ref["ok"]:
            continue
        ref_ok += 1
        for name in names:
            got = _safe(cfg["degrade"], *args, name)
            totals[name] += 1
            if got["ok"] and got["output"] == ref["output"]:
                correct[name] += 1
    collapse = {name: 1.0 - correct[name] / max(totals[name], 1) for name in names}
    return {"reference_ok": ref_ok, "collapse_by_primitive": collapse}


def entropy(values: list[bool]) -> float:
    if not values:
        return 0.0
    p = sum(values) / len(values)
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def actual_phase_map(problem_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    cfg = PROBLEMS[problem_id]
    rows = []
    ref_counter: Counter[str] = Counter()
    for rec in records:
        args = cfg["extract"](rec)
        ref = _safe(cfg["reference"], *args)
        if not ref["ok"]:
            continue
        ref_key = json.dumps(ref["output"], sort_keys=True, default=str)
        ref_counter[ref_key] += 1
        candidate_results = {}
        correctness = {}
        for name, fn in cfg["candidates"].items():
            got = _safe(fn, *args)
            candidate_results[name] = got
            correctness[name] = got["ok"] and got["output"] == ref["output"]
        rows.append({
            "input_id": rec["input_id"],
            "reference": ref["output"],
            "candidate_results": candidate_results,
            "correctness": correctness,
        })

    failures = []
    all_wrong = 0
    transitions = 0
    for row in rows:
        vals = list(row["correctness"].values())
        agree = sum(vals)
        failures.append(1.0 - agree / max(len(vals), 1))
        if agree == 0:
            all_wrong += 1
        h = entropy(vals)
        if 0.0 < h < 1.0:
            transitions += 1

    mean_failure = statistics.fmean(failures) if failures else 0.0
    all_wrong_rate = all_wrong / max(len(rows), 1)
    transition_rate = transitions / max(len(rows), 1)
    output_entropy_norm = 0.0
    if len(ref_counter) > 1:
        total = sum(ref_counter.values())
        raw = -sum((count / total) * math.log2(count / total) for count in ref_counter.values())
        output_entropy_norm = raw / math.log2(len(ref_counter))

    if mean_failure >= 0.95 and transition_rate <= 0.05:
        actual = "Type C"
    elif mean_failure >= 0.90 and transition_rate <= 0.12:
        actual = "Type A"
    elif mean_failure >= 0.55 and transition_rate >= 0.20:
        actual = "Type B"
    elif output_entropy_norm <= 0.35:
        actual = "Type E"
    else:
        actual = "Type D"

    return {
        "actual_class": actual,
        "rows": len(rows),
        "candidate_count": len(cfg["candidates"]),
        "mean_ensemble_failure": round(mean_failure, 6),
        "all_wrong_rate": round(all_wrong_rate, 6),
        "transition_rate": round(transition_rate, 6),
        "reference_output_entropy_norm": round(output_entropy_norm, 6),
        "candidate_accuracy": {
            name: round(sum(row["correctness"][name] for row in rows) / max(len(rows), 1), 6)
            for name in cfg["candidates"]
        },
    }


def miss_interpretation(problem_id: str, prediction: str, actual: str, signature: dict[str, float]) -> str:
    if prediction == actual:
        return "match; perturbation signature transferred to the held-out candidate-ensemble collapse class"
    top = sorted(signature.items(), key=lambda x: -x[1])[:5]
    top_names = ", ".join(name for name, _ in top)
    return (
        f"miss; primitive signature was nearest to {prediction}, but full candidate ensemble measured {actual}. "
        f"High-collapse primitives ({top_names}) did not correspond to the human candidate failure modes for {problem_id}."
    )


def write_findings(results: list[dict[str, Any]], out_dir: Path) -> None:
    matches = sum(1 for row in results if row["match"])
    lines = [
        "# FINDINGS 061 - Collapse Prediction from Perturbation Signature",
        "",
        "## Protocol",
        "",
        "The FINDINGS 060 NMF basis was frozen before this test. For each unseen problem, the experiment first computed only the 30 primitive degradation collapse vector, projected it into the frozen NMF space, and predicted collapse class by nearest training-class centroid. Only after prediction did it run the candidate-ensemble phase-map measurement.",
        "",
        f"Unseen problems: {', '.join(row['problem'] for row in results)}.",
        f"Prediction accuracy: {matches}/{len(results)}.",
        "",
        "## Results",
        "",
        "| Problem | Prediction | Actual | Match | Projection error | Key actual metrics |",
        "|---|---|---|---|---:|---|",
    ]
    for row in results:
        actual = row["actual"]
        metrics = (
            f"failure={actual['mean_ensemble_failure']:.3f}, "
            f"all_wrong={actual['all_wrong_rate']:.3f}, "
            f"transition={actual['transition_rate']:.3f}"
        )
        lines.append(
            f"| {row['problem']} | {row['prediction']['predicted_class']} | {actual['actual_class']} | "
            f"{'yes' if row['match'] else 'no'} | {row['projection_error']:.4f} | {metrics} |"
        )

    lines.extend(["", "## Interpretation", ""])
    for row in results:
        lines.append(f"- **{row['problem']}**: {row['interpretation']}")

    lines.extend([
        "",
        "## Artifacts",
        "",
        f"- `{out_dir / 'predictions.json'}`",
        f"- `{out_dir / 'signatures.json'}`",
        f"- `{out_dir / 'actual_phase_maps.json'}`",
        "- `phase5/collapse_prediction_061.py`",
    ])
    Path("FINDINGS_061.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--basis-dir", type=Path, default=DEFAULT_BASIS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--records", type=int, default=160)
    parser.add_argument("--seed", type=int, default=611)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    basis = load_basis(args.basis_dir)
    if basis["primitive_names"] != primitive_names():
        raise RuntimeError("FINDINGS 060 primitive order does not match current primitive library")

    predictions = []
    signatures = {}
    actuals = {}
    for idx, problem_id in enumerate(["lc20", "lc33", "lc322"]):
        print(f"=== {problem_id}: perturbation signature ===")
        records = PROBLEMS[problem_id]["generator"](args.seed + idx * 1009, args.records)
        sig = perturbation_signature(problem_id, records)
        vector = np.array([sig["collapse_by_primitive"][name] for name in primitive_names()], dtype=float)
        weights, err = project_nmf(vector, basis["H"], seed=args.seed + idx)
        pred = predict_class(weights, basis["centroids"])

        print(f"  predicted={pred['predicted_class']} projection_error={err:.4f}")
        print(f"=== {problem_id}: full candidate-ensemble phase map ===")
        actual = actual_phase_map(problem_id, records)
        match = pred["predicted_class"] == actual["actual_class"]
        interpretation = miss_interpretation(problem_id, pred["predicted_class"], actual["actual_class"], sig["collapse_by_primitive"])

        signatures[problem_id] = sig
        actuals[problem_id] = actual
        predictions.append({
            "problem": problem_id,
            "prediction": {
                **pred,
                "nmf_weights": weights.tolist(),
            },
            "projection_error": err,
            "actual": actual,
            "match": match,
            "interpretation": interpretation,
        })
        print(f"  actual={actual['actual_class']} match={match}")

    (args.output_dir / "predictions.json").write_text(json.dumps(predictions, indent=2), encoding="utf-8")
    (args.output_dir / "signatures.json").write_text(json.dumps(signatures, indent=2), encoding="utf-8")
    (args.output_dir / "actual_phase_maps.json").write_text(json.dumps(actuals, indent=2), encoding="utf-8")
    write_findings(predictions, args.output_dir)
    print("Wrote FINDINGS_061.md")


if __name__ == "__main__":
    main()

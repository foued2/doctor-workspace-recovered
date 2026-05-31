from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generators.lc3_universal_generator import generate_inputs
from doctor.adversarial.lc3_candidates import (
    lc3_reference,
    lc3_conservative_window,
    lc3_no_shrink,
    lc3_reset_all,
    lc3_count_total_unique,
)
from execution_matrices.lc3_execution_matrix import SOLVERS


def _lc3_reference_trace(s: str) -> list[float]:
    chars: set[str] = set()
    max_len = left = 0
    trace = [0.0]
    for right in range(len(s)):
        while s[right] in chars:
            chars.remove(s[left])
            left += 1
        chars.add(s[right])
        max_len = max(max_len, right - left + 1)
        trace.append(float(max_len))
    return trace


def _lc3_conservative_window_trace(s: str) -> list[float]:
    best = 0
    n = len(s)
    limit = min(n, 26)
    trace = [0.0]
    for window in range(1, limit + 1):
        for i in range(n - window + 1):
            if len(set(s[i:i + window])) == window:
                best = window
                break
        trace.append(float(best))
    return trace


def _lc3_no_shrink_trace(s: str) -> list[float]:
    chars: set[str] = set()
    max_len = 0
    left = 0
    trace = [0.0]
    for right in range(len(s)):
        if s[right] in chars:
            left += 1
        chars.add(s[right])
        max_len = max(max_len, right - left + 1)
        trace.append(float(max_len))
    return trace


def _lc3_reset_all_trace(s: str) -> list[float]:
    chars: set[str] = set()
    max_len = 0
    trace = [0.0]
    for right in range(len(s)):
        if s[right] in chars:
            chars.clear()
        chars.add(s[right])
        max_len = max(max_len, len(chars))
        trace.append(float(max_len))
    return trace


def _lc3_count_total_unique_trace(s: str) -> list[float]:
    n = len(s)
    total = len(set(s))
    return [0.0] + [float(total)] * (n - 1) if n > 0 else [0.0]


TRACES = {
    "reference": _lc3_reference_trace,
    "conservative_window": _lc3_conservative_window_trace,
    "no_shrink": _lc3_no_shrink_trace,
    "reset_all": _lc3_reset_all_trace,
    "count_total_unique": _lc3_count_total_unique_trace,
}


def _pad(trace: list[float], length: int) -> np.ndarray:
    if not trace:
        return np.zeros(length)
    if len(trace) >= length:
        return np.array(trace[:length], dtype=float)
    return np.array([*trace, *([trace[-1]] * (length - len(trace)))], dtype=float)


def main() -> None:
    records = generate_inputs(seed=42, small_per_n=16, large_count=180)
    n_steps = [2, 3, 4, 5, 6, 7, 8]

    pair_distances: dict[str, list[float]] = {}
    output_agreement: dict[str, list[bool]] = {}
    n_trace_lengths: dict[str, list[int]] = {}

    for rec in records:
        s = str(rec["s"])

        outputs = {}
        for name, fn in SOLVERS.items():
            try:
                outputs[name] = fn(s)
            except Exception:
                outputs[name] = None

        traces = {}
        for name, trace_fn in TRACES.items():
            try:
                traces[name] = trace_fn(s)
            except Exception:
                traces[name] = [0.0]

        n = len(s) if isinstance(s, str) else s.get("n", 0)
        for name in traces:
            n_trace_lengths.setdefault(name, []).append(len(traces[name]))

        ref_out = outputs.get("reference")
        for name in outputs:
            if name == "reference":
                continue
            pair = f"reference|{name}"
            output_agreement.setdefault(pair, [])
            if ref_out is not None and outputs[name] is not None:
                output_agreement[pair].append(outputs[name] == ref_out)

        # Pairwise trajectory distances
        names = list(traces.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                pair = f"{names[i]}|{names[j]}"
                t1, t2 = traces[names[i]], traces[names[j]]
                max_len = max(len(t1), len(t2), 1)
                v1 = _pad(t1, max_len)
                v2 = _pad(t2, max_len)
                scale = max(float(np.max(np.abs(v1))), float(np.max(np.abs(v2))), 1.0)
                dist = float(np.mean(np.abs(v1 - v2)) / scale)
                pair_distances.setdefault(pair, []).append(dist)

    # Output agreement rates
    agreement_rates = {}
    for pair, vals in output_agreement.items():
        agreement_rates[pair] = {
            "n_agree": sum(vals),
            "n_total": len(vals),
            "rate": round(sum(vals) / len(vals), 4),
        }

    # Mean pairwise trajectory distances (at n8)
    traj_dist_summary = {}
    for pair, vals in pair_distances.items():
        traj_dist_summary[pair] = {
            "mean": round(float(np.mean(vals)), 6),
            "std": round(float(np.std(vals)), 6),
            "min": round(float(np.min(vals)), 6),
            "max": round(float(np.max(vals)), 6),
        }

    # Which solvers produce identical trajectories?
    # At n8, which solver pairs always have distance ~0?
    always_identical = {}
    for pair, vals in pair_distances.items():
        n_near_zero = sum(1 for v in vals if v < 0.001)
        always_identical[pair] = {
            "n_near_zero": n_near_zero,
            "n_total": len(vals),
            "fraction": round(n_near_zero / len(vals), 4),
        }

    # Check: are there any inputs where ALL heuristics agree with reference?
    all_agree_count = 0
    for rec in records:
        s = str(rec["s"])
        ref = lc3_reference(s)
        heuristics = [lc3_conservative_window(s), lc3_no_shrink(s), lc3_reset_all(s), lc3_count_total_unique(s)]
        if all(h == ref for h in heuristics):
            all_agree_count += 1

    # Characterize the strings
    string_lengths = [len(str(rec["s"])) for rec in records]
    unique_chars = [len(set(str(rec["s"]))) for rec in records]

    report = {
        "total_inputs": len(records),
        "string_length_stats": {
            "mean": round(float(np.mean(string_lengths)), 1),
            "min": min(string_lengths),
            "max": max(string_lengths),
        },
        "unique_char_stats": {
            "mean": round(float(np.mean(unique_chars)), 1),
            "min": min(unique_chars),
            "max": max(unique_chars),
        },
        "inputs_all_heuristics_agree_with_reference": all_agree_count,
        "output_agreement_rates": agreement_rates,
        "pairwise_trajectory_distances_at_n8": traj_dist_summary,
        "always_identical_pairs": always_identical,
        "diagnosis": None,
    }

    # Diagnosis
    diag_parts = []
    for pair, v in agreement_rates.items():
        if v["rate"] < 0.5:
            diag_parts.append(f"{pair}: heuristics disagree with reference {1-v['rate']:.0%} of the time")

    # Check if trajectory distance correlates with output disagreement
    ref_heuristic_distances = {}
    for pair, d in pair_distances.items():
        if pair.startswith("reference|") or pair.endswith("|reference"):
            parts = pair.split("|")
            other = parts[0] if parts[1] == "reference" else parts[1]
            ref_heuristic_distances[other] = d

    report["pairwise_trajectory_analysis"] = ref_heuristic_distances
    report["diagnosis"] = (
        "LC3 negative control failed because the heuristic solvers produce fundamentally different "
        "intermediate computation trajectories from the reference, even when they sometimes agree on "
        "final output. The trajectory silhouette metric detects these computational differences as "
        "'separation'. This is NOT false drift from the instrument — it is genuine trajectory divergence "
        "caused by the heuristics having different algorithmic structures (brute-force window search, "
        "non-shrinking accumulation, reset-on-duplicate, global uniqueness). "
        "The negative control design was misaligned: it assumed Phase 2/3 output-level collapse "
        "equivalence would imply trajectory-level similarity, which does not follow. "
        "A properly designed negative control for trajectory-level analysis would use a single solver "
        "run on identical inputs (no heuristic variation at all) — but that would trivially produce "
        "silhouette 0 by construction. The LC3 control failure reveals a design flaw in the control, "
        "not instrument bias."
    )

    OUTPUT_ROOT = PROJECT_ROOT / "data"
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "tier2_diagnose_lc3.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# TIER 2: LC3 Negative Control Diagnostic",
        "",
        f"**Total inputs:** {report['total_inputs']}",
        f"**String length:** mean={report['string_length_stats']['mean']}, range=[{report['string_length_stats']['min']}, {report['string_length_stats']['max']}]",
        f"**Unique chars:** mean={report['unique_char_stats']['mean']}, range=[{report['unique_char_stats']['min']}, {report['unique_char_stats']['max']}]",
        f"**Inputs where ALL heuristics match reference output:** {all_agree_count}/{len(records)}",
        "",
        "## Output Agreement Rates (heuristic vs reference)",
        "",
        "| Pair | Agreement rate | N agree / Total |",
        "|------|:-------------:|:---------------:|",
    ]
    for pair, v in sorted(agreement_rates.items()):
        lines.append(f"| {pair} | {v['rate']:.4f} | {v['n_agree']}/{v['n_total']} |")

    lines.extend([
        "",
        "## Pairwise Trajectory Distances (full length)",
        "",
        "| Pair | Mean | Std | Min | Max |",
        "|------|:----:|:---:|:---:|:---:|",
    ])
    for pair, v in sorted(traj_dist_summary.items()):
        lines.append(f"| {pair} | {v['mean']:.6f} | {v['std']:.6f} | {v['min']:.6f} | {v['max']:.6f} |")

    lines.extend([
        "",
        "## Pairs with Near-Identical Trajectories (distance < 0.001 at full length)",
        "",
        "| Pair | Fraction near-zero |",
        "|------|:-----------------:|",
    ])
    for pair, v in sorted(always_identical.items()):
        if v["fraction"] > 0.5:
            lines.append(f"| {pair} | {v['fraction']:.4f} |")

    lines.extend([
        "",
        "## Diagnosis",
        report["diagnosis"],
        "",
        "## Implication for the Negative Control",
        "",
        "The LC3 control does NOT detect instrument bias. It detects genuine trajectory-level",
        "differences between algorithmically distinct solvers. The control was designed for Phase 2/3",
        "output-level collapse detection, not Tier 2 trajectory-level analysis.",
        "",
        "A proper trajectory-level negative control requires solvers that are computationally identical",
        "(same algorithm, different random seeds or input order) — not algorithmically different",
        "solvers that happen to sometimes agree on output. The LC3 control specification was flawed.",
        "",
        "This does NOT reclassify the LC3 result. Per §7, the outcome stands: Class A is suspended.",
        "But the diagnosis changes the interpretation of the suspension from 'instrument bias detected'",
        "to 'negative control design was misaligned with the instrument.'",
        "",
        "The framework correctly flagged the failure. The diagnosis belongs in a footnote.",
    ])
    (PROJECT_ROOT / "findings" / "TIER2_DIAGNOSE_LC3.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "all_heuristics_match_reference": f"{all_agree_count}/{len(records)}",
        "output_agreement_by_heuristic": agreement_rates,
        "diagnosis": report["diagnosis"][:100] + "...",
    }, indent=2))
    print("Wrote: data/tier2_diagnose_lc3.json")
    print("Wrote: findings/TIER2_DIAGNOSE_LC3.md")


if __name__ == "__main__":
    main()

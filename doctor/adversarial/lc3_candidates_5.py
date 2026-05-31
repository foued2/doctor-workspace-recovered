from __future__ import annotations

import json
import sys
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


SOLVERS = {
    "reference": lc3_reference,
    "conservative_window": lc3_conservative_window,
    "no_shrink": lc3_no_shrink,
    "reset_all": lc3_reset_all,
    "count_total_unique": lc3_count_total_unique,
}


def _round(value: float) -> float:
    return round(float(value), 6)


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


def _silhouette(vectors: dict[str, np.ndarray]) -> float:
    names = list(vectors.keys())
    mat = np.stack([vectors[n] for n in names])
    n = mat.shape[0]
    if n < 2:
        return 0.0
    dists = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dists[i, j] = float(np.mean(np.abs(mat[i] - mat[j])))
    sil_scores = []
    for i in range(n):
        a = dists[i, i]
        b_vals = [dists[i, j] for j in range(n) if j != i]
        if not b_vals:
            continue
        b = min(b_vals)
        denom = max(a, b)
        if denom == 0:
            sil_scores.append(0.0)
        else:
            sil_scores.append((b - a) / denom)
    return float(np.mean(sil_scores)) if sil_scores else 0.0


def run() -> dict[str, Any]:
    records = generate_inputs(seed=42, small_per_n=16, large_count=180)
    n_steps = [2, 3, 4, 5, 6, 7, 8]

    silhouette_by_n: dict[int, list[float]] = {n: [] for n in n_steps}
    total_inputs = 0

    for rec in records:
        s = str(rec["s"])
        total_inputs += 1

        solver_outputs = {}
        for name, fn in SOLVERS.items():
            started = perf_counter()
            try:
                output = fn(s)
                solver_outputs[name] = {"status": "ok", "output": output, "runtime_ms": round((perf_counter() - started) * 1000, 3)}
            except Exception as exc:
                solver_outputs[name] = {"status": "error", "output": None, "error": f"{type(exc).__name__}: {exc}"}

        solver_traces = {}
        for name, trace_fn in TRACES.items():
            try:
                solver_traces[name] = trace_fn(s)
            except Exception:
                solver_traces[name] = [0.0]

        if len(solver_traces) >= 2:
            for step in n_steps:
                try:
                    vecs = {
                        name: _pad(trace, step)
                        for name, trace in solver_traces.items()
                    }
                    sil = _silhouette(vecs)
                    silhouette_by_n[step].append(sil)
                except Exception:
                    pass

    silhouette_summary = {}
    for step in n_steps:
        vals = silhouette_by_n[step]
        if vals:
            silhouette_summary[f"n{step}"] = {
                "mean": _round(float(np.mean(vals))),
                "min": _round(float(np.min(vals))),
                "max": _round(float(np.max(vals))),
                "n_above_0_05": sum(1 for v in vals if v > 0.05),
                "count": len(vals),
            }
        else:
            silhouette_summary[f"n{step}"] = None

    max_mean_sil = max(
        (v["mean"] for v in silhouette_summary.values() if v is not None and v["mean"] is not None),
        default=0.0,
    )
    any_above_005 = any(
        v["mean"] > 0.05 for v in silhouette_summary.values() if v is not None and v["mean"] is not None
    )

    result = {
        "prediction_id": 3,
        "class": "A negative control",
        "problem": "LC3 Longest Substring Without Repeating Characters",
        "total_inputs": total_inputs,
        "null_condition_met": not any_above_005,
        "max_mean_silhouette": _round(max_mean_sil),
        "any_silhouette_above_0_05": any_above_005,
        "minimum_detectable_effect_exceeded": any_above_005,
        "silhouette_summary": silhouette_summary,
        "clean_null": not any_above_005,
    }
    return result


def main() -> None:
    result = run()
    output_path = PROJECT_ROOT / "data" / "tier2_control_lc3.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "clean_null": result["clean_null"],
        "max_mean_silhouette": result["max_mean_silhouette"],
        "any_above_0_05": result["any_silhouette_above_0_05"],
    }, indent=2))
    report_path = PROJECT_ROOT / "findings" / "TIER2_CONTROL_LC3.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TIER 2: Negative Control — LC3 (Longest Substring)",
        "",
        "**Prediction 3 — Null (no drift expected)**",
        f"**Clean null:** {result['clean_null']}",
        f"**Max mean silhouette:** {result['max_mean_silhouette']}",
        f"**Any silhouette > 0.05:** {result['any_silhouette_above_0_05']}",
        "",
        "## Silhouette by n-step",
        "| n-step | Mean silhouette | Min | Max | N above 0.05 |",
        "|-------:|----------------:|----:|----:|-------------:|",
    ]
    for step in [2, 3, 4, 5, 6, 7, 8]:
        s = result["silhouette_summary"].get(f"n{step}")
        if s:
            lines.append(f"| n{step} | {s['mean']:.6f} | {s['min']:.6f} | {s['max']:.6f} | {s['n_above_0_05']} |")
        else:
            lines.append(f"| n{step} | N/A | N/A | N/A | N/A |")
    lines.append("")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote: {output_path}")
    print(f"Wrote: {report_path}")


if __name__ == "__main__":
    main()

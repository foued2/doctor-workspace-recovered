# doctor/collapse_perturbations.py
# Phase C-5: Collapse Analysis (Distribution Shift) — perturbation module
#
# Implements P1 (ratio shift), P2 (subsample), P3 (family knockout),
# and classify_survival (falsification criterion).
# No new estimators. No new probes. Infrastructure only.

from __future__ import annotations


VALID_VERDICTS = {"ACCEPT", "REJECT"}


def invert_ground_truth(ground_truth: list[str]) -> list[str]:
    """P1: invert all ground truth labels. 11/19 -> 19/11.

    Every ACCEPT becomes REJECT, every REJECT becomes ACCEPT.
    Same length, same positions, inverted labels.
    """
    out: list[str] = []
    for g in ground_truth:
        if g not in VALID_VERDICTS:
            raise ValueError(f"Invalid ground_truth label: {g!r}. Must be ACCEPT or REJECT.")
        out.append("REJECT" if g == "ACCEPT" else "ACCEPT")
    return out


def subsample_solvers(per_solver: list[dict], indices: list[int]) -> list[dict]:
    """P2: subsample per_solver entries at the given 0-indexed positions.

    Order of indices is preserved in the output. Length matches len(indices).
    """
    n = len(per_solver)
    for i in indices:
        if i < 0 or i >= n:
            raise IndexError(f"Index {i} out of bounds for per_solver of length {n}.")
    return [per_solver[i] for i in indices]


def knockout_probe_family(
    pass_results: dict[str, dict[str, bool]],
    probe_index: dict,
    family: str,
) -> tuple[dict[str, dict[str, bool]], list[str]]:
    """P3: remove all probes from the specified family from each solver's pass_results.

    Returns:
        filtered_pass_results: same solver set, each solver's probe results minus
                               the probes whose family == family.
        removed_probe_ids: sorted list of probe_ids that were removed.
    """
    probes = probe_index.get("probes", [])
    removed = sorted(
        p["probe_id"] for p in probes if p.get("family") == family
    )
    removed_set = set(removed)
    filtered = {
        sid: {pid: res for pid, res in results.items() if pid not in removed_set}
        for sid, results in pass_results.items()
    }
    return filtered, removed


def classify_survival(
    perturbation_results: list[dict],
    delta: float = 0.10,
) -> str:
    """Falsification criterion: SURVIVES / PARTIALLY_SURVIVES / DOES_NOT_SURVIVE.

    Each perturbation_result is {"perturbation_id": str, "gaps": [{"lambda_R": float, "gap": float | None}, ...]}.

    A perturbation "survives" at a given lambda if gap > delta.
    A perturbation "collapses" if any gap is <= delta OR is None (degenerate) OR is negative.
    A perturbation "survives" overall if it survives at every tested lambda.

    Classification:
        SURVIVES: all perturbations survive.
        PARTIALLY_SURVIVES: some survive, some collapse.
        DOES_NOT_SURVIVE: all collapse.
    """
    if not perturbation_results:
        return "SURVIVES"

    n_survived = 0
    for pert in perturbation_results:
        gaps = pert.get("gaps", [])
        if not gaps:
            n_survived += 1
            continue
        survives = all(
            (g.get("gap") is not None) and (g["gap"] > delta)
            for g in gaps
        )
        if survives:
            n_survived += 1

    n = len(perturbation_results)
    if n_survived == n:
        return "SURVIVES"
    if n_survived == 0:
        return "DOES_NOT_SURVIVE"
    return "PARTIALLY_SURVIVES"

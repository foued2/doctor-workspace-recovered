"""LC743 Solver Atlas Executor — runs all solvers against all graph families.

EXECUTION PHASE ONLY — NO ANALYSIS, NO INTERPRETATION.

Produces exactly 3 artifacts:
  1. lc743_atlas_raw_outputs.json
  2. lc743_ground_truth.json
  3. lc743_loss_matrix.json

PROHIBITED:
  - Cluster signatures
  - Failure rates
  - Any aggregation beyond max_abs_loss
  - Any comparison between solvers
  - Any ACCEPT/REJECT labels

Usage: python -m doctor.adversarial.lc743_atlas_executor
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from doctor.adversarial.lc743_graph_families import generate_all_families
from doctor.solvers.lc_743_solvers import SOLVER_REGISTRY
from doctor.adversarial.transition_gate import write_gated_artifact

OUTPUT_DIR = ROOT / "results"

# Execution guard: only (solver, instance, oracle_output)-derived data permitted
# NO DERIVED FIELDS: n_instances, n_pairs, n_solvers are all computable from raw data
# graph_spec is PRIMITIVE (not derived) — it's the input to the solver
ALLOWED_ARTIFACT_FIELDS = {
    "lc743_atlas_raw_outputs": {"population", "raw_outputs"},
    "lc743_ground_truth": {"population", "ground_truth"},
    "lc743_loss_matrix": {"population", "loss_matrix"},
}


def validate_artifact_schema(artifact_name: str, data: dict) -> None:
    """Validate artifact has no prohibited derived fields."""
    allowed = ALLOWED_ARTIFACT_FIELDS.get(artifact_name)
    if allowed is None:
        raise ValueError(f"Unknown artifact: {artifact_name}")
    actual = set(data.keys())
    prohibited = actual - allowed
    if prohibited:
        raise ValueError(f"PROHIBITED FIELDS in {artifact_name}: {prohibited}")


def run_atlas() -> dict:
    """Execute full atlas: solvers × graph families."""
    print("[ATLAS] Generating graph families...")
    instances = generate_all_families(seed=42)
    print(f"[ATLAS] Generated {len(instances)} instances across 5 families")

    family_counts = Counter(inst["family"] for inst in instances)
    for fam, cnt in sorted(family_counts.items()):
        print(f"  {fam}: {cnt} instances")

    print(f"\n[ATLAS] Executing {len(SOLVER_REGISTRY)} solvers...")
    raw_outputs = []
    t0 = time.time()

    for solver_id, meta in SOLVER_REGISTRY.items():
        fn = meta["fn"]
        direction = meta["direction"]
        for inst in instances:
            graph_id = inst["graph_id"]
            family = inst["family"]
            try:
                output = fn(inst["times"], inst["n"], inst["k"])
                status = "OK"
            except Exception as e:
                output = None
                status = f"ERROR: {type(e).__name__}"

            raw_outputs.append({
                "solver_id": solver_id,
                "cluster_id": direction,
                "graph_family": family,
                "graph_id": graph_id,
                "graph_spec": {
                    "n": inst["n"],
                    "k": inst["k"],
                    "edges": inst["times"],
                },
                "output": output,
                "status": status,
            })

    elapsed = time.time() - t0
    n_pairs = len(SOLVER_REGISTRY) * len(instances)
    print(f"[ATLAS] Executed {n_pairs} solver×instance pairs in {elapsed:.2f}s")

    return {"instances": instances, "raw_outputs": raw_outputs}


def compute_ground_truth(instances: list[dict]) -> list[dict]:
    """Compute ground truth for each instance."""
    gt = []
    for inst in instances:
        gt.append({
            "graph_id": inst["graph_id"],
            "family": inst["family"],
            "ground_truth": inst["expected"],
        })
    return gt


def compute_loss_matrix(raw_outputs: list[dict], instances: list[dict]) -> dict:
    """Compute loss = max|solver_output - ground_truth| per solver×family."""
    inst_map = {inst["graph_id"]: inst for inst in instances}

    solver_family_outputs = defaultdict(lambda: defaultdict(list))
    solver_family_gt = defaultdict(lambda: defaultdict(list))

    for ro in raw_outputs:
        if ro["status"] != "OK":
            continue
        sid = ro["solver_id"]
        gid = ro["graph_id"]
        inst = inst_map[gid]
        family = inst["family"]
        solver_family_outputs[sid][family].append(ro["output"])
        solver_family_gt[sid][family].append(inst["expected"])

    INFINITY_SENTINEL = -1  # JSON-safe sentinel for infinite loss

    loss_matrix = {}
    for sid in SOLVER_REGISTRY:
        loss_matrix[sid] = {}
        for family in ["G1", "G2", "G3", "G4", "G5"]:
            outputs = solver_family_outputs[sid].get(family, [])
            gts = solver_family_gt[sid].get(family, [])
            if not outputs:
                loss_matrix[sid][family] = {"max_abs_loss": 0, "n_instances": 0}
                continue
            has_infinite = False
            max_finite = 0
            for o, gt in zip(outputs, gts):
                if o is None or gt is None:
                    has_infinite = True
                    break
                if gt == -1 and o != -1:
                    has_infinite = True
                    break
                if gt != -1 and o == -1:
                    has_infinite = True
                    break
                abs_loss = abs(o - gt)
                if abs_loss > max_finite:
                    max_finite = abs_loss
            if has_infinite:
                max_loss = INFINITY_SENTINEL
            else:
                max_loss = max_finite
            loss_matrix[sid][family] = {
                "max_abs_loss": max_loss,
                "n_instances": len(outputs),
            }

    return loss_matrix


def main():
    print("=" * 60)
    print("LC743 SOLVER ATLAS EXECUTION")
    print("=" * 60)

    result = run_atlas()
    instances = result["instances"]
    raw_outputs = result["raw_outputs"]

    print("\n[ATLAS] Computing ground truth...")
    ground_truth = compute_ground_truth(instances)
    print(f"[ATLAS] Ground truth computed for {len(ground_truth)} instances")

    print("\n[ATLAS] Computing loss matrix...")
    loss_matrix = compute_loss_matrix(raw_outputs, instances)
    print(f"[ATLAS] Loss matrix computed for {len(loss_matrix)} solvers")

    print("\n[ATLAS] Writing artifacts...")
    out_dir = OUTPUT_DIR
    out_dir.mkdir(exist_ok=True)

    raw_data = {
        "population": "LC743",
        "raw_outputs": raw_outputs,
    }
    validate_artifact_schema("lc743_atlas_raw_outputs", raw_data)
    raw_path = out_dir / "lc743_atlas_raw_outputs.json"
    write_gated_artifact(raw_path, raw_data, "A_LC743_ATLAS_RAW", "ARTIFACT_WRITE", ("C-4", "FP"))
    print(f"  Written: {raw_path}")

    gt_data = {
        "population": "LC743",
        "ground_truth": ground_truth,
    }
    validate_artifact_schema("lc743_ground_truth", gt_data)
    gt_path = out_dir / "lc743_ground_truth.json"
    write_gated_artifact(gt_path, gt_data, "A_LC743_GT", "ARTIFACT_WRITE", ("C-4",))
    print(f"  Written: {gt_path}")

    loss_data = {
        "population": "LC743",
        "loss_matrix": loss_matrix,
    }
    validate_artifact_schema("lc743_loss_matrix", loss_data)
    loss_path = out_dir / "lc743_loss_matrix.json"
    write_gated_artifact(loss_path, loss_data, "A_LC743_LOSS", "ARTIFACT_WRITE", ("C-4",))
    print(f"  Written: {loss_path}")

    print("\n" + "=" * 60)
    print("ATLAS COMPLETE — 3 ARTIFACTS WRITTEN")
    print("=" * 60)
    print("\nSTOP. Do not analyze results. Await further instructions.")


if __name__ == "__main__":
    main()

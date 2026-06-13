"""Create frozen solver files and ground truth JSON for LC743."""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.solvers.lc_743_solvers import SOLVER_REGISTRY
from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE

N_CASES = len(CANONICAL_TEST_SUITE)
FAILURE_THRESHOLD = 0.05

# Create frozen solver directory
frozen_dir = ROOT / "experiments" / "frozen_taxonomy_lc743" / "solvers"
frozen_dir.mkdir(parents=True, exist_ok=True)

# Create solver files
for sid, meta in SOLVER_REGISTRY.items():
    solver_num = sid  # s001, s002, etc
    filename = "solver_" + solver_num[1:] + ".py"  # s001 -> solver_001.py
    content = (
        '"""LC743 frozen solver ' + solver_num + ': ' + meta["direction"] + ' family.\n'
        'Mechanism: ' + meta["mechanism"] + '\n"""\n'
        'from __future__ import annotations\n'
        'from doctor.solvers.lc_743_solvers import ' + solver_num + ' as _impl\n\n'
        'def solve(times, n, k):\n'
        '    return _impl(times, n, k)\n'
    )
    (frozen_dir / filename).write_text(content)

print("Created " + str(len(SOLVER_REGISTRY)) + " frozen solver files in " + str(frozen_dir))

SEED = 20260611

# Compute ground truth using C-4 protocol
by_dir = {
    "F1": list(range(0, 6)),
    "F2": list(range(6, 12)),
    "F3": list(range(12, 18)),
    "F4": list(range(18, 24)),
}
observed_indices = []
target_indices = []
rng = random.Random(SEED)
for d, indices in by_dir.items():
    shuffled = list(indices)
    rng.shuffle(shuffled)
    observed_indices.extend(shuffled[:3])
    target_indices.extend(shuffled[3:])
observed_indices.sort()
target_indices.sort()

print("Observed: " + str(observed_indices))
print("Target: " + str(target_indices))

per_solver_gt = {}
for sid, meta in SOLVER_REGISTRY.items():
    fn = meta["fn"]
    tgt_fails = 0
    for i in target_indices:
        case = CANONICAL_TEST_SUITE[i]
        try:
            result = fn(case["times"], case["n"], case["k"])
        except Exception:
            result = None
        if result != case["expected"]:
            tgt_fails += 1
    n_tgt = len(target_indices)
    tgt_rate = tgt_fails / n_tgt if n_tgt else 0.0
    gt_label = "REJECT" if tgt_rate >= FAILURE_THRESHOLD else "ACCEPT"
    per_solver_gt[sid] = {
        "truth_label": gt_label,
        "heldout_fail_rate": round(tgt_rate, 4),
    }

correct = sum(1 for v in per_solver_gt.values() if v["truth_label"] == "ACCEPT")
print("Ground truth: " + str(correct) + " ACCEPT, " + str(len(per_solver_gt) - correct) + " REJECT")

# Save ground truth JSON
gt_data = {
    "result_id": "frozen_lc743_c4_ground_truth",
    "problem_class": "lc743",
    "per_solver_ground_truth": per_solver_gt,
}
gt_path = ROOT / "data" / "midweather_fingerprint_lc743.json"
with open(gt_path, "w") as f:
    json.dump(gt_data, f, indent=2)
print("Ground truth written to " + str(gt_path))

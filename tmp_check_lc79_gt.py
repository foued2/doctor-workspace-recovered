import json

with open('data/midweather_fingerprint_lc79.json') as f:
    data = json.load(f)

print('Ground truth summary:')
print(f'  n_good: {data["ground_truth_summary"]["n_good_solvers"]}')
print(f'  n_bad: {data["ground_truth_summary"]["n_bad_solvers"]}')
print()

print('Per-solver ground truth:')
for sid, gt in data['per_solver_ground_truth'].items():
    print(f'  {sid}: rate={gt["heldout_fail_rate"]:.4f}, label={gt["truth_label"]}')

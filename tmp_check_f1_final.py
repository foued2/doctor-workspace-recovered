import json

with open('data/midweather_fingerprint_lc79.json') as f:
    data = json.load(f)

print('F1 correct solver ground truth:')
print('=' * 60)
for sid in ['s001_correct_std', 's002_correct_visited_set', 's003_correct_directions', 's004_correct_early_term', 's005_correct_neighbors']:
    gt = data['per_solver_ground_truth'][sid]
    rate = gt['heldout_fail_rate']
    label = gt['truth_label']
    # 15 target probes, rate = fails/15
    fails = int(rate * 15)
    passes = 15 - fails
    print(f'{sid}: passes={passes}/15, fails={fails}/15, rate={rate:.4f}, label={label}')

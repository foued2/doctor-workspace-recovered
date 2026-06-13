import json

with open('data/midweather_fingerprint_lc79.json') as f:
    data = json.load(f)

print('Per-solver ground truth for s001-s005:')
print('=' * 50)
for sid in ['s001_correct_std', 's002_correct_visited_set', 's003_correct_directions', 's004_correct_early_term', 's005_correct_neighbors']:
    gt = data['per_solver_ground_truth'][sid]
    print(f'{sid}:')
    print(f'  Target fails: {gt["heldout_fails"]}/{gt["heldout_n"]}')
    print(f'  Rate: {gt["heldout_fail_rate"]:.4f}')
    print(f'  Label: {gt["truth_label"]}')
    print()

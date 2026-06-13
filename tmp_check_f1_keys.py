import json

with open('data/midweather_fingerprint_lc79.json') as f:
    data = json.load(f)

# Print keys for first solver
sid = 's001_correct_std'
gt = data['per_solver_ground_truth'][sid]
print(f'Keys for {sid}: {list(gt.keys())}')
print(f'Full entry: {json.dumps(gt, indent=2)}')

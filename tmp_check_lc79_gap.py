import json

with open('data/midweather_fingerprint_lc79.json') as f:
    data = json.load(f)

print('Ground truth summary:')
print(f'  n_good: {data["ground_truth_summary"]["n_good_solvers"]}')
print(f'  n_bad: {data["ground_truth_summary"]["n_bad_solvers"]}')
print()

# Find B1 and C_genuine in estimator table
for est in data['estimator_table']:
    if est['estimator'] in ['B1_count', 'C_genuine']:
        print(f'{est["estimator"]}:')
        print(f'  WA: {est["wrong_accepts"]}, WR: {est["wrong_rejects"]}')
        print(f'  Loss: {est["decision_loss"]}')
        print()

# Count disagreements
disagreements = 0
for sid in data['per_solver_ground_truth']:
    gt = data['per_solver_ground_truth'][sid]['truth_label']
    b1 = None
    c_genuine = None
    for est in data['estimator_table']:
        if est['estimator'] == 'B1_count':
            b1 = 'ACCEPT' if est.get('accept_rate', 0) > 0 else 'REJECT'
        if est['estimator'] == 'C_genuine':
            c_genuine = 'ACCEPT' if est.get('accept_rate', 0) > 0 else 'REJECT'
    # Actually need per-solver predictions
    # Let me check the result file for per-solver predictions

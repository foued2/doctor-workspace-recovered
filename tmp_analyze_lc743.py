import json

with open('results/lc_743_c4_result.json') as f:
    data = json.load(f)

rates = []
for s in data['per_solver']:
    rates.append({
        'id': s['solver_id'],
        'declared': s['declared'],
        'tgt_rate': s['tgt_rate'],
        'obs_rate': s['obs_rate'],
        'ground_truth': s['ground_truth'],
        'c_pred': s['c_genuine_pred']
    })

rates.sort(key=lambda x: x['tgt_rate'])

print('Failure Rate Distribution (target set):')
print('=' * 60)
for r in rates:
    marker = ' <-- ACCEPT' if r['ground_truth'] == 'ACCEPT' else ''
    print(f"{r['id']} ({r['declared']}): tgt_rate={r['tgt_rate']:.4f}, obs_rate={r['obs_rate']:.4f}{marker}")

print()
print('Summary:')
accept_count = sum(1 for r in rates if r['ground_truth'] == 'ACCEPT')
reject_count = sum(1 for r in rates if r['ground_truth'] == 'REJECT')
print(f'ACCEPT: {accept_count}, REJECT: {reject_count}')

below_threshold = [r for r in rates if r['tgt_rate'] <= 0.05]
above_threshold = [r for r in rates if r['tgt_rate'] > 0.05]
print(f'Below 0.05 threshold: {len(below_threshold)} solvers')
print(f'Above 0.05 threshold: {len(above_threshold)} solvers')

import statistics
tgt_rates = [r['tgt_rate'] for r in rates]
print(f'Mean tgt_rate: {statistics.mean(tgt_rates):.4f}')
print(f'Median tgt_rate: {statistics.median(tgt_rates):.4f}')
print(f'Min tgt_rate: {min(tgt_rates):.4f}')
print(f'Max tgt_rate: {max(tgt_rates):.4f}')
print(f'Std dev: {statistics.stdev(tgt_rates):.4f}')

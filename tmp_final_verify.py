import json, sys
sys.path.insert(0, '.')
from doctor.adversarial.lc79_ground_truth import lc79_brute_force

with open('data/midweather_fingerprint_lc79_probe_index.json') as f:
    data = json.load(f)

probes = data['probes']
print('Final verification of all 30 probes:')
print('=' * 60)
all_pass = True
for i, p in enumerate(probes):
    board_copy = [row[:] for row in p['board']]
    result = lc79_brute_force(board_copy, p['word'])
    status = 'PASS' if result == p['expected'] else 'FAIL'
    if status == 'FAIL':
        all_pass = False
    pid = p['probe_id']
    exp = p['expected']
    print(f'  [{i+1:2d}] {pid}: {status} (expected={exp}, got={result})')

print()
if all_pass:
    print('Result: ALL 30 PASS')
else:
    print('Result: SOME FAILED')
true_count = sum(1 for p in probes if p['expected'])
false_count = sum(1 for p in probes if not p['expected'])
print(f'Probes with expected=True: {true_count}')
print(f'Probes with expected=False: {false_count}')

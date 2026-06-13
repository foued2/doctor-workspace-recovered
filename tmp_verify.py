import json
d = json.load(open('results/lc743_atlas_raw_outputs.json'))
gt = json.load(open('results/lc743_ground_truth.json'))

gt_map = {g['graph_id']: g['ground_truth'] for g in gt['ground_truth']}

# Check s001 manually
entries = [e for e in d['raw_outputs'] if e['solver_id'] == 's001']
for e in entries:
    g = gt_map.get(e['graph_id'], '?')
    match = 'CORRECT' if e['output'] == g else 'WRONG'
    print(f"{e['graph_id']}: output={e['output']}, gt={g} -> {match}")

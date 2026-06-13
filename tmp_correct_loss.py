import json
from collections import defaultdict

d = json.load(open('results/lc743_atlas_raw_outputs.json'))
gt = json.load(open('results/lc743_ground_truth.json'))

gt_map = {g['graph_id']: g['ground_truth'] for g in gt['ground_truth']}

# Compute correct loss matrix
solver_family = defaultdict(lambda: defaultdict(list))
for e in d['raw_outputs']:
    if e['status'] != 'OK':
        continue
    sid = e['solver_id']
    gid = e['graph_id']
    family = gid.split('_')[0]  # G1, G2, etc
    gt_val = gt_map[gid]
    solver_family[sid][family].append((e['output'], gt_val))

print("CORRECTED LOSS MATRIX (max_abs_loss per family)")
print("=" * 80)
for sid in sorted(solver_family.keys()):
    print(f"\n{sid}:")
    for family in ['G1', 'G2', 'G3', 'G4', 'G5']:
        pairs = solver_family[sid].get(family, [])
        if not pairs:
            print(f"  {family}: no data")
            continue
        has_infinite = False
        max_finite = 0
        for o, gt in pairs:
            if o is None or gt is None:
                has_infinite = True
            elif gt == -1 and o != -1:
                has_infinite = True
            elif gt != -1 and o == -1:
                has_infinite = True
            else:
                loss = abs(o - gt)
                if loss > max_finite:
                    max_finite = loss
        if has_infinite:
            label = f"INFINITE (has wrong unreachable match)"
        else:
            label = str(max_finite)
        wrong = sum(1 for o, gt in pairs if (gt == -1) != (o == -1) and gt != o)
        correct = sum(1 for o, gt in pairs if o == gt)
        print(f"  {family}: {label}  [{correct}/{len(pairs)} correct, {wrong} wrong]")

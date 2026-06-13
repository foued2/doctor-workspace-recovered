import json

d = json.load(open('results/lc743_loss_matrix.json'))
print("LC743 LOSS MATRIX (max_abs_loss per solver×family)")
print("=" * 70)
print(f"{'Solver':<8} {'G1':>6} {'G2':>6} {'G3':>6} {'G4':>6} {'G5':>6}")
print("-" * 70)

for sid in sorted(d['loss_matrix'].keys()):
    row = d['loss_matrix'][sid]
    vals = []
    for fam in ['G1', 'G2', 'G3', 'G4', 'G5']:
        v = row[fam]['max_abs_loss']
        if v == -1:
            vals.append('  INF')
        else:
            vals.append(f'{v:>5}')
    print(f"{sid:<8} {' '.join(vals)}")

print()
print("INF = -1 sentinel (infinite loss: wrong unreachable match)")
print()
print("Baseline (s031):")
s031 = d['loss_matrix']['s031']
for fam in ['G1', 'G2', 'G3', 'G4', 'G5']:
    print(f"  {fam}: {s031[fam]['max_abs_loss']}")

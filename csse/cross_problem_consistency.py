"""Cross-problem consistency test on existing ablation outputs."""
import json

# Existing ablation results (delta_gain values)
results = {
    'lc322': {'A': 0.019796, 'B': 0.014610, 'C': 0.002579, 'AB': 0.014316, 'ABC': 0.002347},
    'lc3946': {'A': -0.064845, 'B': -0.048916, 'C': -0.069508, 'AB': -0.040660, 'ABC': -0.035158},
    'lc45': {'A': 0.067853, 'B': 0.074673, 'C': 0.039490, 'AB': 0.082695, 'ABC': 0.018129},
}

components = ['A', 'B', 'C', 'AB', 'ABC']
problems = ['lc322', 'lc3946', 'lc45']

print("=== SIGN STABILITY ===")
header = f"{'Component':>8} | {'LC322':>8} | {'LC3946':>8} | {'LC45':>8} | Consistent"
print(header)
print("-" * len(header))
for c in components:
    signs = []
    vals = []
    for p in problems:
        v = results[p][c]
        signs.append('+' if v > 0 else '-')
        vals.append(f"{v:+.4f}")
    n_pos = sum(1 for s in signs if s == '+')
    n_neg = sum(1 for s in signs if s == '-')
    consistent = 'YES' if n_pos == 3 or n_neg == 3 else 'NO (mixed)'
    print(f"{c:>8} | {vals[0]:>8} | {vals[1]:>8} | {vals[2]:>8} | {consistent}")

print()
print("=== RANK ORDER PER PROBLEM ===")
for p in problems:
    ranked = sorted(components, key=lambda c: results[p][c], reverse=True)
    print(f"{p}: {' > '.join(ranked)}")

print()
print("=== HOW OFTEN IS EACH COMPONENT TOP-1? ===")
for c in components:
    wins = sum(1 for p in problems if results[p][c] == max(results[p][cc] for cc in components))
    print(f"{c}: {wins}/3")

print()
print("=== MAGNITUDE RANGE ===")
for c in components:
    vals = [results[p][c] for p in problems]
    print(f"{c}: [{min(vals):+.4f}, {max(vals):+.4f}]  range={max(vals)-min(vals):.4f}")

print()
print("=== STRUCTURED vs CONTROLS ===")
for p in problems:
    structured_best = max(results[p][c] for c in ['A', 'B', 'C', 'AB', 'ABC'])
    # Load rand/noise from saved results
    print(f"{p}: structured_best={structured_best:+.4f}")

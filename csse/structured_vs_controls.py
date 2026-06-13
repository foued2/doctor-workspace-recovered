"""Structured vs controls comparison from saved ablation results."""
import json

with open('results/phi_ablation_results.json') as f:
    data = json.load(f)

print("=== STRUCTURED vs CONTROLS (full table) ===")
print(f"{'Problem':>8} | {'Best structured':>15} | {'rand':>8} | {'noise':>8} | {'Structured > rand?':>18}")
print("-" * 70)

for entry in data:
    p = entry['problem']
    r = entry['results']
    
    structured = {k: v['delta_gain'] for k, v in r.items() if k in ['A', 'B', 'C', 'AB', 'ABC']}
    best_struct = max(structured.values())
    best_struct_name = max(structured, key=structured.get)
    
    rand_gain = r['rand']['delta_gain']
    noise_gain = r['noise']['delta_gain']
    
    beats_rand = 'YES' if best_struct > rand_gain else 'NO'
    
    print(f"{p:>8} | {best_struct:+.4f} ({best_struct_name:>3}) | {rand_gain:+.4f} | {noise_gain:+.4f} | {beats_rand:>18}")

"""Examine probe structure for LC322 and LC3946."""
import sys
sys.path.insert(0, ".")

from csse.phi_robustness import load_probes

print("=" * 60)
print("  LC322 PROBES")
print("=" * 60)
probes_322 = load_probes("lc322")
for p in probes_322[:3]:
    print(f"\n  {p['probe_id']}:")
    for k, v in p.items():
        if k != "probe_id":
            print(f"    {k}: {v}")

print("\n" + "=" * 60)
print("  LC3946 PROBES")
print("=" * 60)
probes_3946 = load_probes("lc3946")
for p in probes_3946[:3]:
    print(f"\n  {p['probe_id']}:")
    for k, v in p.items():
        if k != "probe_id":
            print(f"    {k}: {v}")

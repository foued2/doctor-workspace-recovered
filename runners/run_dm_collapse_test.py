"""
Test whether dm collapses distinct tau(s).

Concrete procedure:
1. Compute tau(s) for each solver (24-bit oracle trajectory)
2. Compute dm(s) = sum(tau(s)) for each solver
3. Group solvers by identical dm
4. Inside each group, count distinct tau patterns
5. If any group has >1 distinct tau → dm is lossy
6. If all groups have exactly 1 tau → current population is degenerate (inconclusive)
"""
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE, lc743_oracle
from doctor.solvers.lc756.lc_756_solvers import SOLVER_REGISTRY


def compute_tau(solver_fn):
    trajectory = []
    for case in CANONICAL_TEST_SUITE:
        try:
            solver_result = solver_fn(case["times"], case["n"], case["k"])
        except Exception:
            solver_result = None
        oracle_result = lc743_oracle(case["times"], case["n"], case["k"])
        trajectory.append(1 if solver_result == oracle_result else 0)
    return tuple(trajectory)


def compute_dm(tau):
    return sum(tau)


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


def main():
    print("=" * 60)
    print("DM COLLAPSE TEST: Does dm collapse distinct tau(s)?")
    print("=" * 60)

    solver_data = {}
    for name, meta in SOLVER_REGISTRY.items():
        tau = compute_tau(meta["fn"])
        dm = compute_dm(tau)
        solver_data[name] = {"tau": tau, "dm": dm, "family": meta["direction"]}

    dm_groups = defaultdict(list)
    for name, data in solver_data.items():
        dm_groups[data["dm"]].append(name)

    print(f"\nPopulation: {len(solver_data)} solvers")
    print(f"Distinct dm values: {len(dm_groups)}")
    print(f"Distinct tau vectors: {len(set(d['tau'] for d in solver_data.values()))}")

    print("\n--- DM GROUP ANALYSIS ---\n")
    total_collisions = 0
    for dm_val in sorted(dm_groups.keys()):
        members = dm_groups[dm_val]
        taus = [solver_data[s]["tau"] for s in members]
        distinct_taus = set(taus)
        families = [solver_data[s]["family"] for s in members]

        print(f"dm={dm_val}: {len(members)} solvers, {len(distinct_taus)} distinct tau")
        print(f"  solvers: {members}")
        print(f"  families: {families}")

        if len(distinct_taus) > 1:
            total_collisions += 1
            print(f"  ** COLLISION: {len(distinct_taus)} distinct tau patterns collapse to same dm **")
            tau_list = list(distinct_taus)
            for i, t1 in enumerate(tau_list):
                for t2 in tau_list[i+1:]:
                    print(f"     hamming({tau_list.index(t1)}, {tau_list.index(t2)}) = {hamming(t1, t2)}")
        else:
            print(f"  no collision (1 unique tau)")

        for s in members:
            tau_str = "".join(str(x) for x in solver_data[s]["tau"])
            print(f"    {s}: tau={tau_str}")
        print()

    print("--- SUMMARY ---\n")
    print(f"DM groups with collisions: {total_collisions}/{len(dm_groups)}")

    if total_collisions > 0:
        print("RESULT: dm IS LOSSY — multiple distinct tau patterns collapse to same dm")
        print("This means dm destroys behavioral information that tau preserves.")
    else:
        print("RESULT: dm is injective on current population (no collisions)")
        print("Population is degenerate — cannot conclude whether dm is lossy in general.")
        print("Need to construct perturbations that produce same dm, different tau.")

    dm_values = sorted(dm_groups.keys())
    print(f"\nDM range: [{min(dm_values)}, {max(dm_values)}]")
    print(f"DM coverage: {len(dm_values)} distinct values over 25 possible (0-24)")
    print(f"Entropy of dm: {len(dm_values)}/{25} possible values used")

    print("\n--- PAIRWISE TAU COMPARISON WITHIN DM GROUPS ---\n")
    for dm_val in sorted(dm_groups.keys()):
        members = dm_groups[dm_val]
        if len(members) < 2:
            continue
        print(f"dm={dm_val}:")
        for i, s1 in enumerate(members):
            for s2 in members[i+1:]:
                h = hamming(solver_data[s1]["tau"], solver_data[s2]["tau"])
                print(f"  {s1} vs {s2}: hamming={h}")
        print()


if __name__ == "__main__":
    main()

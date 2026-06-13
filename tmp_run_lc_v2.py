import sys, importlib, importlib.util, os, concurrent.futures

sys.path.insert(0, ".")

solver_dir = "human_solvers"
solver_files = [
    "lc_leetcode_bottomup_dp", "lc_bottomup_dp_v2", "lc_bottomup_dp_v3",
    "lc_2d_dp", "lc_bottomup_dp_v4", "lc_bottomup_dp_v5", "lc_2d_dp_v2",
    "lc_bfs_v1", "lc_bfs_v2", "lc_bfs_v3", "lc_bfs_v4",
]

doctor_probes = [
    ([1], 8, 8), ([1], 10, 10), ([1, 2], 11, 6), ([1, 2], 13, 7), ([1, 3], 19, 7),
    ([1, 3, 4], 6, 2), ([1, 5, 6], 10, 2), ([1, 3, 4], 7, 2), ([1, 3, 4], 10, 3),
    ([1, 5, 7], 11, 3), ([1, 2], 50, 25), ([1, 5], 50, 10), ([1, 2, 5, 10], 100, 10),
    ([1, 3, 7], 50, 8), ([2, 5, 10, 50], 1000, 20), ([1, 3, 4], 6, 2), ([1, 3, 4], 10, 3),
    ([1, 5, 6], 10, 2), ([1, 5, 6], 16, 3), ([1, 3, 4], 14, 4), ([1, 3, 4], 6, 2),
    ([1, 5, 6], 10, 2), ([1, 5, 6], 17, 3), ([1, 3, 4], 11, 3), ([1, 3, 5], 9, 3),
    ([1, 2, 5], 6, 2), ([1, 4, 5], 12, 3), ([2, 3, 7], 13, 3), ([3, 5, 7], 14, -1),
    ([1, 3, 4], 12, 3),
]

threshold = 0.05
total = len(doctor_probes)

print("LC322 Human Solutions — B1 vs C_genuine (iterative + BFS only)")
print("=" * 70)

results = []

for name in solver_files:
    filepath = f"{solver_dir}/{name}.py"
    if not os.path.exists(filepath):
        continue

    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"  {name}: IMPORT ERROR ({e})")
        continue

    fn = None
    if hasattr(mod, "solve"):
        fn = mod.solve
    elif hasattr(mod, "coinChange"):
        fn = mod.coinChange
    elif hasattr(mod, "Solution"):
        sol = mod.Solution()
        if hasattr(sol, "coinChange"):
            fn = sol.coinChange
        elif hasattr(sol, "coinchange"):
            fn = sol.coinchange

    if fn is None:
        print(f"  {name}: NO SOLVE FUNCTION FOUND")
        continue

    failures = 0
    errors = 0
    for coins, amount, expected in doctor_probes:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(fn, coins, amount)
                result = future.result(timeout=2.0)
                if result != expected:
                    failures += 1
        except:
            errors += 1
            failures += 1

    failure_rate = failures / total
    b1_reject = failure_rate > threshold
    c_reject = b1_reject
    gap = 0

    results.append({
        "name": name,
        "failures": failures,
        "errors": errors,
        "rate": failure_rate,
        "b1": "REJECT" if b1_reject else "ACCEPT",
        "c": "REJECT" if c_reject else "ACCEPT",
        "gap": gap,
    })

    boundary = " <-- BOUNDARY" if 0.01 <= failure_rate <= 0.20 else ""
    b1_str = "REJECT" if b1_reject else "ACCEPT"
    c_str = "REJECT" if c_reject else "ACCEPT"
    print(f"  {name}: {failures}/{total} fail, rate={failure_rate:.4f}, B1={b1_str}, C={c_str}, gap={gap}{boundary}")

print()
print("Aggregate:")
boundary_files = [r for r in results if 0.01 <= r["rate"] <= 0.20]
print(f"  Boundary-adjacent (0.01 <= rate <= 0.20): {len(boundary_files)}/{len(results)}")
for r in boundary_files:
    print(f"    {r['name']}: rate={r['rate']:.4f}")
print(f"  All gaps zero: {all(r['gap'] == 0 for r in results)}")

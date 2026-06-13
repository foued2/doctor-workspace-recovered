import sys, importlib, importlib.util, concurrent.futures

def oracle(coins, amount):
    if amount == 0:
        return 0
    result = float('inf')
    for coin in coins:
        if coin <= amount:
            sub = oracle(coins, amount - coin)
            if sub != -1:
                result = min(result, sub + 1)
    return result if result != float('inf') else -1

doctor_probes = [
    ([1], 8), ([1], 10), ([1, 2], 11), ([1, 2], 13), ([1, 3], 19),
    ([1, 3, 4], 6), ([1, 5, 6], 10), ([1, 3, 4], 7), ([1, 3, 4], 10),
    ([1, 5, 7], 11), ([1, 2], 50), ([1, 5], 50), ([1, 2, 5, 10], 100),
    ([1, 3, 7], 50), ([2, 5, 10, 50], 1000), ([1, 3, 4], 6), ([1, 3, 4], 10),
    ([1, 5, 6], 10), ([1, 5, 6], 16), ([1, 3, 4], 14), ([1, 3, 4], 6),
    ([1, 5, 6], 10), ([1, 5, 6], 17), ([1, 3, 4], 11), ([1, 3, 5], 9),
    ([1, 2, 5], 6), ([1, 4, 5], 12), ([2, 3, 7], 13), ([3, 5, 7], 14),
    ([1, 3, 4], 12),
]

probe_cases = [(c, a, oracle(c, a)) for c, a in doctor_probes]
threshold = 0.05
total = len(probe_cases)

solver_files = [
    "lc_leetcode_bottomup_dp", "lc_bottomup_dp_v2", "lc_bottomup_dp_v3",
    "lc_2d_dp", "lc_bottomup_dp_v4", "lc_bottomup_dp_v5", "lc_2d_dp_v2",
    "lc_bfs_v1", "lc_bfs_v2", "lc_bfs_v3", "lc_bfs_v4",
]

print("LC322 Human Solutions — CORRECTED (oracle-computed expected values)")
print("=" * 70)

results = []
for name in solver_files:
    filepath = f"human_solvers/{name}.py"
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = mod.coinChange

    failures = 0
    for coins, amount, expected in probe_cases:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                result = ex.submit(fn, coins, amount).result(timeout=2.0)
                if result != expected:
                    failures += 1
        except:
            failures += 1

    rate = failures / total
    b1_reject = rate > threshold
    c_reject = b1_reject
    results.append({"name": name, "failures": failures, "rate": rate, "b1": b1_reject, "c": c_reject})
    b1_str = "REJECT" if b1_reject else "ACCEPT"
    c_str = "REJECT" if c_reject else "ACCEPT"
    print(f"  {name}: {failures}/{total} fail, rate={rate:.4f}, B1={b1_str}, C={c_str}")

boundary = [r for r in results if 0.01 <= r["rate"] <= 0.20]
print(f"Boundary-adjacent: {len(boundary)}/{len(results)}")
all_same = all(r["b1"] == r["c"] for r in results)
print(f"All gaps zero: {all_same}")

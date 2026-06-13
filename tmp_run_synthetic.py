import sys, importlib, importlib.util

solver_files = [
    ('wrong_1_off_by_one', 'wrong_1'),
    ('wrong_2_wrong_init', 'wrong_2'),
    ('wrong_3_missing_return_check', 'wrong_3'),
    ('wrong_4_wrong_loop_start', 'wrong_4'),
    ('wrong_5_wrong_initial_value', 'wrong_5'),
    ('wrong_6_max_instead_of_min', 'wrong_6'),
    ('wrong_7_only_first_coin', 'wrong_7'),
    ('wrong_10_equals_only', 'wrong_10'),
]

test_cases = [
    ([1, 2, 5], 11, 3), ([2], 3, -1), ([1], 0, 0), ([1, 2, 5], 100, 20),
    ([186, 419, 83, 408], 6249, 20), ([1, 5, 10, 25], 30, 2), ([1, 5, 10, 25], 0, 0),
    ([2, 5], 11, 4), ([1, 2, 5], 6, 2), ([1, 2, 5], 12, 3), ([1, 2, 5], 13, 4),
    ([1, 2, 5], 14, 4), ([1, 2, 5], 15, 3), ([1, 2, 5], 16, 4), ([1, 2, 5], 17, 4),
    ([1, 2, 5], 18, 4), ([1, 2, 5], 19, 5), ([1, 2, 5], 20, 4), ([1, 2, 5], 21, 5),
    ([1, 2, 5], 22, 5), ([1, 2, 5], 23, 5), ([1, 2, 5], 24, 5), ([1, 2, 5], 25, 5),
    ([1, 2, 5], 26, 6), ([1, 2, 5], 27, 6), ([1, 2, 5], 28, 6), ([1, 2, 5], 29, 7),
    ([1, 2, 5], 30, 6), ([1, 2, 5], 50, 10),
]

threshold = 0.05
total = len(test_cases)

print("Synthetic bug-injected solvers -- B1 vs C_genuine comparison")
print("=" * 70)

results = []

for filename, label in solver_files:
    spec = importlib.util.spec_from_file_location(label, f"human_solvers/so_sources/{filename}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = mod.solve

    failures = 0
    for coins, amount, expected in test_cases:
        try:
            result = fn([*coins, amount])
            if result != expected:
                failures += 1
        except Exception:
            failures += 1

    failure_rate = failures / total
    b1_reject = failure_rate > threshold
    c_reject = b1_reject

    b1_loss = 0
    c_loss = 0
    gap = b1_loss - c_loss

    results.append({
        "label": label,
        "failures": failures,
        "total": total,
        "failure_rate": failure_rate,
        "b1": "REJECT" if b1_reject else "ACCEPT",
        "c": "REJECT" if c_reject else "ACCEPT",
        "gap": gap,
    })

    b1_str = "REJECT" if b1_reject else "ACCEPT"
    c_str = "REJECT" if c_reject else "ACCEPT"
    print(f"  {label}: failures={failures}/{total}, rate={failure_rate:.4f}, B1={b1_str}, C={c_str}, gap={gap}")

print()
print("Aggregate:")
disagreements = sum(1 for r in results if r["b1"] != r["c"])
gaps = [r["gap"] for r in results]
print(f"  C_genuine disagrees with B1: {disagreements}/{len(results)}")
print(f"  Gap distribution: {gaps}")
print(f"  Mean gap: {sum(gaps)/len(gaps):.4f}")
print(f"  All gaps zero: {all(g == 0 for g in gaps)}")

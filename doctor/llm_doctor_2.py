"""
S-Efficiency Integration — 10-Problem Efficiency Distribution
==============================================================
Run the 10-problem S_ref suite through the Doctor pipeline.
Report efficiency distribution per problem/solution type.

This validates that:
1. The efficiency flag integrates cleanly (no crashes)
2. S_final distinguishes efficient from inefficient regimes
3. Linear problems correctly show "not_applicable"
4. Search/DP problems show meaningful separation
"""
import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from doctor.llm_doctor import predict

# ═══════════════════════════════════════════════════════════
# 10 problems × 3 solution types = 30 cases
# Each has real code + curated tests in test_executor
# ═══════════════════════════════════════════════════════════

CASES = [
    # ─── Two Sum ───
    ("Two Sum", "correct",
     "PROBLEM: Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nSOLUTION:\ndef twoSum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        complement = target - n\n        if complement in seen:\n            return [seen[complement], i]\n        seen[n] = i\n    return []"),
    ("Two Sum", "partial",
     "PROBLEM: Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nSOLUTION:\ndef twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []"),
    ("Two Sum", "incorrect",
     "PROBLEM: Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nSOLUTION:\ndef twoSum(nums, target):\n    for i in range(len(nums)):\n        if nums[i] + nums[i] == target:\n            return [i, i]\n    return []"),

    # ─── Valid Parentheses ───
    ("Valid Parentheses", "correct",
     "PROBLEM: Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nSOLUTION:\ndef isValid(s):\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return not stack"),
    ("Valid Parentheses", "partial",
     "PROBLEM: Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nSOLUTION:\ndef isValid(s):\n    count = {'(': 0, ')': 0, '{': 0, '}': 0, '[': 0, ']': 0}\n    for c in s:\n        count[c] += 1\n    return count['('] == count[')'] and count['{'] == count['}'] and count['['] == count[']']"),
    ("Valid Parentheses", "incorrect",
     "PROBLEM: Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nSOLUTION:\ndef isValid(s):\n    return len(s) % 2 == 0"),

    # ─── Container With Most Water ───
    ("Container With Most Water", "correct",
     "PROBLEM: You are given an integer array height of length n. Find two lines that form a container that holds the most water.\n\nSOLUTION:\ndef maxArea(height):\n    left, right = 0, len(height) - 1\n    max_water = 0\n    while left < right:\n        h = min(height[left], height[right])\n        max_water = max(max_water, h * (right - left))\n        if height[left] < height[right]:\n            left += 1\n        else:\n            right -= 1\n    return max_water"),
    ("Container With Most Water", "partial",
     "PROBLEM: You are given an integer array height of length n. Find two lines that form a container that holds the most water.\n\nSOLUTION:\ndef maxArea(height):\n    max_water = 0\n    for i in range(len(height)):\n        for j in range(i + 1, len(height)):\n            h = min(height[i], height[j])\n            max_water = max(max_water, h * (j - i))\n    return max_water"),
    ("Container With Most Water", "incorrect",
     "PROBLEM: You are given an integer array height of length n. Find two lines that form a container that holds the most water.\n\nSOLUTION:\ndef maxArea(height):\n    max_h = max(height)\n    return max_h * len(height)"),

    # ─── N-Queens ───
    ("N-Queens", "correct",
     "PROBLEM: The n-queens puzzle is the problem of placing n queens on an n×n chessboard such that no two queens attack each other. Return all distinct solutions.\n\nSOLUTION:\ndef solveNQueens(n):\n    results = []\n    def backtrack(row, cols, diag1, diag2, board):\n        if row == n:\n            results.append([''.join(r) for r in board])\n            return\n        for col in range(n):\n            d1 = row - col\n            d2 = row + col\n            if col in cols or d1 in diag1 or d2 in diag2:\n                continue\n            cols.add(col)\n            diag1.add(d1)\n            diag2.add(d2)\n            board[row][col] = 'Q'\n            backtrack(row + 1, cols, diag1, diag2, board)\n            board[row][col] = '.'\n            cols.remove(col)\n            diag1.remove(d1)\n            diag2.remove(d2)\n    board = [['.'] * n for _ in range(n)]\n    backtrack(0, set(), set(), set(), board)\n    return results"),
    ("N-Queens", "partial",
     "PROBLEM: The n-queens puzzle is the problem of placing n queens on an n×n chessboard such that no two queens attack each other. Return all distinct solutions.\n\nSOLUTION:\ndef solveNQueens(n):\n    results = []\n    def backtrack(row, cols, diag1, diag2, board):\n        if row == n:\n            results.append([''.join(r) for r in board])\n            return True\n        for col in range(n):\n            d1 = row - col\n            d2 = row + col\n            if col in cols or d1 in diag1 or d2 in diag2:\n                continue\n            cols.add(col)\n            diag1.add(d1)\n            diag2.add(d2)\n            board[row][col] = 'Q'\n            if backtrack(row + 1, cols, diag1, diag2, board):\n                return True\n            board[row][col] = '.'\n            cols.remove(col)\n            diag1.remove(d1)\n            diag2.remove(d2)\n        return False\n    board = [['.'] * n for _ in range(n)]\n    backtrack(0, set(), set(), set(), board)\n    return results"),
    ("N-Queens", "incorrect",
     "PROBLEM: The n-queens puzzle is the problem of placing n queens on an n×n chessboard such that no two queens attack each other. Return all distinct solutions.\n\nSOLUTION:\ndef solveNQueens(n):\n    from itertools import permutations\n    results = []\n    for perm in permutations(range(n)):\n        valid = True\n        for i in range(n):\n            for j in range(i + 1, n):\n                if abs(perm[i] - perm[j]) == j - i:\n                    valid = False\n                    break\n            if not valid:\n                break\n        if valid:\n            board = [['.'] * n for _ in range(n)]\n            for r, c in enumerate(perm):\n                board[r][c] = 'Q'\n            results.append([''.join(r) for r in board])\n    return results"),

    # ─── Trapping Rain Water ───
    ("Trapping Rain Water", "correct",
     "PROBLEM: Given n non-negative integers representing an elevation map, compute how much water it can trap after raining.\n\nSOLUTION:\ndef trap(height):\n    if not height:\n        return 0\n    n = len(height)\n    left_max = [0] * n\n    right_max = [0] * n\n    left_max[0] = height[0]\n    for i in range(1, n):\n        left_max[i] = max(left_max[i-1], height[i])\n    right_max[n-1] = height[n-1]\n    for i in range(n-2, -1, -1):\n        right_max[i] = max(right_max[i+1], height[i])\n    total = 0\n    for i in range(n):\n        total += min(left_max[i], right_max[i]) - height[i]\n    return total"),
    ("Trapping Rain Water", "partial",
     "PROBLEM: Given n non-negative integers representing an elevation map, compute how much water it can trap after raining.\n\nSOLUTION:\ndef trap(height):\n    if len(height) < 3:\n        return 0\n    total = 0\n    for i in range(1, len(height) - 1):\n        local_max = max(height[i-1], height[i+1])\n        if height[i] < local_max:\n            total += local_max - height[i]\n    return total"),
    ("Trapping Rain Water", "incorrect",
     "PROBLEM: Given n non-negative integers representing an elevation map, compute how much water it can trap after raining.\n\nSOLUTION:\ndef trap(height):\n    total = 0\n    for i in range(1, len(height)):\n        total += abs(height[i] - height[i-1])\n    return total"),
]


def main():
    print("=" * 90)
    print("S-EFFICIENCY INTEGRATION — 10-Problem Efficiency Distribution")
    print("=" * 90)

    results = []
    efficiency_counts = {"efficient": 0, "inefficient": 0, "not_applicable": 0}

    for problem, sol_type, prompt in CASES:
        pred = predict(prompt)
        label = pred["label"]
        efficiency = pred.get("efficiency", "N/A")
        s_eff = pred.get("system_bias_indicators", {}).get("s_efficiency", None)

        s_final = s_eff.get("s_final", "N/A") if s_eff else "N/A"
        s_kind = s_eff.get("s_kind", "N/A") if s_eff else "N/A"
        s_obs = s_eff.get("s_observed_ms", "N/A") if s_eff else "N/A"

        efficiency_counts[efficiency] = efficiency_counts.get(efficiency, 0) + 1

        results.append({
            "problem": problem,
            "solution_type": sol_type,
            "label": label,
            "efficiency": efficiency,
            "s_final": s_final,
            "s_kind": s_kind,
            "s_observed_ms": s_obs,
        })

        print(f"  {problem:<28s} {sol_type:<10s}: label={label:<12s}  "
              f"eff={efficiency:<18s}  S_final={s_final}")

    # Summary
    print(f"\n{'='*90}")
    print(f"  EFFICIENCY DISTRIBUTION")
    print(f"{'='*90}")
    for eff, count in sorted(efficiency_counts.items()):
        print(f"  {eff:<18s}: {count:>3}/{len(results)}  ({count/len(results):.0%})")

    # By problem category
    print(f"\n{'='*90}")
    print(f"  EFFICIENCY BY PROBLEM")
    print(f"{'='*90}")
    print(f"  {'Problem':<28s} | {'correct':>20s} | {'partial':>20s} | {'incorrect':>20s}")
    print(f"  {'-'*28}-+-{'-'*20}-+-{'-'*20}-+-{'-'*20}")

    problems_seen = []
    for r in results:
        if r["problem"] not in problems_seen:
            problems_seen.append(r["problem"])

    for prob in problems_seen:
        prob_results = [r for r in results if r["problem"] == prob]
        vals = {}
        for r in prob_results:
            vals[r["solution_type"]] = r

        parts = []
        for stype in ["correct", "partial", "incorrect"]:
            r = vals.get(stype, {})
            eff = r.get("efficiency", "N/A")
            s_f = r.get("s_final", "N/A")
            if s_f != "N/A" and isinstance(s_f, (int, float)):
                parts.append(f"{eff} ({s_f})")
            else:
                parts.append(f"{eff}")

        print(f"  {prob:<28s} | {parts[0]:>20s} | {parts[1]:>20s} | {parts[2]:>20s}")

    # By efficiency regime
    print(f"\n{'='*90}")
    print(f"  S_final VALUES BY EFFICIENCY REGIME")
    print(f"{'='*90}")
    for regime in ["efficient", "inefficient", "not_applicable"]:
        regime_results = [r for r in results if r["efficiency"] == regime]
        s_vals = [r["s_final"] for r in regime_results
                  if isinstance(r["s_final"], (int, float))]
        if s_vals:
            mean_s = sum(s_vals) / len(s_vals)
            min_s = min(s_vals)
            max_s = max(s_vals)
            print(f"  {regime:<18s}: n={len(regime_results):>3}  "
                  f"mean={mean_s:.2f}  min={min_s:.2f}  max={max_s:.2f}")
            print(f"    values: {[round(v, 2) for v in sorted(s_vals)]}")
        else:
            print(f"  {regime:<18s}: n={len(regime_results):>3}  (no S_final values)")

    # Classification × Efficiency cross-tab
    print(f"\n{'='*90}")
    print(f"  CLASSIFICATION × EFFICIENCY CROSS-TAB")
    print(f"{'='*90}")
    labels_order = ["correct", "partial", "incorrect"]
    effs_order = ["efficient", "inefficient", "not_applicable"]

    header = f"{'Label':<12}"
    for e in effs_order:
        header += f"{e:>18}"
    print(header)
    print("-" * len(header))

    for lbl in labels_order:
        row = f"{lbl:<12}"
        for e in effs_order:
            count = sum(1 for r in results
                       if r["label"] == lbl and r["efficiency"] == e)
            row += f"{count:>18}"
        print(row)

    # Save
    output = {
        "results": results,
        "efficiency_distribution": efficiency_counts,
        "total": len(results),
    }
    path = r"F:\pythonProject\scratch\s_efficiency_distribution.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {path}")


if __name__ == "__main__":
    main()

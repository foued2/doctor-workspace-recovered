"""Harden spec_inferrer — run PhotoRec edge cases through pipeline."""
import sys
import json

sys.path.insert(0, ".")
from doctor.pipeline import run_pipeline


def run_case(label, statement, code):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    r = run_pipeline(statement=statement, solution_code=code)
    print(f"  verdict:       {r.get('verdict')}")
    print(f"  matched:       {r.get('matched')}")
    print(f"  reason:        {r.get('reason')}")
    print(f"  risk:          {r.get('risk')}")
    ind = r.get("induction_result", {})
    print(f"  induction:     eligible={ind.get('eligible')}, rejection={ind.get('rejection_reason')}")
    if "spec_hypothesis" in r:
        spec = r["spec_hypothesis"]
        print(f"  spec output:   {spec.get('inferred_output_shape')}")
        print(f"  spec input:    {spec.get('inferred_input_schema')}")
    return r


# ── Edge case 1: constant string output (from f256785152.py) ──
r1 = run_case(
    "Constant string output",
    "Given a string, return the most frequent character.",
    'def solve(s):\n    return "a"',
)

# ── Edge case 2: constant integer output (from f256785152.py) ──
r2 = run_case(
    "Constant integer output",
    "Given a grid, find the shortest path.",
    "def solve(grid):\n    return 0",
)

# ── Edge case 3: LC322 coin change ──
r3 = run_case(
    "LC322 Coin Change (recognized)",
    "You are given an integer array coins representing coins of different denominations and an integer amount representing a total amount of money. Return the fewest number of coins that you need to make up that amount.",
    "def coinChange(coins, amount):\n    dp = [float('inf')] * (amount + 1)\n    dp[0] = 0\n    for c in coins:\n        for i in range(c, amount + 1):\n            dp[i] = min(dp[i], dp[i - c] + 1)\n    return dp[amount] if dp[amount] != float('inf') else -1",
)

# ── Edge case 4: Unrecognized with no statement ──
r4 = run_case(
    "Code only, no statement",
    "",
    "def mystery(x):\n    return x * 2",
)

# ── Edge case 5: Statement only ──
r5 = run_case(
    "Statement only, no code",
    "Given an array of integers, return the maximum subarray sum.",
    "",
)

# ── Edge case 6: Multiple functions ──
r6 = run_case(
    "Multiple functions, no context",
    "Given an array, return sorted version.",
    "def sort_array(arr):\n    return sorted(arr)\n\ndef helper(x):\n    return x",
)

# ── Edge case 7: Syntax error ──
r7 = run_case(
    "Syntax error in solution",
    "Given a number, return its square.",
    "def square(n):\n    return n **",
)

# ── Edge case 8: LC79 Word Search ──
lc79_code = '''def exist(board, word):
    if not board or not board[0]:
        return False
    rows, cols = len(board), len(board[0])
    def dfs(r, c, i):
        if i == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols or board[r][c] != word[i]:
            return False
        tmp = board[r][c]
        board[r][c] = "#"
        found = dfs(r+1,c,i+1) or dfs(r-1,c,i+1) or dfs(r,c+1,i+1) or dfs(r,c-1,i+1)
        board[r][c] = tmp
        return found
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False
'''
r8 = run_case(
    "LC79 Word Search (recognized)",
    "Given an m x n grid of characters board and a string word, return true if word exists in the grid.",
    lc79_code,
)

print("\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)
for i, (label, r) in enumerate([
    ("constant_string", r1),
    ("constant_integer", r2),
    ("lc322_recognized", r3),
    ("code_only", r4),
    ("statement_only", r5),
    ("multiple_functions", r6),
    ("syntax_error", r7),
    ("lc79_recognized", r8),
], 1):
    verdict = r.get("verdict", "N/A")
    matched = r.get("matched", "N/A")
    print(f"  {i}. {label:30s} verdict={verdict:30s} matched={matched}")

"""CSSE Solver Generation — 20 solvers across 4 families.

Families:
  A1 (S0,P1): correct structure + micro-noise
  A2 (S0,P0): correct baseline (clean)
  B1 (S1,P0): structural defect only
  B2 (S1,P1): structural defect + micro-noise

S-axis (structural):
  S0 = correct DP subset-sum
  S1 = wrong state transition (dp[j] = True instead of dp[j - nums[i]])

P-axis (perturbation):
  P0 = clean
  P1 = 1-3 micro-errors from: off-by-one, missing edge case, wrong comparison

Each solver is a standalone `solve(nums, target) -> bool` function.
"""

from __future__ import annotations
import textwrap

SOLVERS = {}

# ══════════════════════════════════════════════════════════════════════════
# A2 — S0,P0: Correct clean solver (5 copies, structurally identical)
# ══════════════════════════════════════════════════════════════════════════

_A2_BODY = textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target, nums[i] - 1, -1):
                if dp[j - nums[i]]:
                    dp[j] = True
        return dp[target]
""")

for i in range(1, 6):
    SOLVERS[f"A2_{i:02d}"] = ("A2", "S0", "P0", _A2_BODY)


# ══════════════════════════════════════════════════════════════════════════
# A1 — S0,P1: Correct structure + 1-3 micro-noise errors
# ══════════════════════════════════════════════════════════════════════════

# Noise 1: off-by-one — inner loop starts at target instead of target-1
#   range(target, nums[i] - 1, -1) → range(target + 1, nums[i] - 1, -1)
#   This means dp[target] is never set from combining, only dp[0..target-1].
#   Affects: probes where the winning combination uses the full target range.
_NOISE_OFF_BY_ONE = textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target + 1, nums[i] - 1, -1):
                if dp[j - nums[i]]:
                    dp[j] = True
        return dp[target]
""")

# Noise 2: missing edge — does not return True for target==0
#   Removes the `if target == 0: return True` guard.
#   Affects: probe p17 (target=0, empty list), p20 (target=0, non-empty).
_NOISE_MISSING_EDGE = textwrap.dedent("""\
    def solve(nums, target):
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target, nums[i] - 1, -1):
                if dp[j - nums[i]]:
                    dp[j] = True
        return dp[target]
""")

# Noise 3: wrong comparison — `>=` instead of `>` in boundary check
#   Uses `if dp[j - nums[i]] >= True:` which is equivalent to `if dp[j - nums[i]]:`
#   Actually, let me use a real bug: `j - nums[i] > 0` instead of `>= 0`
#   This skips the case j == nums[i], meaning single-element matches fail.
_NOISE_WRONG_CMP = textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target, nums[i] - 1, -1):
                if j - nums[i] > 0 and dp[j - nums[i]]:
                    dp[j] = True
        return dp[target]
""")

# A1_01: noise 1 only (off-by-one)
SOLVERS["A1_01"] = ("A1", "S0", "P1", _NOISE_OFF_BY_ONE)

# A1_02: noise 2 only (missing edge)
SOLVERS["A1_02"] = ("A1", "S0", "P1", _NOISE_MISSING_EDGE)

# A1_03: noise 3 only (wrong comparison)
SOLVERS["A1_03"] = ("A1", "S0", "P1", _NOISE_WRONG_CMP)

# A1_04: noise 1 + noise 2
SOLVERS["A1_04"] = ("A1", "S0", "P1", textwrap.dedent("""\
    def solve(nums, target):
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target + 1, nums[i] - 1, -1):
                if dp[j - nums[i]]:
                    dp[j] = True
        return dp[target]
"""))

# A1_05: noise 1 + noise 3
SOLVERS["A1_05"] = ("A1", "S0", "P1", textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target + 1, nums[i] - 1, -1):
                if j - nums[i] > 0 and dp[j - nums[i]]:
                    dp[j] = True
        return dp[target]
"""))


# ══════════════════════════════════════════════════════════════════════════
# B1 — S1,P0: Structural defect only (no noise)
#
# S1: wrong state transition — dp[j] = True unconditionally when processing
#     element i, instead of dp[j] = dp[j] or dp[j - nums[i]].
#     This means once any element is processed, all reachable indices become
#     True regardless of whether the subset actually sums correctly.
#     Effect: if ANY element <= target, dp[j] is True for all j >= nums[i].
# ══════════════════════════════════════════════════════════════════════════

_B1_BODY = textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target, nums[i] - 1, -1):
                dp[j] = True
        return dp[target]
""")

for i in range(1, 6):
    SOLVERS[f"B1_{i:02d}"] = ("B1", "S1", "P0", _B1_BODY)


# ══════════════════════════════════════════════════════════════════════════
# B2 — S1,P1: Structural defect + micro-noise
#
# Same S1 structural bug as B1, plus the same noise variants as A1.
# The structural bug dominates, but noise adds extra failure modes.
# ══════════════════════════════════════════════════════════════════════════

# B2_01: S1 + noise 1 (off-by-one)
SOLVERS["B2_01"] = ("B2", "S1", "P1", textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target + 1, nums[i] - 1, -1):
                dp[j] = True
        return dp[target]
"""))

# B2_02: S1 + noise 2 (missing edge)
SOLVERS["B2_02"] = ("B2", "S1", "P1", textwrap.dedent("""\
    def solve(nums, target):
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target, nums[i] - 1, -1):
                dp[j] = True
        return dp[target]
"""))

# B2_03: S1 + noise 3 (wrong comparison)
SOLVERS["B2_03"] = ("B2", "S1", "P1", textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target, nums[i] - 1, -1):
                if j - nums[i] > 0:
                    dp[j] = True
        return dp[target]
"""))

# B2_04: S1 + noise 1 + noise 2
SOLVERS["B2_04"] = ("B2", "S1", "P1", textwrap.dedent("""\
    def solve(nums, target):
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target + 1, nums[i] - 1, -1):
                dp[j] = True
        return dp[target]
"""))

# B2_05: S1 + noise 1 + noise 3
SOLVERS["B2_05"] = ("B2", "S1", "P1", textwrap.dedent("""\
    def solve(nums, target):
        if target == 0:
            return True
        if not nums:
            return False
        n = len(nums)
        dp = [False] * (target + 1)
        dp[0] = True
        for i in range(n):
            for j in range(target + 1, nums[i] - 1, -1):
                if j - nums[i] > 0:
                    dp[j] = True
        return dp[target]
"""))


def get_solver_ids() -> list[str]:
    """Return sorted list of all solver IDs."""
    return sorted(SOLVERS.keys())


def get_solver(sid: str) -> tuple[str, str, str, str]:
    """Return (family, s_axis, p_axis, code) for a solver ID."""
    return SOLVERS[sid]

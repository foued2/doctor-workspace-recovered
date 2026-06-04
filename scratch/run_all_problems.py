"""Run pipeline on all 13 TEST_SUITES problems with correct solutions."""
import os, sys
os.environ["DOCTOR_ALLOW_UNTRUSTED_EXECUTION"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doctor.core.test_executor import TEST_SUITES
from doctor.registry.problem_registry import get_problem
from doctor.pipeline import run_pipeline

SOLUTIONS = {
    "two_sum": (
        "def twoSum(nums, target):\n"
        "    seen = {}\n"
        "    for i, n in enumerate(nums):\n"
        "        if target - n in seen:\n"
        "            return [seen[target - n], i]\n"
        "        seen[n] = i\n"
        "    return []"
    ),
    "lc3": (
        "def lengthOfLongestSubstring(s):\n"
        "    seen = set()\n"
        "    l = 0\n"
        "    max_len = 0\n"
        "    for r in range(len(s)):\n"
        "        while s[r] in seen:\n"
        "            seen.remove(s[l])\n"
        "            l += 1\n"
        "        seen.add(s[r])\n"
        "        max_len = max(max_len, r - l + 1)\n"
        "    return max_len"
    ),
    "lc42": (
        "def trap(height):\n"
        "    if not height:\n"
        "        return 0\n"
        "    l, r = 0, len(height) - 1\n"
        "    l_max, r_max = height[l], height[r]\n"
        "    water = 0\n"
        "    while l < r:\n"
        "        if l_max < r_max:\n"
        "            l += 1\n"
        "            l_max = max(l_max, height[l])\n"
        "            water += l_max - height[l]\n"
        "        else:\n"
        "            r -= 1\n"
        "            r_max = max(r_max, height[r])\n"
        "            water += r_max - height[r]\n"
        "    return water"
    ),
    "lc312": (
        "def maxCoins(nums):\n"
        "    nums = [1] + nums + [1]\n"
        "    n = len(nums)\n"
        "    dp = [[0] * n for _ in range(n)]\n"
        "    for length in range(2, n):\n"
        "        for i in range(n - length):\n"
        "            j = i + length\n"
        "            for k in range(i + 1, j):\n"
        "                dp[i][j] = max(dp[i][j], nums[i] * nums[k] * nums[j] + dp[i][k] + dp[k][j])\n"
        "    return dp[0][n - 1]"
    ),
    "lc743": (
        "def networkDelayTime(times, n, k):\n"
        "    import heapq\n"
        "    graph = {}\n"
        "    for u, v, w in times:\n"
        "        graph.setdefault(u, []).append((v, w))\n"
        "    dist = {}\n"
        "    pq = [(0, k)]\n"
        "    while pq:\n"
        "        d, node = heapq.heappop(pq)\n"
        "        if node in dist:\n"
        "            continue\n"
        "        dist[node] = d\n"
        "        for v, w in graph.get(node, []):\n"
        "            if v not in dist:\n"
        "                heapq.heappush(pq, (d + w, v))\n"
        "    return max(dist.values()) if len(dist) == n else -1"
    ),
    "lc406": (
        "def reconstructQueue(people):\n"
        "    people.sort(key=lambda p: (-p[0], p[1]))\n"
        "    result = []\n"
        "    for p in people:\n"
        "        result.insert(p[1], p)\n"
        "    return result"
    ),
    "lc494": (
        "def findTargetSumWays(nums, target):\n"
        "    from functools import lru_cache\n"
        "    @lru_cache(None)\n"
        "    def dfs(i, s):\n"
        "        if i == len(nums):\n"
        "            return 1 if s == target else 0\n"
        "        return dfs(i+1, s+nums[i]) + dfs(i+1, s-nums[i])\n"
        "    return dfs(0, 0)"
    ),
    "lc875": (
        "def minEatingSpeed(piles, h):\n"
        "    lo, hi = 1, max(piles)\n"
        "    while lo < hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        hours = sum((p + mid - 1) // mid for p in piles)\n"
        "        if hours <= h:\n"
        "            hi = mid\n"
        "        else:\n"
        "            lo = mid + 1\n"
        "    return lo"
    ),
    "lc134": (
        "def canCompleteCircuit(gas, cost):\n"
        "    total, cur, start = 0, 0, 0\n"
        "    for i in range(len(gas)):\n"
        "        total += gas[i] - cost[i]\n"
        "        cur += gas[i] - cost[i]\n"
        "        if cur < 0:\n"
        "            start = i + 1\n"
        "            cur = 0\n"
        "    return start if total >= 0 else -1"
    ),
    "lc1029": (
        "def twoCitySchedCost(costs):\n"
        "    costs.sort(key=lambda x: x[0] - x[1])\n"
        "    n = len(costs) // 2\n"
        "    return sum(c[0] for c in costs[:n]) + sum(c[1] for c in costs[n:])"
    ),
    "lc322": (
        "def coinChange(coins, amount):\n"
        "    dp = [float('inf')] * (amount + 1)\n"
        "    dp[0] = 0\n"
        "    for i in range(1, amount + 1):\n"
        "        for c in coins:\n"
        "            if c <= i:\n"
        "                dp[i] = min(dp[i], dp[i-c] + 1)\n"
        "    return dp[amount] if dp[amount] != float('inf') else -1"
    ),
    "cf607a": (
        "def solve(n, a):\n"
        "    a.sort()\n"
        "    count = 1\n"
        "    for i in range(1, n):\n"
        "        if a[i] != a[i-1]:\n"
        "            count += 1\n"
        "    return count"
    ),
    "arrange_numbers_divisible": (
        "def arrange_numbers_divisible(n, k):\n"
        "    result = []\n"
        "    for i in range(1, n + 1):\n"
        "        if i % k == 0:\n"
        "            result.append(i)\n"
        "    return result if result else [-1]"
    ),
}

for problem_id in sorted(TEST_SUITES.keys()):
    p = get_problem(problem_id)
    desc = p.get("description", "") if p else ""
    sol = SOLUTIONS.get(problem_id, "")
    if not desc:
        print(f"{problem_id}: NO DESCRIPTION IN REGISTRY")
        continue
    if not sol:
        print(f"{problem_id}: NO SOLUTION DEFINED")
        continue
    r = run_pipeline(desc, sol)
    verdict = r.get("verdict", "?")
    matched = r.get("matched", "?")
    risk = r.get("risk", "?")
    stages = r.get("pipeline", {})
    executor = stages.get("executor", {})
    exec_pass = executor.get("passed", "?")
    exec_total = executor.get("total", "?")
    print(f"{problem_id}: verdict={verdict} matched={matched} risk={risk} executor={exec_pass}/{exec_total}")

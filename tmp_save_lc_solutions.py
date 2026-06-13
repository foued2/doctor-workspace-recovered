import os

OUT_DIR = "human_solvers"

solutions = {
    "lc_leetcode_bottomup_dp": '''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        dp = [0] + ([float("inf")] * amount)
        for i in range(1, amount + 1):
            for coin in coins:
                if coin <= i:
                    dp[i] = min(dp[i], dp[i - coin] + 1)
        if dp[-1] == float("inf"):
            return -1
        return dp[-1]
''',
    "lc_recursive_no_memo": '''class Solution:
    def coinChange(self, coins: list[int], amount: int) -> int:
        if amount < 0:
            return -1
        if amount == 0:
            return 0
        min_count = float("inf")
        for coin in coins:
            res = self.coinChange(coins, amount - coin)
            if res != -1:
                min_count = min(min_count, 1 + res)
        return min_count if min_count != float("inf") else -1
''',
    "lc_recursive_with_memo": '''class Solution:
    def coinChange(self, coins: list[int], amount: int) -> int:
        memo = {}
        def solve(rem):
            if rem < 0:
                return -1
            if rem == 0:
                return 0
            if rem in memo:
                return memo[rem]
            min_count = float("inf")
            for coin in coins:
                res = solve(rem - coin)
                if res != -1:
                    min_count = min(min_count, 1 + res)
            memo[rem] = min_count if min_count != float("inf") else -1
            return memo[rem]
        return solve(amount)
''',
    "lc_bottomup_dp_v2": '''class Solution:
    def coinChange(self, coins: list[int], amount: int) -> int:
        dp = [amount + 1] * (amount + 1)
        dp[0] = 0
        for i in range(1, amount + 1):
            for coin in coins:
                if i - coin >= 0:
                    dp[i] = min(dp[i], 1 + dp[i - coin])
        return dp[amount] if dp[amount] != amount + 1 else -1
''',
    "lc_bottomup_dp_v3": '''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        min_coins = [amount + 1] * (amount + 1)
        min_coins[0] = 0
        for i in range(1, amount + 1):
            for c in coins:
                if i - c >= 0:
                    min_coins[i] = min(min_coins[i], 1 + min_coins[i - c])
        return min_coins[-1] if min_coins[-1] != amount + 1 else -1
''',
    "lc_2d_dp": '''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        n = len(coins)
        INF = float("inf")
        dp = [[INF] * (amount + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = 0
        for i in range(1, n + 1):
            for j in range(1, amount + 1):
                if coins[i-1] <= j:
                    dp[i][j] = min(1 + dp[i][j - coins[i-1]], dp[i-1][j])
                else:
                    dp[i][j] = dp[i-1][j]
        return dp[n][amount] if dp[n][amount] != INF else -1
''',
    "lc_bottomup_dp_v4": '''class Solution(object):
    def coinChange(self, coins, amount):
        max_value = amount + 1
        dp = [max_value] * (amount + 1)
        dp[0] = 0
        for coin in coins:
            for x in range(coin, amount + 1):
                dp[x] = min(dp[x], dp[x - coin] + 1)
        return dp[amount] if dp[amount] != max_value else -1
''',
    "lc_greedy_gcd": '''from math import gcd
class Solution:
    @staticmethod
    def coinChange(coins, target):
        if target == 0:
            return 0
        n = len(coins)
        if n == 1:
            return target // coins[0] if target % coins[0] == 0 else -1
        coins.sort()
        minCoin = coins[0]
        if target == minCoin:
            return 1
        idx = 1
        gcdVal = minCoin
        while idx < n and target >= coins[idx]:
            if target == coins[idx]:
                return 1
            gcdVal = gcd(coins[idx], gcdVal)
            coins[idx] -= minCoin
            idx += 1
        if target % gcdVal != 0:
            return -1
        minVal = (target - 1) // (coins[idx - 1] + minCoin) + 1
        maxVal = target // minCoin
        for i in range(minVal, maxVal + 1):
            if Solution.findCombination(coins, 1, idx - 1, target - i * minCoin, i):
                return i
        return -1
    @staticmethod
    def findCombination(coins, left, right, target, maxCoins):
        if target == 0:
            return True
        if target < coins[left] or target // coins[right] > maxCoins:
            return False
        if target % coins[right] == 0:
            return True
        if left == right:
            return False
        for k in range(target // coins[right] + 1):
            if Solution.findCombination(coins, left, right - 1, target - k * coins[right], maxCoins - k):
                return True
        return False
''',
    "lc_bfs_v1": '''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        q = deque()
        visit = set([0])
        q.append([0,0])
        while q:
            curr,steps = q.popleft()
            if curr == amount:
                return steps
            for coin in coins:
                nxt = curr + coin
                if nxt <= amount and nxt not in visit:
                    q.append((nxt,steps+1))
                    visit.add(nxt)
        return -1
''',
    "lc_bfs_v2": '''def coinChange(self, coins: List[int], amount: int) -> int:
        q = deque([(amount,0)])
        visited = set()
        while q:
            cur, n_coins = q.popleft()
            if cur == 0:
                return n_coins
            for c in coins:
                new_cur = cur - c
                if new_cur in visited or new_cur < 0:
                    continue
                q.append((new_cur,n_coins+1))
                visited.add(new_cur)
        return -1
''',
    "lc_bfs_v3": '''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        if amount == 0:
            return 0
        if amount in coins:
            return 1
        queue = deque([(amount, 0)])
        lookup = set([amount])
        while queue:
            remainingAmount, coinsUsed = queue.popleft()
            if remainingAmount == 0:
                return coinsUsed
            for coin in coins:
                if remainingAmount - coin >= 0 and remainingAmount - coin not in lookup:
                    queue.append((remainingAmount - coin, coinsUsed + 1))
                    lookup.add(remainingAmount - coin)
        return -1
''',
    "lc_bottomup_dp_v5": '''class Solution:
    def coinChange(self, coins, amount):
        dp = [float("inf")] * (amount + 1)
        dp[0] = 0
        for coin in coins:
            for i in range(coin, amount + 1):
                dp[i] = min(dp[i], dp[i - coin] + 1)
        return dp[amount] if dp[amount] != float("inf") else -1
''',
    "lc_bfs_v4": '''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        queue = deque()
        queue.append([0,0])
        visited = set()
        while queue:
            current, level = queue.popleft()
            if current == amount:
                return level
            for coin in coins:
                candidate = current+coin
                if candidate <= amount and candidate not in visited:
                    queue.append([candidate, level+1])
                    visited.add(candidate)
        return -1
''',
    "lc_2d_dp_v2": '''class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        n = len(coins)
        INF = float("inf")
        dp = [[INF] * (amount + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = 0
        for i in range(1, n + 1):
            for j in range(1, amount + 1):
                if coins[i-1] <= j:
                    dp[i][j] = min(1 + dp[i][j - coins[i-1]], dp[i-1][j])
                else:
                    dp[i][j] = dp[i-1][j]
        return dp[n][amount] if dp[n][amount] != INF else -1
''',
}

os.makedirs(OUT_DIR, exist_ok=True)

for name, code in solutions.items():
    filepath = f"{OUT_DIR}/{name}.py"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Saved: {name}.py ({len(code)} bytes)")

print(f"\nTotal: {len(solutions)} files")

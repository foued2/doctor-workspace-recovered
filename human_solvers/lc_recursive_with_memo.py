class Solution:
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

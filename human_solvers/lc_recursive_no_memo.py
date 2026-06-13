class Solution:
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

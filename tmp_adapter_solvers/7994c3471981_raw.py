from math import gcd
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

def solve(coins, amount):
    dp = [amount] * (amount + 1)  # BUG: should be float('inf')
    dp[0] = 0
    for i in range(1, amount + 1):
        for coin in coins:
            if i - coin >= 0:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    return dp[amount] if dp[amount] != amount else -1

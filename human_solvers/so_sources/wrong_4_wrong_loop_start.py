def solve(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for i in range(0, amount + 1):  # BUG: should start at 1
        for coin in coins:
            if i - coin >= 0:
                dp[i] = min(dp[i], dp[i - coin] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1

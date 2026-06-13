def coinChange(coins, amount):
    coins.sort()
    dp = [0] + [float('inf')] * amount
    for i in coins:
        for j in range(i, amount + 1):
            dp[j] = min(dp[j], int(j / i) + dp[j % i])
    if dp[-1] == float('inf'):
        return -1
    else:
        return dp[-1]

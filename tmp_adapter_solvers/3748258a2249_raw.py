class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        """
        :type coins: List[int]
        :type amount: int
        :rtype: int
        """
        # Create a table to store the minimum number of coins required to make up the amount
        dp = [float('inf')] * (amount + 1)
        dp[0] = 0
        
        # Iterate through all the coins and update the table for every amount value
        for coin in coins:
            for i in range(coin, amount + 1):
                dp[i] = min(dp[i], dp[i - coin] + 1)
                
        # Check if it's possible to make up the amount with given coins
        return dp[amount] if dp[amount] != float('inf') else -1
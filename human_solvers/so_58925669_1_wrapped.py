import sys

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    lookup_dict = {}
    minimum = sys.maxsize

    def coinChangeAux(coins, amount):
        nonlocal minimum
        if amount in lookup_dict:
            return lookup_dict[amount]
        if amount <= 0:
            lookup_dict[amount] = 0
            return 0
        if not coins:
            return -1
        for i in coins:
            if amount >= i:
                minimum = min(minimum, coinChange(coins, amount - i) + 1)
        lookup_dict[amount] = minimum
        return lookup_dict[amount]

    def coinChange(coins, amount):
        result = coinChangeAux(coins, amount)
        return -1 if result == sys.maxsize else result

    return coinChange(coins, amount)

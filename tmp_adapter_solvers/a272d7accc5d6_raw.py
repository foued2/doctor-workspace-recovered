import sys

lookup_dict = {}
minimum = sys.maxsize

def coinChange(coins, amount):
    result = coinChangeAux(coins, amount)
    return -1 if result == sys.maxsize else result

def coinChangeAux(coins, amount):
    global minimum, lookup_dict
    if amount in lookup_dict.keys():
        return lookup_dict[amount]
    if amount <= 0:
        lookup_dict[amount] = 0
        return lookup_dict[amount]
    if not coins:
        return -1
    for i in coins:
        if amount >= i:
            minimum = min(minimum, coinChange(coins, amount - i) + 1)
    lookup_dict[amount] = minimum
    return lookup_dict[amount]

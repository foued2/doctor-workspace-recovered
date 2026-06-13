
from aa13a340f3ad0_raw import Solution

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return Solution().coinChange(coins, amount)

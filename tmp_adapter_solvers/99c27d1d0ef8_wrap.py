
from 99c27d1d0ef8_raw import Solution

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return Solution().coinChange(coins, amount)

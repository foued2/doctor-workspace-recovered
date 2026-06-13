
from a4a6bddf36273_raw import coinChange as _fn

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return _fn(coins, amount)

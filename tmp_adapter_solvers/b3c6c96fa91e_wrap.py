
from b3c6c96fa91e_raw import solve as _raw_solve

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return _raw_solve(coins, amount)

from doctor.solvers.lc322.lc_322_solvers import solve_20
import concurrent.futures

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(solve_20, coins, amount)
        try:
            return future.result(timeout=5.0)
        except concurrent.futures.TimeoutError:
            return -1
        except Exception:
            return -1
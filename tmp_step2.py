"""Step 2: Run C-4 evaluation for LC756. Raw output only."""
import sys, json
sys.path.insert(0, r"C:\Users\pakla\PycharmProjects\doctor-workspace-recovered")

from runners.run_c4_lc756 import run_all_solvers, estimate

results = run_all_solvers()
estimates = estimate(results)

# Print raw output only
print(json.dumps(estimates, indent=2))

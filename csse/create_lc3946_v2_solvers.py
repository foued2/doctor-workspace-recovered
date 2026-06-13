"""Create solver files for LC3946 second population."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
solvers_dir = ROOT / "experiments" / "frozen_taxonomy_lc3946_v2" / "solvers"
solvers_dir.mkdir(parents=True, exist_ok=True)

# Create solver files
for i in range(1, 31):
    solver_id = f"solver_{i:03d}"
    content = f'''"""LC3946 v2 solver {solver_id}."""
from doctor.adversarial.lc3946_candidates_v2 import {solver_id} as _impl


def solve(solver_input: list) -> int:
    return _impl(solver_input)
'''
    
    solver_path = solvers_dir / f"{solver_id}.py"
    with open(solver_path, "w") as f:
        f.write(content)

print(f"Created {len(list(solvers_dir.glob('solver_*.py')))} solver files in {solvers_dir}")

"""Generate frozen v2 solver files for LC45 and LC743."""
from pathlib import Path

# LC45 v2
lc45_v2_dir = Path('experiments/frozen_taxonomy_lc45_v2/solvers')
lc45_v2_dir.mkdir(parents=True, exist_ok=True)

for i in range(1, 11):
    content = f'''"""LC45 v2 frozen solver {i:03d}."""
from __future__ import annotations
from doctor.adversarial.lc45_candidates_v2 import solver_{i:03d} as _impl

def solve(nums):
    return _impl(nums)
'''
    (lc45_v2_dir / f'solver_{i:03d}.py').write_text(content)

print(f'Created {len(list(lc45_v2_dir.glob("solver_*.py")))} LC45 v2 solvers')

# LC743 v2
lc743_v2_dir = Path('experiments/frozen_taxonomy_lc743_v2/solvers')
lc743_v2_dir.mkdir(parents=True, exist_ok=True)

for i in range(1, 32):
    content = f'''"""LC743 v2 frozen solver {i:03d}."""
from __future__ import annotations
from doctor.adversarial.lc743_candidates_v2 import solver_{i:03d} as _impl

def solve(times, n, k):
    return _impl(times, n, k)
'''
    (lc743_v2_dir / f'solver_{i:03d}.py').write_text(content)

print(f'Created {len(list(lc743_v2_dir.glob("solver_*.py")))} LC743 v2 solvers')

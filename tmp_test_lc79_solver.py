import sys
sys.path.insert(0, '.')
from doctor.adversarial.problem_class_config import get_problem_class_config
import json

config = get_problem_class_config('lc79')

with open('data/midweather_fingerprint_lc79_probe_index.json') as f:
    probe_data = json.load(f)

# Load a correct solver
import importlib.util
spec = importlib.util.spec_from_file_location('s001', 'doctor/adversarial/lc79_candidates/s001_correct_std.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
solve_fn = module.solve

# Test on first probe
probe = probe_data['probes'][0]
solver_input = config.probe_to_solver_input(probe)
result = solve_fn(solver_input['board'], solver_input['word'])
oracle_result = config.oracle(solver_input)
print(f'Probe: {probe["probe_id"]}')
print(f'Solver result: {result}')
print(f'Oracle result: {oracle_result}')
print(f'Match: {result == oracle_result}')

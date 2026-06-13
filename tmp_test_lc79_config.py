import sys
sys.path.insert(0, '.')
from doctor.adversarial.problem_class_config import get_problem_class_config

config = get_problem_class_config('lc79')
print('Config loaded successfully')
print(f'problem_id: {config.problem_id}')
print(f'solver_entry_point: {config.solver_entry_point}')
print(f'estimator_names: {config.estimator_names}')
print(f'fingerprint_axes: {config.fingerprint_axes}')
print(f'oracle type: {type(config.oracle)}')
print(f'probe_to_solver_input type: {type(config.probe_to_solver_input)}')
print(f'raw_tensor_encoder type: {type(config.raw_tensor_encoder)}')
print(f'C_genuine policy: {config.estimator_policies["C_genuine"]}')
print(f'B1 policy: {config.estimator_policies["B1_count"]}')

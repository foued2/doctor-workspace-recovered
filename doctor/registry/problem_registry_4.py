from doctor.registry.problem_registry import get_problems
import json

registry = get_problems()
ref_solution = registry['two_sum']['spec']['reference_solution']

with open('F:/pythonProject1/scratch/candidate_two_sum.json') as f:
    candidate = json.load(f)

print('Reference solution:')
print(ref_solution[:200])
print()
print('Test cases to validate:')

exec_globals = {}
exec(ref_solution, exec_globals)
two_sum_fn = exec_globals['twoSum']

for tc in candidate['execution']['test_cases']:
    raw_input = tc['input']
    expected = tc['expected']

    lines = [l.strip() for l in raw_input.strip().split('\n') if l.strip()]

    if len(lines) == 1:
        parts = raw_input.split()
        n = int(parts[0])
        arr = [int(x) for x in parts[1:1+n]]
        target = int(parts[1+n])
    elif len(lines) == 2:
        n = int(lines[0])
        arr = list(map(int, lines[1].split()))
        target = int(lines[1].split()[0])
    else:
        parts = raw_input.replace('\n', ' ').split()
        n = int(parts[0])
        arr = [int(x) for x in parts[1:1+n]]
        target = int(parts[1+n])

    result = two_sum_fn(arr, target)
    result_str = f"[{result[0]}, {result[1]}]"
    expected_str = f"[{expected.split()[0]}, {expected.split()[1]}]"
    passed = result_str == expected_str
    status = 'PASS' if passed else 'FAIL'
    print(f"  {tc['label']}: {status}")
    print(f"    input: n={n}, arr={arr}, target={target}")
    print(f"    expected: {expected_str}")
    print(f"    got: {result_str}")
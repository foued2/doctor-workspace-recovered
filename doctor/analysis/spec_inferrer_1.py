from doctor.analysis.spec_inferrer import _generate_probes, _load_solution, _safe_call, _axis3_non_trivial
import json

stmt = "Given a list of integers nums, return a list of all peak elements. An element is a peak if it is strictly greater than its immediate neighbors. Elements at the boundaries are never peaks."
code = "def find_peaks(nums):\n    result = []\n    for i in range(1, len(nums) - 1):\n        if nums[i] > nums[i-1] and nums[i] > nums[i+1]:\n            result.append(nums[i])\n    return result\n"

spec = {
    "inferred_input_schema": {"nums": "list"},
    "inferred_output_shape": "list",
    "constraint_hypotheses": [
        "output contains only elements satisfying a local predicate",
        "output elements satisfy a strict local comparison constraint"
    ],
    "ambiguity_flags": ["single_valid_solution_unconfirmed"],
    "completeness_score": 0.75,
    "canonical_form": "Given nums: list, return list where output contains only elements satisfying a local predicate"
}

probes = _generate_probes(spec)
print("Probes:", probes)

fn = _load_solution(code)
results = []
for args in probes:
    ok, out = _safe_call(fn, args)
    print(f"Args: {args}, Ok: {ok}, Output: {out}")
    if ok:
        results.append((args, out))

print("\nAxis 3 check:", _axis3_non_trivial(results))
print("Number of unique outputs:", len(set(str(r[1]) for r in results)))

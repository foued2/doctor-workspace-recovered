from doctor.pipeline import run_pipeline
import json

stmt = "Given a list of integers nums, return the maximum difference between any two elements where the larger element appears after the smaller one."
code = "def max_difference(nums):\n    if not nums:\n        return 0\n    min_so_far = nums[0]\n    max_diff = 0\n    for x in nums[1:]:\n        max_diff = max(max_diff, x - min_so_far)\n        min_so_far = min(min_so_far, x)\n    return max_diff\n"

r = run_pipeline(stmt, code)
print("=== IND-10 spec_hypothesis ===")
print(json.dumps(r.get('spec_hypothesis', {}), indent=2))
print("\neligible:", r.get('induction_result', {}).get('eligible'))
print("reason:", r.get('induction_result', {}).get('rejection_reason'))

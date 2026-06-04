"""Verify agreement path works end-to-end after checker_gen fix."""
import sys
sys.path.insert(0, ".")
from doctor.pipeline import run_pipeline

r = run_pipeline(
    statement="Given an array of integers and a target, return indices of two numbers that add up to target.",
    solution_code='def twoSum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n    return []'
)
print("verdict:", r.get("verdict"))
print("matched:", r.get("matched"))
print("pass_rate:", r.get("pass_rate"))
print("risk:", r.get("risk"))

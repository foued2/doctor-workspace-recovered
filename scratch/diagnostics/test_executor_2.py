"""
Evidence Policy Layer — rule-based classification on top of existing signals.
No scoring changes. No modifications to evidence computation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from doctor.test_executor import TestExecutor
from doctor.evidence import compute_evidence_components
from doctor.evidence_policy import classify_evidence

executor = TestExecutor()

SOLUTIONS = {
    "Two Sum": {
        "correct": """
def twoSum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
""",
        "partial": """
def twoSum(nums, target):
    for i in range(min(2, len(nums))):
        for j in range(i+1, min(3, len(nums))):
            if nums[i] + nums[j] == target:
                return [i, j]
    return None
""",
        "error": """
def twoSum(nums, target):
    return [nums.index(target), nums.index(0)]
""",
    },
    "Trapping Rain Water": {
        "correct": """
def trap(height):
    if not height:
        return 0
    left, right = 0, len(height) - 1
    left_max, right_max = height[left], height[right]
    water = 0
    while left < right:
        if left_max < right_max:
            left += 1
            left_max = max(left_max, height[left])
            water += max(0, left_max - height[left])
        else:
            right -= 1
            right_max = max(right_max, height[right])
            water += max(0, right_max - height[right])
    return water
""",
        "partial": """
def trap(height):
    if len(height) < 3:
        return 0
    water = 0
    for i in range(1, len(height) - 1):
        if height[i] < height[i-1] and height[i] < height[i+1]:
            water += min(height[i-1], height[i+1]) - height[i]
    return water
""",
        "error": """
def trap(height):
    return height[0] - height[-1]
""",
    },
    "Valid Parentheses": {
        "correct": """
def isValid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return not stack
""",
        "partial": """
def isValid(s):
    return s.count('(') == s.count(')') and s.count('[') == s.count(']') and s.count('{') == s.count('}')
""",
        "error": """
def isValid(s):
    return s.count('(') + s.count('[') + int(s)
""",
    },
}

for problem_name, sols in SOLUTIONS.items():
    for kind, code in sols.items():
        report = executor.verify(problem_name, code)
        components = compute_evidence_components(report.traces, report.total, report.passed)
        classification = classify_evidence(components["pass_ratio"], components["has_error"])
        print({
            "problem": problem_name,
            "kind": kind,
            "pass_ratio": components["pass_ratio"],
            "has_error": components["has_error"],
            "classification": classification,
        })

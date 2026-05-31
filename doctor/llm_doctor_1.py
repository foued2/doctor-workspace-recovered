import sys
sys.path.insert(0, r'F:\pythonProject')
from doctor.llm_doctor import predict
import json

# Test 1: Partial - only odd-length palindromes (misses even)
partial_lps = """PROBLEM: Longest Palindromic Substring
SOLUTION:
def longestPalindrome(s):
    if not s: return ""
    start = 0
    max_len = 1
    for i in range(len(s)):
        # Only odd-length expansion
        l, r = i-1, i+1
        while l >= 0 and r < len(s) and s[l] == s[r]:
            if r - l + 1 > max_len:
                start = l
                max_len = r - l + 1
            l -= 1
            r += 1
    return s[start:start+max_len]
"""

# Test 2: Incorrect - Two Sum using same element twice
wrong_twosum = """PROBLEM: Two Sum
SOLUTION:
def twoSum(nums, target):
    for i in range(len(nums)):
        if nums[i] + nums[i] == target:
            return [i, i]
    return []
"""

# Test 3: Partial - Valid Parentheses counter only (ignores ordering)
partial_vp = """PROBLEM: Valid Parentheses
SOLUTION:
def isValid(s):
    count = 0
    for c in s:
        if c == '(':
            count += 1
        elif c == ')':
            count -= 1
        if count < 0:
            return False
    return count == 0
"""

for name, code in [("LPS_partial", partial_lps), ("TwoSum_incorrect", wrong_twosum), ("VP_partial", partial_vp)]:
    r = predict(code)
    bi = r.get('system_bias_indicators', {})
    print(f"\n{name}:")
    print(f"  label={r['label']}, conf={r['confidence']}")
    print(f"  severity={bi.get('layer2_severity')}, ratio={bi.get('layer2_failure_ratio')}")
    print(f"  core_fail={bi.get('layer2_core_failures')}, edge_fail={bi.get('layer2_edge_failures')}")
    print(f"  decision_path={r['decision_path']}")

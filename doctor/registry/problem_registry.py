#!/usr/bin/env python3
"""Find registry problems related to counting."""
import sys
sys.path.insert(0, '.')

from doctor.registry.problem_registry import get_problems

problems = get_problems()

print("Problems with 'count' in keywords or description:")
print("=" * 80)

for pid, p in problems.items():
    keywords = p.get('keywords', [])
    desc = p.get('description', '')
    
    if 'count' in keywords or 'count' in desc.lower():
        print(f"\n{pid}:")
        print(f"  Keywords: {keywords[:5]}")
        print(f"  Description: {desc[:80]}")
        
        # Check test cases for empty list
        test_cases = p.get('test_cases', [])
        has_empty = any(tc.get('input') == [] for tc in test_cases)
        print(f"  Has empty list test: {has_empty}")
        print(f"  Num test cases: {len(test_cases)}")

#!/usr/bin/env python3
"""
Schema classifier: given a problem statement, outputs domain, paradigm, dp_type, confidence.
Uses few-shot examples from ground truth labels.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from doctor.llm_client import _call_llm_with_stats

# Few-shot examples drawn from ground truth labels
FEW_SHOT = (
    "Example 1:\n"
    "Statement: Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n"
    "Output: {\"domain\": \"array\", \"paradigm\": \"hashing\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 2:\n"
    "Statement: Given an integer x, return true if x reads the same forward and backward.\n"
    "Output: {\"domain\": \"math\", \"paradigm\": \"reversal\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 3:\n"
    "Statement: Given an integer array nums, return the contiguous subarray with the largest sum.\n"
    "Output: {\"domain\": \"array\", \"paradigm\": \"dynamic_programming\", \"dp_type\": \"1D\", \"confidence\": \"high\"}\n\n"
    "Example 4:\n"
    "Statement: Given two strings s and t, return the minimum window substring of s such that every character in t is included.\n"
    "Output: {\"domain\": \"string\", \"paradigm\": \"sliding_window\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 5:\n"
    "Statement: Given an integer n, return all distinct solutions to the n-queens puzzle.\n"
    "Output: {\"domain\": \"matrix\", \"paradigm\": \"backtracking\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 6:\n"
    "Statement: Return the sum of the even-valued Fibonacci terms that do not exceed n.\n"
    "Output: {\"domain\": \"math\", \"paradigm\": \"iterative\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 7:\n"
    "Statement: Return the largest prime factor of n.\n"
    "Output: {\"domain\": \"math\", \"paradigm\": \"trial_division\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 8:\n"
    "Statement: Given a Roman numeral string, convert it to its integer value.\n"
    "Output: {\"domain\": \"string\", \"paradigm\": \"accumulation\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 9:\n"
    "Statement: Implement the myAtoi(string s) function, which converts a string to a 32-bit signed integer.\n"
    "Output: {\"domain\": \"string\", \"paradigm\": \"finite_state_machine\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 10:\n"
    "Statement: Given an integer, convert it to a Roman numeral.\n"
    "Output: {\"domain\": \"math\", \"paradigm\": \"greedy\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 11:\n"
    "Statement: Given a string s and an integer numRows, write the characters of s in a zigzag pattern on numRows.\n"
    "Output: {\"domain\": \"string\", \"paradigm\": \"simulation\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 12:\n"
    "Statement: Given an unsorted integer array nums, return the smallest missing positive integer.\n"
    "Output: {\"domain\": \"array\", \"paradigm\": \"in_place_hashing\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 13:\n"
    "Statement: Given an array of integers heights representing histogram bar heights, return the area of the largest rectangle.\n"
    "Output: {\"domain\": \"array\", \"paradigm\": \"monotonic_stack\", \"dp_type\": \"\", \"confidence\": \"high\"}\n\n"
    "Example 14:\n"
    "Statement: Given two strings haystack and needle, return the index of the first occurrence of needle in haystack.\n"
    "Output: {\"domain\": \"string\", \"paradigm\": \"string_matching\", \"dp_type\": \"\", \"confidence\": \"high\"}\n"
)

PROMPT_START = (
    "Classify this problem statement into schema fields.\n\n"
    "Return only valid JSON:\n"
    "{\n"
    '  "domain": "array|string|math|matrix|linked_list|tree|graph",\n'
    '  "paradigm": "hashing|two_pointer|reversal|backtracking|dynamic_programming|recursive|iterative|greedy|stack_based|sliding_window|binary_search|other",\n'
    '  "traversal": "specific algorithm pattern (e.g., two_pointer, expand_around_center, bottom_up, backtracking)",\n'
    '  "data_structures": ["list", "of", "data", "structures", "needed"],\n'
    '  "tags": ["relevant", "context", "tags"],\n'
    '  "dp_type": "1D|2D|",\n'
    '  "confidence": "high|low"\n'
    "}\n\n"
    "Rules:\n"
    "- domain: structural data type the problem operates on\n"
    "- paradigm: primary algorithmic technique\n"
    "- traversal: specific algorithm pattern or approach\n"
    "- data_structures: list of data structures the solution will use\n"
    "- tags: list of relevant context tags (difficulty, techniques, etc.)\n"
    "- dp_type: only fill if problem uses dynamic programming\n"
    "- confidence: high if clear, low if ambiguous.\n\n"
)

PROMPT_END = "\n\nOutput JSON:"


def classify_schema(statement):
    """Classify problem statement into schema fields.
    
    Returns: {"domain": str, "paradigm": str, "dp_type": str, "confidence": str}
    """
    prompt = PROMPT_START + FEW_SHOT + "Statement: " + statement + PROMPT_END

    try:
        response, _ = _call_llm_with_stats(prompt)
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
            if text.startswith("json"):
                text = text[4:].lstrip()
        data = json.loads(text.strip())
        return {
            "domain": data.get("domain", ""),
            "paradigm": data.get("paradigm", ""),
            "traversal": data.get("traversal", ""),
            "data_structures": data.get("data_structures", []),
            "tags": data.get("tags", []),
            "dp_type": data.get("dp_type", ""),
            "confidence": data.get("confidence", "low")
        }
    except Exception as e:
        return {
            "domain": "",
            "paradigm": "",
            "dp_type": "",
            "confidence": "",
            "error": str(e)
        }


if __name__ == "__main__":
    # Quick test
    test_statement = "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
    result = classify_schema(test_statement)
    print(json.dumps(result, indent=2))

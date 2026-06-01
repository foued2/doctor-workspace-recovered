from __future__ import annotations

from typing import Any, Dict, Optional


PROBLEMS: Dict[str, Dict[str, Any]] = {
    "two_sum": {
        "name": "Two Sum",
        "keywords": ["array", "hash", "two sum", "pair", "target"],
        "description": "Given an array of integers and a target, return indices of two numbers that add up to target.",
        "spec": {"verifiable": True},
    },
    "lc3": {
        "name": "Longest Substring Without Repeating Characters",
        "keywords": ["string", "sliding window", "substring", "longest"],
        "description": "Given a string, find the length of the longest substring without repeating characters.",
        "spec": {"verifiable": True},
    },
    "lc20": {
        "name": "Valid Parentheses",
        "keywords": ["stack", "string", "parentheses", "brackets"],
        "description": "Given a string of parentheses, determine if it is valid.",
        "spec": {"verifiable": True},
    },
    "lc33": {
        "name": "Search in Rotated Sorted Array",
        "keywords": ["binary search", "array", "rotated", "sorted"],
        "description": "Search for a target in a rotated sorted array.",
        "spec": {"verifiable": True},
    },
    "lc42": {
        "name": "Trapping Rain Water",
        "keywords": ["array", "two pointers", "stack", "trapping", "water"],
        "description": "Given n non-negative integers, compute how much water it can trap after raining.",
        "spec": {"verifiable": True},
    },
    "lc45": {
        "name": "Jump Game II",
        "keywords": ["array", "greedy", "dynamic programming", "jump"],
        "description": "Given an array of non-negative integers, find minimum jumps to reach the last index.",
        "spec": {"verifiable": True},
    },
    "lc53": {
        "name": "Maximum Subarray",
        "keywords": ["array", "dynamic programming", "divide and conquer", "subarray"],
        "description": "Find the contiguous subarray with the largest sum.",
        "spec": {"verifiable": True},
    },
    "lc70": {
        "name": "Climbing Stairs",
        "keywords": ["dynamic programming", "climbing", "stairs", "fibonacci"],
        "description": "Given n steps, find how many distinct ways to climb to the top.",
        "spec": {"verifiable": True},
    },
    "lc79": {
        "name": "Word Search",
        "keywords": ["backtracking", "matrix", "word", "search"],
        "description": "Given a 2D board and a word, find if the word exists in the grid.",
        "spec": {"verifiable": True},
    },
    "lc97": {
        "name": "Interleaving String",
        "keywords": ["dynamic programming", "string", "interleaving"],
        "description": "Determine if s3 is formed by interleaving s1 and s2.",
        "spec": {"verifiable": True},
    },
    "lc118": {
        "name": "Pascal's Triangle",
        "keywords": ["array", "dynamic programming", "pascal"],
        "description": "Given numRows, generate Pascal's triangle.",
        "spec": {"verifiable": True},
    },
    "lc121": {
        "name": "Best Time to Buy and Sell Stock",
        "keywords": ["array", "dynamic programming", "stock", "buy", "sell"],
        "description": "Find the maximum profit from buying and selling a stock once.",
        "spec": {"verifiable": True},
    },
    "lc128": {
        "name": "Longest Consecutive Sequence",
        "keywords": ["array", "hash set", "consecutive", "sequence"],
        "description": "Find the length of the longest consecutive elements sequence.",
        "spec": {"verifiable": True},
    },
    "lc134": {
        "name": "Gas Station",
        "keywords": ["array", "greedy", "gas", "station"],
        "description": "Find the starting gas station to complete a circular tour.",
        "spec": {"verifiable": True},
    },
    "lc135": {
        "name": "Candy",
        "keywords": ["array", "greedy", "candy"],
        "description": "Distribute candies to children with rating-based constraints.",
        "spec": {"verifiable": True},
    },
    "lc136": {
        "name": "Single Number",
        "keywords": ["array", "bit manipulation", "hash"],
        "description": "Find the element that appears only once.",
        "spec": {"verifiable": True},
    },
    "lc137": {
        "name": "Single Number II",
        "keywords": ["array", "bit manipulation"],
        "description": "Find the element that appears once while others appear three times.",
        "spec": {"verifiable": True},
    },
    "lc139": {
        "name": "Word Break",
        "keywords": ["dynamic programming", "string", "dictionary"],
        "description": "Determine if a string can be segmented into dictionary words.",
        "spec": {"verifiable": True},
    },
    "lc152": {
        "name": "Maximum Product Subarray",
        "keywords": ["array", "dynamic programming", "product"],
        "description": "Find the contiguous subarray with the largest product.",
        "spec": {"verifiable": True},
    },
    "lc179": {
        "name": "Largest Number",
        "keywords": ["array", "sorting", "string"],
        "description": "Arrange numbers to form the largest possible number.",
        "spec": {"verifiable": True},
    },
    "lc191": {
        "name": "Number of 1 Bits",
        "keywords": ["bit manipulation", "count"],
        "description": "Count the number of 1 bits in an unsigned integer.",
        "spec": {"verifiable": True},
    },
    "lc198": {
        "name": "House Robber",
        "keywords": ["dynamic programming", "house", "robber"],
        "description": "Find maximum money you can rob without robbing adjacent houses.",
        "spec": {"verifiable": True},
    },
    "lc200": {
        "name": "Number of Islands",
        "keywords": ["DFS", "BFS", "matrix", "island", "grid"],
        "description": "Count the number of islands in a 2D grid.",
        "spec": {"verifiable": True},
    },
    "lc300": {
        "name": "Longest Increasing Subsequence",
        "keywords": ["dynamic programming", "binary search", "subsequence"],
        "description": "Find the length of the longest strictly increasing subsequence.",
        "spec": {"verifiable": True},
    },
    "lc312": {
        "name": "Burst Balloons",
        "keywords": ["dynamic programming", "interval", "balloon"],
        "description": "Find maximum coins from bursting balloons.",
        "spec": {"verifiable": True},
    },
    "lc322": {
        "name": "Coin Change",
        "keywords": ["dynamic programming", "coin", "change", "minimum"],
        "description": "Given coins and an amount, find fewest coins needed to make the amount.",
        "spec": {"verifiable": True},
    },
    "lc337": {
        "name": "House Robber III",
        "keywords": ["dynamic programming", "tree", "house", "robber"],
        "description": "Find maximum money from robbing houses in a binary tree.",
        "spec": {"verifiable": True},
    },
    "lc392": {
        "name": "Is Subsequence",
        "keywords": ["two pointers", "string", "subsequence"],
        "description": "Determine if s is a subsequence of t.",
        "spec": {"verifiable": True},
    },
    "lc416": {
        "name": "Partition Equal Subset Sum",
        "keywords": ["dynamic programming", "partition", "subset"],
        "description": "Determine if array can be partitioned into two subsets with equal sum.",
        "spec": {"verifiable": True},
    },
    "lc424": {
        "name": "Longest Repeating Character Replacement",
        "keywords": ["sliding window", "string", "replacement"],
        "description": "Find longest substring with at most k character replacements.",
        "spec": {"verifiable": True},
    },
    "lc494": {
        "name": "Target Sum",
        "keywords": ["dynamic programming", "backtracking", "target"],
        "description": "Find number of ways to assign +/- to elements to reach target.",
        "spec": {"verifiable": True},
    },
    "lc560": {
        "name": "Subarray Sum Equals K",
        "keywords": ["array", "hash map", "prefix sum"],
        "description": "Find number of contiguous subarrays with sum equal to k.",
        "spec": {"verifiable": True},
    },
    "lc647": {
        "name": "Palindromic Substrings",
        "keywords": ["string", "dynamic programming", "palindrome"],
        "description": "Count all palindromic substrings.",
        "spec": {"verifiable": True},
    },
    "lc739": {
        "name": "Daily Temperatures",
        "keywords": ["array", "stack", "temperature"],
        "description": "For each day, find number of days until warmer temperature.",
        "spec": {"verifiable": True},
    },
    "lc743": {
        "name": "Network Delay Time",
        "keywords": ["graph", "shortest path", "dijkstra", "network"],
        "description": "Find time for all nodes to receive a signal.",
        "spec": {"verifiable": True},
    },
    "lc875": {
        "name": "Koko Eating Bananas",
        "keywords": ["binary search", "array", "eating", "bananas"],
        "description": "Find minimum eating speed to finish bananas within h hours.",
        "spec": {"verifiable": True},
    },
    "lc997": {
        "name": "Find the Town Judge",
        "keywords": ["graph", "town", "judge", "trust"],
        "description": "Find the town judge based on trust relationships.",
        "spec": {"verifiable": True},
    },
    "lc1143": {
        "name": "Longest Common Subsequence",
        "keywords": ["dynamic programming", "string", "subsequence"],
        "description": "Find length of longest common subsequence of two strings.",
        "spec": {"verifiable": True},
    },
    "lc1971": {
        "name": "Find if Path Exists in Graph",
        "keywords": ["graph", "DFS", "BFS", "path"],
        "description": "Determine if a path exists between source and destination.",
        "spec": {"verifiable": True},
    },
    "lc3928": {
        "name": "Arrange Numbers Divisible",
        "keywords": ["array", "arrange", "divisible"],
        "description": "Arrange numbers divisible by k.",
        "spec": {"verifiable": True},
    },
    "merge_intervals": {
        "name": "Merge Intervals",
        "keywords": ["array", "intervals", "merge", "overlap"],
        "description": "Merge all overlapping intervals.",
        "spec": {"verifiable": True},
    },
    "binary_tree_max_path": {
        "name": "Binary Tree Maximum Path Sum",
        "keywords": ["binary tree", "path", "maximum", "sum"],
        "description": "Find the maximum path sum in a binary tree.",
        "spec": {"verifiable": True},
    },
    "reverse_linked_list": {
        "name": "Reverse Linked List",
        "keywords": ["linked list", "reverse", "pointer"],
        "description": "Reverse a singly linked list.",
        "spec": {"verifiable": True},
    },
    "lru_cache": {
        "name": "LRU Cache",
        "keywords": ["cache", "hash", "linked list", "lru"],
        "description": "Design an LRU cache data structure.",
        "spec": {"verifiable": True},
    },
    "median_finder": {
        "name": "Find Median from Data Stream",
        "keywords": ["heap", "median", "stream", "data structure"],
        "description": "Find median of a data stream.",
        "spec": {"verifiable": True},
    },
    "median_two_sorted": {
        "name": "Median of Two Sorted Arrays",
        "keywords": ["array", "binary search", "median", "sorted"],
        "description": "Find median of two sorted arrays.",
        "spec": {"verifiable": True},
    },
    "edit_distance": {
        "name": "Edit Distance",
        "keywords": ["dynamic programming", "string", "edit", "distance", "levenshtein"],
        "description": "Compute minimum edit distance between two strings.",
        "spec": {"verifiable": True},
    },
    "maximal_square": {
        "name": "Maximal Square",
        "keywords": ["dynamic programming", "matrix", "binary", "square"],
        "description": "Find the largest square containing only 1s in a binary matrix.",
        "spec": {"verifiable": True},
    },
}


def get_problem(problem_id: str) -> Optional[Dict[str, Any]]:
    return PROBLEMS.get(problem_id)


def get_problems() -> Dict[str, Dict[str, Any]]:
    return dict(PROBLEMS)


def list_problem_ids() -> list:
    return list(PROBLEMS.keys())

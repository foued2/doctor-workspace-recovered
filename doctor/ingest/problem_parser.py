from __future__ import annotations

import re
from typing import Any, Dict, Optional

_KNOWN_OBJECTIVES = {
    "two_sum": ["two sum", "sum of two", "add two numbers", "find two numbers", "pair that sums", "indices of two numbers"],
    "max_subarray": ["maximum subarray", "max subarray", "contiguous subarray"],
    "climbing_stairs": ["climbing stairs", "climb stairs", "ways to climb", "climb to the top", "distinct ways to climb"],
    "lc322": ["coin change", "minimum coins", "fewest coins", "fewest number of coins"],
    "longest_increasing": ["longest increasing", "longest subsequence", "lis "],
    "number_of_islands": ["number of islands", "count islands", "num islands"],
    "merge_intervals": ["merge intervals", "merge overlapping", "overlapping intervals"],
    "lc121": ["best time to buy", "buy and sell stock", "max profit from stock"],
    "binary_tree_max_path": ["binary tree maximum path", "max path sum"],
    "lc42": ["trapping rain water", "trapped water", "rain water"],
    "lc20": ["valid parentheses", "valid brackets", "balanced parentheses"],
    "reverse_linked_list": ["reverse linked list", "reverse a linked list"],
    "lru_cache": ["lru cache", "least recently used"],
    "median_finder": ["finding median", "median of stream", "median from data stream"],
    "serialize_deserialize": ["serialize and deserialize", "serialize binary tree"],
    "lc139": ["word break", "word dictionary"],
    "median_two_sorted": ["median of two sorted", "median of two arrays"],
    "edit_distance": ["edit distance", "minimum edits", "levenshtein"],
    "maximal_square": ["maximal square", "largest square"],
    "lc416": ["partition equal subset", "equal sum partition"],
    "lc70": ["climbing stairs", "climb stairs", "ways to climb"],
    "lc53": ["maximum subarray", "max subarray", "contiguous subarray"],
    "lc45": ["jump game", "minimum jumps", "fewest jumps"],
    "lc312": ["burst balloons", "burst balloon"],
    "lc560": ["subarray sum equals k", "subarray sum"],
    "lc997": ["town judge", "find the town judge"],
    "lc875": ["koko eating bananas", "eating bananas"],
    "lc743": ["network delay", "signal propagation"],
    "lc79": ["word search", "exist in the grid", "board and a word", "word exists"],
}


def _extract_objective(text: str) -> Optional[str]:
    text_lower = text.lower()
    for objective, keywords in _KNOWN_OBJECTIVES.items():
        for kw in keywords:
            if kw in text_lower:
                return objective
    if re.search(r"\bfind\b|\breturn\b|\bcompute\b|\bcalculate\b", text_lower):
        return "general"
    return None


def _extract_input_type(text: str) -> Optional[str]:
    text_lower = text.lower()
    if "array" in text_lower or "list" in text_lower or "nums" in text_lower:
        return "array"
    if "string" in text_lower or "text" in text_lower:
        return "string"
    if "tree" in text_lower or "node" in text_lower:
        return "tree"
    if "matrix" in text_lower or "grid" in text_lower:
        return "matrix"
    if "integer" in text_lower or "number" in text_lower or "n " in text_lower:
        return "integer"
    return None


def parse_problem(statement: str) -> Dict[str, Any]:
    if not statement or not statement.strip():
        return {
            "objective": None,
            "input_type": None,
            "constraints": [],
            "examples": [],
            "raw_statement": statement or "",
        }

    objective = _extract_objective(statement)
    input_type = _extract_input_type(statement)

    return {
        "objective": objective,
        "input_type": input_type,
        "constraints": [],
        "examples": [],
        "raw_statement": statement,
        "source_statement": statement,
    }


def parse_problem_statement(statement: str) -> Dict[str, Any]:
    return parse_problem(statement)

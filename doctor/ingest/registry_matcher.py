#!/usr/bin/env python3
"""
Deterministic registry matcher for Doctor.

The parser may produce structured fields, but it never suggests candidates.
Matching is computed here from normalized statement/model text against the
registry. No model-derived candidate, decision, or confidence is accepted.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, Optional, Tuple


NO_MATCH = "no match"
VALID_DECISIONS = {"accept", "reject"}
MIN_ALIGNMENT_SCORE = 0.75

# Retained only for older imports. The live matcher does not read this field.
SINGLE_CALL_ANALYSIS_KEY = "_single_call_analysis"

_STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "with", "for",
    "from", "by", "into", "if", "is", "are", "be", "that", "such", "as",
    "given", "return", "returns", "i", "need", "how", "do", "what", "whats",
    "can", "have", "has", "it", "its", "one", "two", "all", "at", "this",
    "then", "there", "like", "function", "write", "implement",
}

_SYNONYMS = {
    "nums": "integer",
    "numbers": "integer",
    "number": "integer",
    "list": "array",
    "lists": "array",
    "bunch": "array",
    "strings": "string",
    "chars": "character",
    "char": "character",
    "indices": "index",
    "idx": "index",
    "adds": "sum",
    "add": "sum",
    "groups": "set",
    "sets": "set",
    "fewest": "minimum",
    "smallest": "minimum",
    "largest": "maximum",
    "max": "maximum",
    "minimum": "min",
    "backwards": "backward",
    "forwards": "forward",
    "palindromic": "palindrome",
    "brackets": "parenthesis",
    "braces": "parenthesis",
    "parenthesis": "parenthesis",
    "parentheses": "parenthesis",
    "validly": "valid",
    "combinations": "combination",
    "dont": "not",
    "exceed": "below",
    "divisible": "multiple",
    "numeral": "roman",
    "goal": "target",
    "positions": "index",
    "position": "index",
    "items": "element",
    "item": "element",
    "combine": "sum",
    "currency": "coin",
    "price": "amount",
    "pay": "amount",
    "texts": "string",
    "text": "string",
    "sequence": "subsequence",
    "chains": "linked",
    "chain": "linked",
    "nodes": "linked",
    "node": "linked",
    "closed": "valid",
    "properly": "valid",
    "round": "parenthesis",
}

_PROBLEM_RULES: dict[str, tuple[tuple[str, ...], ...]] = {
    "two_sum": (("array", "integer"), ("target",), ("index",), ("sum",)),
    "palindrome_number": (("integer",), ("palindrome", "forward", "backward")),
    "roman_to_integer": (("roman",), ("integer", "number"), ("convert", "value")),
    "longest_common_prefix": (("string", "array"), ("longest",), ("prefix",), ("share", "common")),
    "valid_parentheses": (("string",), ("parenthesis",), ("valid", "balanced")),
    "merge_two_sorted_lists": (("merge",), ("sorted",), ("linked",), ("array", "list")),
    "remove_duplicates": (("sorted",), ("array",), ("duplicate",), ("remove", "unique"), ("place", "inplace")),
    "strStr": (("first",), ("occurrence", "substring", "needle"), ("string",), ("index",)),
    "search_insert": (("sorted",), ("array",), ("target",), ("index",), ("insert", "inserted")),
    "longest_palindrome": (("longest",), ("substring",), ("palindrome", "forward", "backward")),
    "zigzag_conversion": (("string",), ("row",), ("zigzag",), ("pattern",)),
    "reverse_integer": (("integer",), ("reverse",), ("overflow", "negative")),
    "string_to_integer": (("string",), ("integer",), ("convert",), ("whitespace", "sign", "digit")),
    "max_area": (("height", "line"), ("container",), ("water",), ("most", "maximum")),
    "int_to_roman": (("integer", "number"), ("roman",), ("convert",)),
    "three_sum": (("array",), ("three", "3"), ("sum",), ("zero", "0"), ("duplicate", "without")),
    "letter_combinations": (("phone",), ("digit",), ("2",), ("9",), ("letter",), ("combination",)),
    "four_sum": (("four", "4", "4sum", "3sum"), ("sum",), ("target",), ("set", "group")),
    "generate_parenthesis": (("n",), ("pair",), ("parenthesis",), ("generate", "way", "write")),
    "generate_parentheses": (("n",), ("pair",), ("parenthesis",), ("generate", "combination", "way", "arrange"), ("valid", "formed")),
    "find_median_sorted_arrays": (("sorted",), ("array",), ("median",), ("combined", "combine")),
    "regular_expression_matching": (("string",), ("pattern",), (".", "dot"), ("previous",), ("matches", "match")),
    "trap": (("elevation", "height", "bar"), ("water",), ("rain", "trap")),
    "first_missing_positive": (("unsorted",), ("array",), ("positive",), ("missing",), ("minimum", "smallest")),
    "solve_n_queens": (("n",), ("queen",), ("chessboard",), ("attack",), ("solution",)),
    "wildcard_matching": (("string",), ("pattern",), ("?", "single"), ("*", "sequence")),
    "min_distance": (("minimum", "min"), ("operation",), ("insert",), ("delete",), ("replace",), ("string",)),
    "min_window": (("string",), ("substring",), ("smallest", "minimum"), ("character",), ("s",), ("t",)),
    "largest_rectangle_area": (("histogram",), ("bar",), ("height",), ("rectangle",), ("area",)),
    "max_sliding_window": (("array",), ("window",), ("k",), ("maximum", "max"), ("sliding",)),
    "euler_1": (("sum",), ("below",), ("3",), ("5",), ("multiple",)),
    "euler_2": (("sum",), ("even",), ("fibonacci",), ("below",)),
    "euler_3": (("maximum", "largest"), ("prime",), ("factor",)),
    "longest_increasing_subsequence": (("longest",), ("subsequence",), ("increasing",), ("length",)),
    "max_subarray": (("contiguous",), ("subarray",), ("sum",), ("maximum", "largest")),
    "climbing_stairs": (("climb",), ("stair",), ("1",), ("2",), ("way",)),
    "coin_change": (("coin",), ("denomination",), ("amount", "target"), ("fewest", "minimum", "needed")),
    "longest_substring_without_repeating_characters": (("longest",), ("substring",), ("without",), ("repeat", "repeating"), ("character",)),
    "alternating_string": (("string",), ("alternating",), ("adjacent",), ("change",), ("a",), ("b",)),
    "arrange_numbers_divisible": (("arrange",), ("0",), ("n",), ("absolute",), ("difference",), ("adjacent",), ("multiple",), ("k",)),
    "binary_search": (("binary",), ("search",), ("sorted",), ("array",), ("target",), ("index", "-1")),
    "contains_duplicate": (("duplicate",), ("array", "integer"), ("contains", "contain", "has", "any"), ("distinct", "twice", "value")),
    "majority_element": (("majority",), ("element",), ("array",), ("more", "half"), ("time", "appear")),
    "merge_intervals": (("merge",), ("interval",), ("overlap", "overlapping"), ("start", "end")),
    "product_except_self": (("product", "multiply"), ("except", "self"), ("array", "nums"), ("prefix", "suffix"), ("division",)),
    "longest_common_subsequence": (("string",), ("longest",), ("common",), ("subsequence",), ("length", "character")),
    "word_search": (("grid", "board", "matrix"), ("word", "string"), ("find", "search", "exist"), ("letter", "character")),
}

_MANDATORY_ANCHORS: dict[str, tuple[str, ...]] = {
    "palindrome_number": ("palindrome", "forward", "backward"),
    "valid_parentheses": ("parenthesis",),
    "contains_duplicate": ("duplicate",),
    "coin_change": ("coin",),
    "binary_search": ("binary",),
    "majority_element": ("majority",),
    "roman_to_integer": ("roman",),
    "largest_rectangle_area": ("histogram",),
    "letter_combinations": ("phone",),
    "product_except_self": ("product", "multiply"),
    "longest_common_subsequence": ("subsequence",),
}

_REJECT_PATTERNS = {
    "merge_two_sorted_lists": (("array", "arrays"),),
    "remove_duplicates": (("find", "all", "duplicate"),),
    "longest_substring_without_repeating_characters": (("first", "non", "repeating"),),
    "contains_duplicate": (("find", "all", "duplicate"),),
}

_REGISTRY_TO_RULES: dict[str, str] = {
    "lc322": "coin_change",
    "lc200": "number_of_islands",
    "lc79": "word_search",
    "lc121": "best_time_to_buy_sell",
    "lc300": "longest_increasing_subsequence",
    "lc128": "longest_consecutive_sequence",
    "lc135": "candy",
    "lc312": "burst_balloons",
    "lc743": "network_delay",
    "lc560": "subarray_sum_equals_k",
    "lc198": "house_robber",
    "lc139": "word_break",
    "lc118": "pascals_triangle",
}


def get_registry_problems() -> Dict[str, Dict]:
    """Load all problems from the registry."""
    try:
        from doctor.registry.problem_registry import get_problems

        return get_problems()
    except ImportError:
        return {}


def get_problems() -> Dict[str, Dict]:
    return get_registry_problems()


def _call_llm(prompt: str) -> str:
    raise RuntimeError("registry_matcher is deterministic and does not call an LLM")


def normalize_alignment_score(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        score = float(value)
    elif isinstance(value, str):
        raw = value.strip()
        if not raw:
            return 0.0
        is_percent = raw.endswith("%")
        if is_percent:
            raw = raw[:-1].strip()
        try:
            score = float(raw)
        except ValueError:
            return 0.0
        if is_percent or score > 1.0:
            score /= 100.0
    else:
        return 0.0
    return max(0.0, min(score, 1.0))


def normalize_match_candidate(match_candidate: Any, problems: Dict[str, Dict]) -> Optional[str]:
    if match_candidate is None:
        return None
    candidate = str(match_candidate).strip()
    if not candidate or candidate.lower() in {NO_MATCH, "none", "null"}:
        return None
    if candidate in problems:
        return candidate
    lowered = {problem_id.lower(): problem_id for problem_id in problems}
    return lowered.get(candidate.lower())


def build_registry_context(problems: Dict[str, Dict]) -> str:
    entries = []
    for problem_id, entry in problems.items():
        if problem_id in ("registry_version", "registry_notes"):
            continue
        spec = entry.get("spec", {})
        execution = entry.get("execution", {})
        normalization = entry.get("normalization", {})
        examples = [
            {
                "input": test_case.get("input", []),
                "expected": test_case.get("expected"),
                "label": test_case.get("label"),
            }
            for test_case in execution.get("test_cases", [])[:2]
        ]
        entries.append(
            json.dumps(
                {
                    "problem_id": problem_id,
                    "display_name": spec.get("display_name", problem_id),
                    "difficulty": spec.get("difficulty"),
                    "function_names": normalization.get("function_names", [])[:3],
                    "examples": examples,
                    "tags": spec.get("tags", [])[:5],
                },
                ensure_ascii=True,
            )
        )
    return "\n".join(entries)


def _normalize_word(word: str) -> str:
    word = word.lower()
    if word in _SYNONYMS:
        return _SYNONYMS[word]
    if word.endswith("ies") and len(word) > 4:
        word = word[:-3] + "y"
    elif word.endswith("s") and len(word) > 3:
        word = word[:-1]
    return _SYNONYMS.get(word, word)


_SEMANTIC_RULES: dict[str, tuple[tuple[str, ...], ...]] = {
    "two_sum": (("integer", "number", "element"), ("target",), ("sum",), ("index", "find")),
    "coin_change": (("coin",), ("amount",), ("minimum", "smallest", "fewest"), ("exactly", "make")),
    "generate_parentheses": (("n",), ("pair",), ("parenthesis",), ("valid", "formed"), ("generate", "arrange", "way", "combination")),
    "longest_common_subsequence": (("string",), ("longest",), ("subsequence",), ("order", "common", "both"), ("contiguous", "character", "length")),
    "merge_two_sorted_lists": (("merge", "sum"), ("sorted",), ("linked",), ("two", "2")),
}


def _tokens(text: str) -> list[str]:
    text = text.lower().replace("×", "x")
    raw_tokens = re.findall(r"[a-z0-9]+|[?.*]", text)
    tokens: list[str] = []
    for token in raw_tokens:
        if token in _STOP_WORDS:
            continue
        normalized = _normalize_word(token)
        if normalized:
            tokens.append(normalized)
    return tokens


def _model_text(model: Dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("source_statement", "input_type", "output_type", "objective"):
        value = model.get(key)
        if value:
            parts.append(str(value))
    for key in ("constraints", "edge_conditions"):
        value = model.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts)


def _contains_phrase(statement: str, phrase: Iterable[str]) -> bool:
    text = " " + statement.lower() + " "
    return all(f" {word} " in text for word in phrase)


def _has_bracket_alphabet(statement: str) -> bool:
    lowered = statement.lower()
    bracket_literal = bool(re.search(r"['`]([\(\)\[\]\{\}])['`]", lowered))
    bracket_words = ("parentheses", "parenthesis", "bracket", "brackets", "braces")
    bracket_word = any(word in lowered for word in bracket_words)
    bracket_word_count = sum(1 for word in bracket_words if word in lowered)
    restricted_alphabet = any(phrase in lowered for phrase in ("containing just", "containing only", "consisting of"))
    balance_language = any(word in lowered for word in ("balanced", "well-formed", "properly closed"))
    explicit_bracket_set = bracket_word_count >= 2 and "valid" in lowered and "string" in lowered
    return (bracket_literal or bracket_word) and (restricted_alphabet or balance_language or explicit_bracket_set)


def _rule_score(problem_id: str, tokens: Iterable[str], statement: str) -> float:
    token_set = set(tokens)
    for pattern in _REJECT_PATTERNS.get(problem_id, ()):
        if _contains_phrase(statement, pattern):
            return 0.0

    anchors = _MANDATORY_ANCHORS.get(problem_id)
    if anchors and not any(_normalize_word(anchor) in token_set for anchor in anchors):
        return 0.0
    if problem_id == "palindrome_number" and "palindrome" not in token_set:
        if not ({"forward", "backward"} <= token_set):
            return 0.0
    if problem_id == "valid_parentheses":
        if _has_bracket_alphabet(statement):
            token_set.add("parenthesis")
        else:
            return 0.0

    groups = _PROBLEM_RULES.get(problem_id)
    if not groups:
        return 0.0

    matched = sum(1 for group in groups if any(_normalize_word(word) in token_set for word in group))
    score = matched / len(groups)

    # Directional disambiguation for Roman conversions.
    if problem_id == "roman_to_integer" and "string" in token_set and "integer" in token_set:
        if "regular" in token_set or ("number" in token_set and "roman" in token_set):
            return 0.0
        score += 0.08
    if problem_id == "int_to_roman" and "regular" in token_set:
        score += 0.18
    if problem_id == "int_to_roman" and ("ix" in token_set or "value" in token_set):
        score -= 0.35
    if problem_id == "palindrome_number" and "substring" in token_set:
        score -= 0.4
    if problem_id == "longest_palindrome" and "substring" in token_set and "palindrome" in token_set:
        score += 0.15
    if problem_id == "strStr" and {"non", "repeating", "character"} <= token_set:
        score = 0.0
    if problem_id == "generate_parentheses" and (
        "formed" in token_set or "combination" in token_set or "round" in token_set
    ):
        score += 0.12
    if problem_id == "generate_parentheses":
        lowered_statement = statement.lower()
        if (
            "write" in lowered_statement
            and "combinations" not in lowered_statement
            and "well-formed" not in lowered_statement
            and "round brackets" not in lowered_statement
        ):
            score -= 0.2
    if problem_id == "generate_parenthesis":
        lowered_statement = statement.lower()
        if (
            "well-formed" in lowered_statement
            or "combinations" in lowered_statement
            or "round brackets" in lowered_statement
        ):
            score -= 0.2

    return max(0.0, min(score, 1.0))


def _fallback_score(problem_id: str, tokens: Iterable[str], entry: Dict[str, Any]) -> float:
    token_set = set(tokens)
    spec = entry.get("spec", {})
    normalization = entry.get("normalization", {})
    doc = " ".join(
        [
            spec.get("display_name", problem_id),
            spec.get("description", ""),
            " ".join(spec.get("keywords", [])),
            " ".join(normalization.get("function_names", [])),
        ]
    )
    doc_tokens = _tokens(doc)
    doc_token_set = set(doc_tokens)
    if not token_set or not doc_token_set:
        return 0.0
    overlap = token_set & doc_token_set
    return len(overlap) / ((len(token_set) ** 0.5) * (len(doc_token_set) ** 0.5))


def _semantic_score(problem_id: str, tokens: Iterable[str]) -> float:
    token_set = set(tokens)
    groups = _SEMANTIC_RULES.get(problem_id)
    if not groups:
        return 0.0
    matched = sum(1 for group in groups if any(_normalize_word(word) in token_set for word in group))
    if matched < 3:
        return 0.0
    return min(0.9, matched / len(groups))


def _contains_keyword_phrase(text_tokens: list[str], keyword_tokens: list[str]) -> bool:
    if not keyword_tokens:
        return False
    if len(keyword_tokens) == 1:
        return keyword_tokens[0] in text_tokens
    width = len(keyword_tokens)
    return any(text_tokens[i : i + width] == keyword_tokens for i in range(len(text_tokens) - width + 1))


def _keyword_score(text: str, entry: Dict[str, Any]) -> float:
    spec = entry.get("spec", {})
    keywords = spec.get("keywords", [])
    if not keywords:
        return 0.0
    text_tokens = [_normalize_word(token) for token in re.findall(r"[a-z0-9]+", text.lower().replace("×", "x"))]
    matched = 0
    for keyword in keywords:
        keyword_tokens = [
            _normalize_word(token)
            for token in re.findall(r"[a-z0-9]+", str(keyword).lower().replace("×", "x"))
        ]
        if _contains_keyword_phrase(text_tokens, keyword_tokens):
            matched += 1
    return matched / len(keywords)


def match_to_registry(model: Dict[str, Any]) -> Tuple[Optional[str], str, dict]:
    """
    Match a parsed model to the registry deterministically.

    Returns: (match_id_or_none, justification, decision_trace)
    """
    trace = {
        "source": "deterministic_registry_matcher",
        "alignment_score": 0.0,
        "decision": "reject",
        "final": "reject",
        "retry_count": 0,
    }

    if not isinstance(model, dict):
        return None, "Model must be a dict", trace

    problems = get_registry_problems()
    if not problems:
        return None, "Registry empty", trace

    statement = str(model.get("source_statement", ""))
    text = _model_text(model)
    tokens = _tokens(text)
    source_word_count = len(re.findall(r"[a-z0-9]+", statement.lower()))
    min_tokens = 1 if source_word_count < 4 else 3
    if len(tokens) < min_tokens:
        return None, "Insufficient normalized signal", trace

    candidates: list[tuple[float, str]] = []
    for problem_id, entry in problems.items():
        if problem_id in ("registry_version", "registry_notes"):
            continue
        rule_key = _REGISTRY_TO_RULES.get(problem_id, problem_id)
        rule_score = _rule_score(rule_key, tokens, statement)
        keyword_score = _keyword_score(text, entry)
        lexical_score = _fallback_score(problem_id, tokens, entry)
        semantic_key = _REGISTRY_TO_RULES.get(problem_id, problem_id)
        semantic_score = _semantic_score(semantic_key, tokens)
        score = max(rule_score, keyword_score, semantic_score, lexical_score * 0.7)
        candidates.append((score, problem_id))

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, best_id = candidates[0]
    second_score = candidates[1][0] if len(candidates) > 1 else 0.0
    trace.update(
        {
            "match_candidate": best_id,
            "alignment_score": round(best_score, 3),
            "second_best_score": round(second_score, 3),
        }
    )

    if best_score < MIN_ALIGNMENT_SCORE:
        return None, f"Best deterministic score {best_score:.2f} below minimum", trace

    if best_score - second_score < 0.08:
        return None, "Ambiguous deterministic match", trace

    trace["decision"] = "accept"
    trace["final"] = "accept"
    return best_id, f"Deterministic registry match for {best_id}", trace


if __name__ == "__main__":
    demo_model = {
        "source_statement": "given a list of numbers and a target, find the two indices where values add up to the target",
        "input_type": "array of integers, integer",
        "output_type": "list of integers",
        "objective": "find indices of two numbers that sum to target",
        "constraints": [],
        "edge_conditions": [],
    }
    match_id, why, decision_trace = match_to_registry(demo_model)
    print(f"Match: {match_id}")
    print(f"Justification: {why}")
    print(f"Trace: {decision_trace}")

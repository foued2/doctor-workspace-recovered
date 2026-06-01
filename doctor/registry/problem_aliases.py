"""Problem aliases — canonical ID resolution and function name matching."""
from __future__ import annotations

import re
from typing import Optional


# Alias map: variant_name -> canonical_id
_ALIASES: dict[str, str] = {
    "twoSum": "two_sum",
    "twosum": "two_sum",
    "two_sum": "two_sum",
    "two-sum": "two_sum",
    "two sum": "two_sum",
    "trapping_rain_water": "lc42",
    "trapping-rain-water": "lc42",
    "trappingrainwater": "lc42",
    "burst_balloons": "lc312",
    "burst-balloons": "lc312",
    "network_delay_time": "lc743",
    "network-delay-time": "lc743",
    "queue_reconstruction_by_height": "lc406",
    "queue-reconstruction-by-height": "lc406",
    "target_sum": "lc494",
    "target-sum": "lc494",
    "koko_eating_bananas": "lc875",
    "koko-eating-bananas": "lc875",
    "gas_station": "lc134",
    "gas-station": "lc134",
    "longest_substring_without_repeating_characters": "lc3",
    "longest-substring-without-repeating-characters": "lc3",
    "longest_substring": "lc3",
    "two_city_scheduling": "lc1029",
    "two-city-scheduling": "lc1029",
}

# Function name aliases per problem
_FUNC_ALIASES: dict[str, list[str]] = {
    "two_sum": ["twoSum", "two_sum", "solve", "solution"],
    "lc42": ["trap", "solution", "solve"],
    "lc312": ["maxCoins", "max_coins", "solution", "solve"],
    "lc743": ["networkDelayTime", "network_delay_time", "solution", "solve"],
    "lc406": ["reconstructQueue", "reconstruct_queue", "solution", "solve"],
    "lc494": ["findTargetSumWays", "find_target_sum_ways", "solution", "solve"],
    "lc875": ["minEatingSpeed", "min_eating_speed", "solution", "solve"],
    "lc134": ["canCompleteCircuit", "can_complete_circuit", "solution", "solve"],
    "lc3": ["lengthOfLongestSubstring", "length_of_longest_substring", "solution", "solve"],
    "lc1029": ["twoCitySchedCost", "two_city_sched_cost", "solution", "solve"],
    "cf607a": ["solve", "solution", "destroy_beacons"],
    "arrange_numbers_divisible": ["arrangeNumbersDivisible", "arrange_numbers_divisible", "solution"],
}


def canonical_problem_id(problem_id: str) -> str:
    """Resolve a variant problem ID to its canonical form."""
    if not problem_id:
        return problem_id
    normalized = problem_id.strip().lower().replace("-", "_").replace(" ", "_")
    return _ALIASES.get(normalized, _ALIASES.get(problem_id, problem_id))


def function_name_aliases(problem_name: str) -> list[str]:
    """Return known function name aliases for a problem."""
    canonical = canonical_problem_id(problem_name)
    return _FUNC_ALIASES.get(canonical, _FUNC_ALIASES.get(problem_name, []))


def equivalent_function_name(name: str, expected: str) -> bool:
    """Check if two function names are equivalent (case-insensitive, underscore-insensitive)."""
    def normalize(s: str) -> str:
        return re.sub(r'[_\s]+', '', s.lower())
    return normalize(name) == normalize(expected)

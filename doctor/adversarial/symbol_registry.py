from __future__ import annotations

import pytest

from doctor.adversarial.symbol_registry import LC11_SYMBOL_REGISTRY, SymbolCategory


BASE_CONTEXT = {
    "height": (1, 8, 6, 2, 5, 4, 8, 3, 7),
    "n": 9,
    "i": 1,
    "j": 8,
    "left_index": 1,
    "right_index": 8,
    "chosen_left": 0,
    "chosen_right": 8,
    "TIE_TRANSITION_POLICY": "advance_left",
    "symmetric_boundaries": True,
    "interior_peak_height": 9,
    "interior_pair_area": 40,
    "boundary_pair_area": 8,
    "fixed_shorter_height": 7,
    "moving_taller_height": 8,
    "area_after_moving_taller": 40,
    "area_before_moving_taller": 49,
    "moved_boundary": "right",
    "taller_boundary": "right",
    "remaining_search_width": 7,
    "previous_width": 8,
    "hidden_partner_index": 6,
    "hidden_partner_effective_height": 8,
    "hidden_width": 5,
    "next_max_area": 49,
    "previous_max_area": 40,
    "wrong_width": 8,
    "early_candidate_area": 49,
    "late_candidate_area": 18,
    "late_candidate_seen_after_early": True,
}


EXPECTED_VALUES = {
    "height": (1, 8, 6, 2, 5, 4, 8, 3, 7),
    "n": 9,
    "i": 1,
    "j": 8,
    "left_index": 1,
    "right_index": 8,
    "chosen_left": 0,
    "chosen_right": 8,
    "TIE_TRANSITION_POLICY": "advance_left",
    "tie_transition_policy": "advance_left",
    "boundary_left_height": 1,
    "boundary_right_height": 7,
    "boundary_heights": (1, 7),
    "symmetric_boundaries": True,
    "interior_peak_height": 9,
    "interior_pair_area": 40,
    "boundary_pair_area": 8,
    "fixed_shorter_height": 7,
    "moving_taller_height": 8,
    "area_after_moving_taller": 40,
    "area_before_moving_taller": 49,
    "moved_boundary": "right",
    "taller_boundary": "right",
    "left_height": 8,
    "right_height": 7,
    "remaining_search_width": 7,
    "previous_width": 8,
    "hidden_partner_index": 6,
    "hidden_partner_height": 8,
    "hidden_width": 5,
    "current_area": 49,
    "hidden_partner_effective_height": 8,
    "hidden_partner_area": 40,
    "candidate_area": 49,
    "chosen_pair_area": 8,
    "next_max_area": 49,
    "previous_max_area": 40,
    "wrong_width": 8,
    "wrong_area": 56,
    "correct_area": 49,
    "early_candidate_area": 49,
    "late_candidate_area": 18,
    "late_candidate_seen_after_early": True,
    "max_width": 8,
    "max_area": 49,
    "global_max_pair_area": 49,
    "optimal_left": 1,
    "optimal_right": 8,
    "optimal_pair_width": 7,
    "optimal_pair_index": (1, 8),
    "left_endpoint_best_area": 8,
    "right_endpoint_best_area": 49,
    "tallest_height": 8,
    "tallest_height_index": 1,
    "search_window_after_single_step": (2, 8),
    "search_window_after_double_step": (2, 7),
}


def test_registry_entries_are_structured():
    assert LC11_SYMBOL_REGISTRY.problem_id == "lc11_container_with_most_water"
    assert len(LC11_SYMBOL_REGISTRY.names) == len(LC11_SYMBOL_REGISTRY.entries)
    assert LC11_SYMBOL_REGISTRY.get("global_max_pair_area").category is SymbolCategory.ORACLE_DEPENDENT


@pytest.mark.parametrize("symbol_name, expected", sorted(EXPECTED_VALUES.items()))
def test_lc11_symbol_callable_concrete_values(symbol_name, expected):
    entry = LC11_SYMBOL_REGISTRY.get(symbol_name)
    assert entry.ambiguity is None
    assert entry.compute(BASE_CONTEXT) == expected


def test_tallest_height_index_concrete_unique_case():
    entry = LC11_SYMBOL_REGISTRY.get("tallest_height_index")
    assert entry.compute({"height": (1, 3, 9, 4)}) == 2


def test_tallest_height_index_uses_policy_on_tie():
    entry = LC11_SYMBOL_REGISTRY.get("tallest_height_index")
    assert entry.compute(BASE_CONTEXT) == 1


def test_every_registry_symbol_has_test_coverage():
    covered = set(EXPECTED_VALUES)
    assert LC11_SYMBOL_REGISTRY.names == covered

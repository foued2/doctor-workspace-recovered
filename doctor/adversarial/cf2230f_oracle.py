from __future__ import annotations

from functools import lru_cache
import json
import random
from pathlib import Path
from typing import Any

from doctor.adversarial.cf2230f_oracle import cf2230f_scores_small


ROOT = Path(__file__).resolve().parents[1]
DUEL_ARTIFACT = ROOT / "data" / "track_d_phase2_cf2230f_oracle_duel.json"
SAMPLE_PARENTS = [1, 1, 3, 3, 1, 2, 1, 2, 8]


def test_cf2230f_conditional_duel_artifact_is_valid() -> None:
    artifact = _load_json(DUEL_ARTIFACT)
    assert artifact["target"] == "CF2230F"
    assert artifact["q_limit"] == 6
    assert artifact["status"] in {
        "passed",
        "aborted_on_sample_disagreement",
        "aborted_on_subset_disagreement",
        "aborted_on_ambiguity",
    }
    assert artifact["forbidden_experiments_run"] is False
    assert artifact["sample_cases_checked"] == 6
    assert artifact["sample_disagreements"] == 0
    if artifact["status"] == "passed":
        assert artifact["deterministic_subset_checked"] == 25
        assert artifact["deterministic_subset_disagreements"] == 0
        assert artifact["first_disagreement"] is None


def test_cf2230f_independent_minimax_agrees_with_existing_oracle_on_artifact_cases() -> None:
    artifact = _load_json(DUEL_ARTIFACT)
    for row in artifact["per_case"]:
        parents = row["parents"]
        assert len(parents) <= 6
        existing = cf2230f_scores_small(parents, max_q=6)
        independent = cf2230f_minimax_independent(parents)
        assert row["existing_oracle_output"] == existing
        assert row["independent_oracle_output"] == independent
        assert row["agreement"] == (existing == independent)


def test_cf2230f_sample_prefix_gate_is_first_and_within_q_limit() -> None:
    artifact = _load_json(DUEL_ARTIFACT)
    sample_rows = artifact["per_case"][: artifact["sample_cases_checked"]]
    assert [row["case_id"] for row in sample_rows] == [
        f"cf2230f_sample_prefix_q{q}" for q in range(1, 7)
    ]
    assert all(row["suite"] == "sample_prefix" for row in sample_rows)
    assert all(row["q"] <= 6 for row in sample_rows)
    assert all(row["agreement"] is True for row in sample_rows)


def test_cf2230f_independent_oracle_rejects_invalid_parent_sequences() -> None:
    for parents in ([0], [1, 3], [1, 1, 4]):
        try:
            cf2230f_minimax_independent(parents)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid parent sequence accepted: {parents!r}")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_cf2230f_duel_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for q in range(1, 7):
        rows.append(
            {
                "case_id": f"cf2230f_sample_prefix_q{q}",
                "suite": "sample_prefix",
                "parents": SAMPLE_PARENTS[:q],
            }
        )
    rows.extend(
        [
            {"case_id": "cf2230f_shape_path_q6", "suite": "deterministic_shape", "parents": [1, 2, 3, 4, 5, 6]},
            {"case_id": "cf2230f_shape_star_q6", "suite": "deterministic_shape", "parents": [1, 1, 1, 1, 1, 1]},
            {"case_id": "cf2230f_shape_balanced_q6", "suite": "deterministic_shape", "parents": [1, 1, 2, 2, 3, 3]},
            {"case_id": "cf2230f_shape_root_repeat_q5", "suite": "deterministic_shape", "parents": [1, 1, 1, 1, 1]},
            {"case_id": "cf2230f_shape_leaf_repeat_q5", "suite": "deterministic_shape", "parents": [1, 2, 3, 4, 5]},
        ]
    )
    rng = random.Random(2230_20260519)
    seen = {tuple(row["parents"]) for row in rows}
    random_index = 1
    while random_index <= 20:
        q = rng.randint(1, 6)
        parents = [rng.randint(1, i) for i in range(1, q + 1)]
        key = tuple(parents)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "case_id": f"cf2230f_random_q_le_6_{random_index:03d}",
                "suite": "deterministic_random",
                "parents": parents,
            }
        )
        random_index += 1
    assert len(rows) == 31
    return rows


def cf2230f_minimax_independent(parents: list[int]) -> list[int]:
    _validate_parent_sequence(parents)
    return [_score_prefix_independent(tuple(parents[:q])) for q in range(1, len(parents) + 1)]


def _validate_parent_sequence(parents: list[int]) -> None:
    if len(parents) > 6:
        raise ValueError("q limit exceeded")
    for i, parent in enumerate(parents, start=1):
        if type(parent) is not int or type(parent) is bool or parent < 1 or parent > i:
            raise ValueError("invalid parent sequence")


def _score_prefix_independent(parents: tuple[int, ...]) -> int:
    n = len(parents) + 1
    neighbors = {node: set() for node in range(n)}
    for child, parent_one in enumerate(parents, start=1):
        parent = parent_one - 1
        neighbors[parent].add(child)
        neighbors[child].add(parent)

    @lru_cache(maxsize=None)
    def play(red: frozenset[int], blue: frozenset[int], chip: int | None, alice_turn: bool) -> int:
        occupied = red | blue
        white = frozenset(node for node in range(n) if node not in occupied)
        if alice_turn:
            if chip is None:
                moves = white
            else:
                moves = frozenset(node for node in neighbors[chip] if node in white)
            if not moves:
                return len(red)
            return max(play(red | frozenset([node]), blue, node, False) for node in moves)

        if not white:
            return len(red)
        return min(play(red, blue | frozenset([node]), chip, True) for node in white)

    return play(frozenset(), frozenset(), None, True)

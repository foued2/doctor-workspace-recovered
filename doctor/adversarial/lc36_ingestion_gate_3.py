"""Runner for LC36 ingestion gate (Valid Sudoku). Evaluates solvers under syntax_only."""
from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc36_ingestion_gate import lc36_ingestion_gate


def lc36_oracle(board: list[list[str]]) -> bool:
    """Standard set-based Sudoku validation."""
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == ".":
                continue
            b = (r // 3) * 3 + (c // 3)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v)
            cols[c].add(v)
            boxes[b].add(v)
    return True


def solver_set_based(board: list[list[str]]) -> bool:
    """Standard set-based validation."""
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == ".":
                continue
            b = (r // 3) * 3 + (c // 3)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v)
            cols[c].add(v)
            boxes[b].add(v)
    return True


def solver_bitmap(board: list[list[str]]) -> bool:
    """Bitmap-based validation."""
    rows = [0] * 9
    cols = [0] * 9
    boxes = [0] * 9
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == ".":
                continue
            bit = 1 << int(v)
            b = (r // 3) * 3 + (c // 3)
            if rows[r] & bit or cols[c] & bit or boxes[b] & bit:
                return False
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
    return True


def solver_always_true(board: list[list[str]]) -> bool:
    return True


def solver_always_false(board: list[list[str]]) -> bool:
    return False


def solver_check_rows_cols_skip_boxes(board: list[list[str]]) -> bool:
    """Checks row and column uniqueness only — skips box validation."""
    for r in range(9):
        seen = set()
        for c in range(9):
            v = board[r][c]
            if v == ".":
                continue
            if v in seen:
                return False
            seen.add(v)
    for c in range(9):
        seen = set()
        for r in range(9):
            v = board[r][c]
            if v == ".":
                continue
            if v in seen:
                return False
            seen.add(v)
    return True


REFERENCE_TESTS: list[dict[str, list[list[str]] | bool]] = [
    {
        "board": [
            ["5", "3", ".", ".", "7", ".", ".", ".", "."],
            ["6", ".", ".", "1", "9", "5", ".", ".", "."],
            [".", "9", "8", ".", ".", ".", ".", "6", "."],
            ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
            ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
            ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
            [".", "6", ".", ".", ".", ".", "2", "8", "."],
            [".", ".", ".", "4", "1", "9", ".", ".", "5"],
            [".", ".", ".", ".", "8", ".", ".", "7", "9"],
        ],
        "expected": True,
    },
    {
        "board": [
            ["8", "3", ".", ".", "7", ".", ".", ".", "."],
            ["6", ".", ".", "1", "9", "5", ".", ".", "."],
            [".", "9", "8", ".", ".", ".", ".", "6", "."],
            ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
            ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
            ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
            [".", "6", ".", ".", ".", ".", "2", "8", "."],
            [".", ".", ".", "4", "1", "9", ".", ".", "5"],
            [".", ".", ".", ".", "8", ".", ".", "7", "9"],
        ],
        "expected": False,
    },
    {"board": [[".", ".", ".", ".", ".", ".", ".", ".", "."] for _ in range(9)], "expected": True},
    # Isolation test 1: row-valid + column-valid + box-INVALID
    {
        "board": [
            ["5", "3", ".", ".", ".", ".", ".", ".", "."],
            [".", "5", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
        ],
        "expected": False,
    },
    # Isolation test 2: row-valid + box-valid + column-INVALID
    {
        "board": [
            ["5", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            ["5", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
        ],
        "expected": False,
    },
    # Isolation test 3: column-valid + box-valid + row-INVALID
    {
        "board": [
            ["5", ".", ".", "5", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", ".", "."],
        ],
        "expected": False,
    },
]


def run_suite(solvers: list[Callable[[list[list[str]]], bool]], label: str) -> dict[str, object]:
    print(f"\n--- {label} ---")
    result = lc36_ingestion_gate(problem={}, solvers=solvers, oracle=lc36_oracle, reference_tests=REFERENCE_TESTS)
    ingest = result["ingest"]
    print(f"  ingest: {ingest}")
    print(f"  reason: {result.get('reason', 'N/A')}")
    metrics = result.get("metrics", {})
    if metrics:
        print(f"  oracle_alignment: {metrics.get('oracle_alignment', 'N/A')}")
        print(f"  avg_stability: {metrics.get('avg_perturbation_stability', 'N/A')}")
    return {"ingest": ingest, "reason": result.get("reason", "N/A")}


def main() -> int:
    print("=" * 60)
    print("LC36 Ingestion Gate — Valid Sudoku")
    print("=" * 60)
    good = run_suite([solver_set_based, solver_bitmap], "Good solvers (should PASS)")
    bad = run_suite([solver_always_true, solver_always_false, solver_check_rows_cols_skip_boxes], "Negative controls (must FAIL)")
    verdict = good["ingest"] is True and bad["ingest"] is False
    print(f"\n{'='*60}")
    print(f"Good solvers ingested: {good['ingest']}")
    print(f"Bad solvers rejected: {not bad['ingest']} (reason: {bad['reason']})")
    print(f"Overall: {'PASS' if verdict else 'FAIL'}")
    print(f"{'='*60}")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""
LC79 Word Search — Brute Force Oracle

Standard backtracking with visited tracking.
Given an m x n board of characters and a word, return True if the word exists on the board.
The word can be constructed from letters of sequentially adjacent cells (horizontally or vertically).
The same cell may not be used more than once.
"""


def lc79_brute_force(board: list[list[str]], word: str) -> bool:
    if not board or not board[0] or not word:
        return False

    rows, cols = len(board), len(board[0])

    def backtrack(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False

        # Mark visited by temporarily changing the cell
        orig = board[r][c]
        board[r][c] = '#'

        # Explore all 4 directions
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            if backtrack(r + dr, c + dc, idx + 1):
                return True

        # Restore cell
        board[r][c] = orig
        return False

    for r in range(rows):
        for c in range(cols):
            if backtrack(r, c, 0):
                return True

    return False

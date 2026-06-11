# F4_003: DP approach (completely wrong for this problem)
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    if len(word) == 0:
        return True
    # BUG: tries to use DP — wrong paradigm for pathfinding
    prev = [[False] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == word[0]:
                prev[r][c] = True
    for k in range(1, len(word)):
        curr = [[False] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == word[k]:
                    for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < rows and 0 <= nc < cols and prev[nr][nc]:
                            curr[r][c] = True  # BUG: allows revisiting cells
        prev = curr
    return any(prev[r][c] for r in range(rows) for c in range(cols))

# F4_001: BFS instead of DFS (loses backtracking state)
from collections import deque
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    for r in range(rows):
        for c in range(cols):
            if board[r][c] != word[0]:
                continue
            queue = deque([(r, c, 0, set())])
            while queue:
                cr, ci, idx, vis = queue.popleft()
                if idx == len(word):
                    return True
                if (cr, ci) in vis:
                    continue
                vis.add((cr, ci))
                for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                    nr, nc = cr+dr, ci+dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if board[nr][nc] == word[idx+1]:
                            queue.append((nr, nc, idx+1, set(vis)))  # BUG: BFS loses path
    return False

# F4_002: Greedy path following (always first matching neighbor)
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False
        board[r][c] = '#'
        for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:  # BUG: greedy, no backtracking
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == word[idx+1]:
                if dfs(nr, nc, idx+1):  # BUG: takes first match, doesn't try others
                    return True
        board[r][c] = word[idx]
        return False
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False

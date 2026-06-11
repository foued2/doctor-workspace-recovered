# F3_008: Wrong boundary — uses len(board[0]) for both dimensions
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows = len(board)
    cols = len(board[0])
    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= cols or c < 0 or c >= cols:  # BUG: cols for rows
            return False
        if board[r][c] != word[idx]:
            return False
        board[r][c] = '#'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            if dfs(r+dr, c+dc, idx+1):
                return True
        board[r][c] = word[idx]
        return False
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False

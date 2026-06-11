# F3_004: Wrong character check — compares to word[idx+1]
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if idx + 1 < len(word) and board[r][c] != word[idx+1]:  # BUG: idx+1
            return False
        board[r][c] = '#'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            if dfs(r+dr, c+dc, idx+1):
                return True
        board[r][c] = word[idx] if idx < len(word) else '#'
        return False
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False

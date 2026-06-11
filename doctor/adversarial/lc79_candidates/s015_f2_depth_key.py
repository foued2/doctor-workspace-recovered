# F2_010: Use depth as visited key instead of position
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    def dfs(r, c, idx, depth):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False
        if depth in visited:  # BUG: uses depth not position
            return False
        visited.add(depth)
        board[r][c] = '#'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            if dfs(r+dr, c+dc, idx+1, depth+1):
                return True
        board[r][c] = word[idx]
        visited.discard(depth)
        return False
    for r in range(rows):
        for c in range(cols):
            visited = set()
            if dfs(r, c, 0, 0):
                return True
    return False

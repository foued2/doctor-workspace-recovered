# F1_variant_002: Backtracking with explicit visited set (no board mutation)
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    def dfs(r, c, idx, visited):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if (r, c) in visited:
            return False
        if board[r][c] != word[idx]:
            return False
        visited.add((r, c))
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            if dfs(r+dr, c+dc, idx+1, visited):
                return True
        visited.remove((r, c))
        return False
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0, set()):
                return True
    return False

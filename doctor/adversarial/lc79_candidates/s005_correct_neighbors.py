# F1_variant_005: Backtracking with generator/yield style
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    def neighbors(r, c):
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc
    def bt(r, c, idx):
        if idx == len(word):
            return True
        if board[r][c] != word[idx]:
            return False
        board[r][c] = None
        for nr, nc in neighbors(r, c):
            if bt(nr, nc, idx+1):
                return True
        board[r][c] = word[idx]
        return False
    for r in range(rows):
        for c in range(cols):
            if bt(r, c, 0):
                return True
    return False

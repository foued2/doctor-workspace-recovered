# F1_variant_003: Backtracking with directions as list of tuples
def solve(board, word):
    if not board or not word:
        return False
    R, C = len(board), len(board[0])
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    def bt(r, c, k):
        if k == len(word):
            return True
        if r < 0 or r >= R or c < 0 or c >= C:
            return False
        if board[r][c] != word[k]:
            return False
        tmp = board[r][c]
        board[r][c] = None
        for dr, dc in dirs:
            if bt(r+dr, c+dc, k+1):
                return True
        board[r][c] = tmp
        return False
    for i in range(R):
        for j in range(C):
            if bt(i, j, 0):
                return True
    return False

# F1_variant_004: Backtracking with early termination on single-char word
def solve(board, word):
    if not word:
        return True
    if not board or not board[0]:
        return False
    m, n = len(board), len(board[0])
    def search(i, j, k):
        if board[i][j] != word[k]:
            return False
        if k == len(word) - 1:
            return True
        ch = board[i][j]
        board[i][j] = '*'
        for di, dj in [(0,1),(1,0),(0,-1),(-1,0)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < m and 0 <= nj < n and board[ni][nj] != '*':
                if search(ni, nj, k + 1):
                    return True
        board[i][j] = ch
        return False
    for i in range(m):
        for j in range(n):
            if search(i, j, 0):
                return True
    return False

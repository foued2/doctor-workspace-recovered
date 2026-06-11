# F4_004: Random walk (nondeterministic, wrong approach)
import random
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    for _ in range(1000):  # BUG: random, not deterministic
        r = random.randint(0, rows-1)
        c = random.randint(0, cols-1)
        if board[r][c] != word[0]:
            continue
        path = [(r, c)]
        visited = {(r, c)}
        idx = 0
        while idx < len(word) - 1:
            cr, cc = path[-1]
            neighbors = []
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                    if board[nr][nc] == word[idx+1]:
                        neighbors.append((nr, nc))
            if not neighbors:
                break
            nxt = random.choice(neighbors)
            path.append(nxt)
            visited.add(nxt)
            idx += 1
        if idx == len(word) - 1:
            return True
    return False

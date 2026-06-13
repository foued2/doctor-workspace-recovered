def coinChange(self, coins: List[int], amount: int) -> int:
        q = deque([(amount,0)])
        visited = set()
        while q:
            cur, n_coins = q.popleft()
            if cur == 0:
                return n_coins
            for c in coins:
                new_cur = cur - c
                if new_cur in visited or new_cur < 0:
                    continue
                q.append((new_cur,n_coins+1))
                visited.add(new_cur)
        return -1

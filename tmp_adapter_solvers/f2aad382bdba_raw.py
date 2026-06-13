class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        q = deque()
        visit = set([0])
        q.append([0,0])
        while q:
            curr,steps = q.popleft()
            if curr == amount:
                return steps
            for coin in coins:
                nxt = curr + coin
                if nxt <= amount and nxt not in visit:
                    q.append((nxt,steps+1))
                    visit.add(nxt)
        return -1

class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        queue = deque()
        queue.append([0,0])
        visited = set()
        while queue:
            current, level = queue.popleft()
            if current == amount:
                return level
            for coin in coins:
                candidate = current+coin
                if candidate <= amount and candidate not in visited:
                    queue.append([candidate, level+1])
                    visited.add(candidate)
        return -1

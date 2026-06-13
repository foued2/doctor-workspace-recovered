"""LC45 — v2 solver population (10 solvers, different strategies)."""
from __future__ import annotations
from collections import deque


def solver_001(nums):
    """BFS shortest path."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    visited = {0}
    queue = deque([(0, 0)])
    
    while queue:
        pos, jumps = queue.popleft()
        for step in range(1, nums[pos] + 1):
            nxt = pos + step
            if nxt >= n - 1:
                return jumps + 1
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, jumps + 1))
    
    return -1


def solver_002(nums):
    """Greedy: always jump to position with max future reach."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    jumps = 0
    pos = 0
    while pos < n - 1:
        if nums[pos] == 0: return -1
        
        best_pos = pos + 1
        best_reach = 0
        for step in range(1, nums[pos] + 1):
            nxt = pos + step
            if nxt >= n - 1:
                return jumps + 1
            reach = nxt + nums[nxt]
            if reach > best_reach:
                best_reach = reach
                best_pos = nxt
        
        pos = best_pos
        jumps += 1
    
    return jumps


def solver_003(nums):
    """Greedy: always jump to farthest position."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    jumps = 0
    pos = 0
    while pos < n - 1:
        if nums[pos] == 0: return -1
        
        farthest = pos + 1
        for step in range(2, nums[pos] + 1):
            nxt = pos + step
            if nxt >= n - 1:
                return jumps + 1
            if nxt > farthest:
                farthest = nxt
        
        pos = farthest
        jumps += 1
    
    return jumps


def solver_004(nums):
    """DP bottom-up."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    dp = [float('inf')] * n
    dp[0] = 0
    
    for i in range(n):
        if dp[i] == float('inf'): continue
        for step in range(1, nums[i] + 1):
            nxt = i + step
            if nxt < n:
                dp[nxt] = min(dp[nxt], dp[i] + 1)
    
    return dp[n - 1] if dp[n - 1] != float('inf') else -1


def solver_005(nums):
    """Greedy with interval coverage."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    jumps = 0
    current_end = 0
    farthest = 0
    
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
            if current_end >= n - 1:
                return jumps
    
    return -1


def solver_006(nums):
    """DFS with memoization."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    memo = {}
    
    def dfs(pos):
        if pos >= n - 1: return 0
        if pos in memo: return memo[pos]
        if nums[pos] == 0: return float('inf')
        
        best = float('inf')
        for step in range(1, nums[pos] + 1):
            best = min(best, 1 + dfs(pos + step))
        
        memo[pos] = best
        return best
    
    result = dfs(0)
    return result if result != float('inf') else -1


def solver_007(nums):
    """BFS with depth limit."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    for depth in range(1, n):
        visited = set()
        queue = deque([(0, 0)])
        
        while queue:
            pos, jumps = queue.popleft()
            if jumps > depth: continue
            
            for step in range(1, nums[pos] + 1):
                nxt = pos + step
                if nxt >= n - 1:
                    return jumps + 1
                if nxt not in visited and jumps + 1 <= depth:
                    visited.add(nxt)
                    queue.append((nxt, jumps + 1))
    
    return -1


def solver_008(nums):
    """Greedy: random tie-breaking."""
    import random
    rng = random.Random(42)
    
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    jumps = 0
    pos = 0
    while pos < n - 1:
        if nums[pos] == 0: return -1
        
        candidates = []
        for step in range(1, nums[pos] + 1):
            nxt = pos + step
            if nxt >= n - 1:
                return jumps + 1
            candidates.append(nxt)
        
        pos = rng.choice(candidates)
        jumps += 1
    
    return jumps


def solver_009(nums):
    """DP with path reconstruction."""
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    dp = [float('inf')] * n
    parent = [-1] * n
    dp[0] = 0
    
    for i in range(n):
        if dp[i] == float('inf'): continue
        for step in range(1, nums[i] + 1):
            nxt = i + step
            if nxt < n and dp[i] + 1 < dp[nxt]:
                dp[nxt] = dp[i] + 1
                parent[nxt] = i
    
    return dp[n - 1] if dp[n - 1] != float('inf') else -1


def solver_010(nums):
    """Bidirectional BFS."""
    from collections import deque
    
    n = len(nums)
    if n <= 1: return 0
    if nums[0] == 0: return -1
    
    forward = {0: 0}
    backward = {n - 1: 0}
    f_queue = deque([0])
    b_queue = deque([n - 1])
    
    for _ in range(n):
        if f_queue:
            pos = f_queue.popleft()
            for step in range(1, nums[pos] + 1):
                nxt = pos + step
                if nxt in backward:
                    return forward[pos] + 1 + backward[nxt]
                if nxt < n and nxt not in forward:
                    forward[nxt] = forward[pos] + 1
                    f_queue.append(nxt)
        
        if b_queue:
            pos = b_queue.popleft()
            for prev in range(max(0, pos - nums[pos]), pos):
                if prev not in backward:
                    backward[prev] = backward[pos] + 1
                    b_queue.append(prev)
                    if prev in forward:
                        return forward[prev] + 1 + backward[prev]
    
    return -1

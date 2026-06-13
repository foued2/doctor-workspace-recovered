from typing import List
import heapq

class Solution:
    def networkDelayTime(self, times: List[List[int]], n: int, k: int) -> int:
        #create adjacency list
        adj_list = [[] for _ in range(n+1)]
        for u, v, w in times:
            adj_list[u].append((v, w))
        
        #initialize distance dictionary for all nodes, set all to infinite except source node
        dist = {node: float('inf') for node in range(1, n+1)}
        dist[k] = 0
        
        #initialize heap to track visited nodes
        heap = [(0, k)]
        
        while heap:
            time, node = heapq.heappop(heap)
            if time > dist[node]:
                continue
            for neighbor, neighbor_time in adj_list[node]:
                new_time = time + neighbor_time
                if new_time < dist[neighbor]:
                    dist[neighbor] = new_time
                    heapq.heappush(heap, (new_time, neighbor))
        
        max_time = max(dist.values())
        return max_time if max_time < float('inf') else -1
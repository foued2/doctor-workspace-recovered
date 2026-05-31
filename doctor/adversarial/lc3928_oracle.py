from __future__ import annotations

import heapq
from typing import Iterable

from doctor.adversarial.lc3928_oracle import INF, lc3928_exact_small, validate_lc3928_input


def lc3928_exact_small_reference(n: int, prices: Iterable[int], roads: Iterable[Iterable[int]]) -> list[int]:
    return lc3928_exact_small(n, prices, roads)


def lc3928_naive_local_price(n: int, prices: Iterable[int], roads: Iterable[Iterable[int]]) -> list[int]:
    n, price_tuple, _road_tuple = validate_lc3928_input(n, prices, roads)
    return list(price_tuple)


def lc3928_single_source_wrong_direction(n: int, prices: Iterable[int], roads: Iterable[Iterable[int]]) -> list[int]:
    n, price_tuple, road_tuple = validate_lc3928_input(n, prices, roads)
    if not price_tuple:
        return []
    cheapest_shop = min(range(n), key=lambda idx: price_tuple[idx])
    dist = _dijkstra(n, road_tuple, cheapest_shop, loaded=False)
    return [
        price_tuple[i] if dist[i] >= INF else min(price_tuple[i], price_tuple[cheapest_shop] + dist[i])
        for i in range(n)
    ]


def lc3928_greedy_nearest_shop(n: int, prices: Iterable[int], roads: Iterable[Iterable[int]]) -> list[int]:
    n, price_tuple, road_tuple = validate_lc3928_input(n, prices, roads)
    answer: list[int] = []
    for start in range(n):
        empty_dist = _dijkstra(n, road_tuple, start, loaded=False)
        nearest = min(range(n), key=lambda idx: (empty_dist[idx], price_tuple[idx]))
        if empty_dist[nearest] >= INF:
            answer.append(price_tuple[start])
        else:
            answer.append(min(price_tuple[start], price_tuple[nearest] + 2 * empty_dist[nearest]))
    return answer


def _dijkstra(n: int, roads: tuple[tuple[int, int, int, int], ...], source: int, *, loaded: bool) -> list[int]:
    adjacency: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for u, v, cost, tax in roads:
        weight = cost * tax if loaded else cost
        adjacency[u].append((v, weight))
        adjacency[v].append((u, weight))
    dist = [INF] * n
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        current, vertex = heapq.heappop(heap)
        if current != dist[vertex]:
            continue
        for nxt, weight in adjacency[vertex]:
            candidate = current + weight
            if candidate < dist[nxt]:
                dist[nxt] = candidate
                heapq.heappush(heap, (candidate, nxt))
    return dist

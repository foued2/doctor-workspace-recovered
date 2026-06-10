"""LC743 Graph Family Generator — produces G1-G5 instances.

Each family targets specific structural properties:
  G1: DAG sparse (acyclic, integer weights [1-20])
  G2: Dense weighted (high edge density ~n²/3, random integer weights)
  G3: Cycle-heavy (strongly connected components, multiple cycles)
  G4: Adversarial relaxation (delayed optimal edge, hub-and-spoke misleading)
  G5: Degenerate (disconnected, single-node, unreachable targets)

Output format per instance:
  {
    "graph_id": "G{family}_{index}",
    "family": "G1|G2|G3|G4|G5",
    "times": list of [u, v, w],
    "n": int,
    "k": int,
    "expected": int (oracle output),
    "note": str
  }
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any


def dijkstra_oracle(times: list[list[int]], n: int, k: int) -> int:
    """Canonical Dijkstra oracle for LC743."""
    graph: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist: dict[int, float] = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap: list[tuple[float, int]] = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)


import heapq


def generate_g1_dag_sparse(
    rng: random.Random, n_instances: int = 5, n_nodes: int = 6
) -> list[dict[str, Any]]:
    """G1: DAG sparse graphs. Acyclic, integer weights [1-20]."""
    instances = []
    for i in range(n_instances):
        edges = []
        for u in range(1, n_nodes):
            for v in range(u + 1, min(u + 4, n_nodes + 1)):
                if rng.random() < 0.5:
                    w = rng.randint(1, 20)
                    edges.append([u, v, w])
        k = rng.randint(1, n_nodes)
        expected = dijkstra_oracle(edges, n_nodes, k)
        instances.append({
            "graph_id": f"G1_{i}",
            "family": "G1",
            "times": edges,
            "n": n_nodes,
            "k": k,
            "expected": expected,
            "note": "DAG sparse, acyclic, weights [1-20]",
        })
    return instances


def generate_g2_dense(
    rng: random.Random, n_instances: int = 5, n_nodes: int = 5
) -> list[dict[str, Any]]:
    """G2: Dense weighted graphs. High edge density ~n²/3."""
    instances = []
    for i in range(n_instances):
        edges = []
        for u in range(1, n_nodes + 1):
            for v in range(1, n_nodes + 1):
                if u != v and rng.random() < 0.4:
                    w = rng.randint(1, 20)
                    edges.append([u, v, w])
        k = rng.randint(1, n_nodes)
        expected = dijkstra_oracle(edges, n_nodes, k)
        instances.append({
            "graph_id": f"G2_{i}",
            "family": "G2",
            "times": edges,
            "n": n_nodes,
            "k": k,
            "expected": expected,
            "note": "Dense weighted, high edge density",
        })
    return instances


def generate_g3_cycle_heavy(
    rng: random.Random, n_instances: int = 5, n_nodes: int = 5
) -> list[dict[str, Any]]:
    """G3: Cycle-heavy graphs. Strongly connected components."""
    instances = []
    for i in range(n_instances):
        edges = []
        for u in range(1, n_nodes + 1):
            v = (u % n_nodes) + 1
            w = rng.randint(1, 10)
            edges.append([u, v, w])
        for _ in range(n_nodes):
            u = rng.randint(1, n_nodes)
            v = rng.randint(1, n_nodes)
            if u != v:
                w = rng.randint(1, 10)
                edges.append([u, v, w])
        k = rng.randint(1, n_nodes)
        expected = dijkstra_oracle(edges, n_nodes, k)
        instances.append({
            "graph_id": f"G3_{i}",
            "family": "G3",
            "times": edges,
            "n": n_nodes,
            "k": k,
            "expected": expected,
            "note": "Cycle-heavy, SCC present",
        })
    return instances


def generate_g4_adversarial(
    rng: random.Random, n_instances: int = 5, n_nodes: int = 6
) -> list[dict[str, Any]]:
    """G4: Adversarial relaxation graphs. Delayed optimal edge activation."""
    instances = []
    for i in range(n_instances):
        edges = []
        for u in range(1, n_nodes):
            w = rng.randint(1, 5)
            edges.append([u, u + 1, w])
        hub = rng.randint(1, n_nodes)
        spoke = rng.randint(1, n_nodes)
        while spoke == hub:
            spoke = rng.randint(1, n_nodes)
        edges.append([hub, spoke, 100])
        edges.append([spoke, hub, 1])
        k = rng.randint(1, n_nodes)
        expected = dijkstra_oracle(edges, n_nodes, k)
        instances.append({
            "graph_id": f"G4_{i}",
            "family": "G4",
            "times": edges,
            "n": n_nodes,
            "k": k,
            "expected": expected,
            "note": "Adversarial relaxation, hub-and-spoke",
        })
    return instances


def generate_g5_degenerate(
    rng: random.Random, n_instances: int = 5
) -> list[dict[str, Any]]:
    """G5: Degenerate graphs. Disconnected, single-node, unreachable."""
    instances = []
    cases = [
        {"n": 1, "k": 1, "times": [], "note": "Single node"},
        {"n": 3, "k": 1, "times": [[1, 2, 1]], "note": "Node 3 unreachable"},
        {"n": 4, "k": 1, "times": [[1, 2, 5], [3, 4, 5]], "note": "Two components"},
        {"n": 2, "k": 1, "times": [], "note": "No edges, 2 nodes"},
        {"n": 5, "k": 3, "times": [[1, 2, 1], [4, 5, 1]], "note": "Source isolated"},
    ]
    for i, case in enumerate(cases[:n_instances]):
        expected = dijkstra_oracle(case["times"], case["n"], case["k"])
        instances.append({
            "graph_id": f"G5_{i}",
            "family": "G5",
            "times": case["times"],
            "n": case["n"],
            "k": case["k"],
            "expected": expected,
            "note": case["note"],
        })
    return instances


def generate_all_families(seed: int = 42) -> list[dict[str, Any]]:
    """Generate all 5 graph families. Returns list of instance dicts."""
    rng = random.Random(seed)
    instances = []
    instances.extend(generate_g1_dag_sparse(rng))
    instances.extend(generate_g2_dense(rng))
    instances.extend(generate_g3_cycle_heavy(rng))
    instances.extend(generate_g4_adversarial(rng))
    instances.extend(generate_g5_degenerate(rng))
    return instances

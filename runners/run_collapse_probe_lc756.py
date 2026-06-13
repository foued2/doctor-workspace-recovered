"""LC756 Collapse Probe — Structural and Behavioral Identifiability Test.

Runs 4 diagnostic layers:
  1. Solver identity collapse test (token overlap, signature overlap)
  2. Behavioral divergence test (output entropy on micro-instances)
  3. Template reuse detection (helper function reuse, control flow skeletons)
  4. Collapse metric (structural_similarity × output_convergence)

Usage:
    python runners/run_collapse_probe_lc756.py
"""
from __future__ import annotations

import ast
import json
import math
import sys
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE, lc743_oracle

# ============================================================================
# Helper: parse solver file and extract function bodies
# ============================================================================

def extract_solvers_from_file(filepath: Path) -> dict[str, str]:
    """Extract function source code from a Python file."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    solvers = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("s") and node.name[1:].isdigit():
            # Get the source lines for this function
            start = node.lineno - 1
            end = node.end_lineno
            lines = source.splitlines()[start:end]
            solvers[node.name] = "\n".join(lines)
    return solvers


def extract_function_bodies(filepath: Path) -> dict[str, str]:
    """Extract just the function body (excluding docstring and signature)."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    bodies = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("s") and node.name[1:].isdigit():
            # Get body lines (skip docstring)
            body_start = node.lineno
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                body_start = node.body[0].end_lineno + 1
            end = node.end_lineno
            lines = source.splitlines()[body_start - 1:end]
            bodies[node.name] = "\n".join(lines)
    return bodies


# ============================================================================
# Layer 1: Solver Identity Collapse Test
# ============================================================================

def tokenize_python(code: str) -> list[str]:
    """Simple Python tokenizer for structural comparison."""
    import re
    # Remove comments and docstrings
    code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
    # Tokenize
    tokens = re.findall(r'\b\w+\b|[^\s\w]', code)
    return tokens


def token_overlap(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Compute normalized token overlap (Jaccard-like)."""
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def compute_pairwise_similarity(solvers: dict[str, str]) -> dict[tuple[str, str], float]:
    """Compute pairwise token overlap for all solver pairs."""
    tokenized = {name: tokenize_python(code) for name, code in solvers.items()}
    similarities = {}
    names = sorted(tokenized.keys())
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            sim = token_overlap(tokenized[name_a], tokenized[name_b])
            similarities[(name_a, name_b)] = sim
    return similarities


def compute_signature_overlap(solvers_a: dict[str, str], solvers_b: dict[str, str]) -> float:
    """Compute function signature overlap between two solver sets."""
    import re
    sigs_a = set()
    sigs_b = set()
    for code in solvers_a.values():
        match = re.search(r'def\s+(\w+)\s*\((.*?)\)', code)
        if match:
            sigs_a.add(match.group(2).strip())
    for code in solvers_b.values():
        match = re.search(r'def\s+(\w+)\s*\((.*?)\)', code)
        if match:
            sigs_b.add(match.group(2).strip())
    if not sigs_a or not sigs_b:
        return 0.0
    return len(sigs_a & sigs_b) / len(sigs_a | sigs_b)


# ============================================================================
# Layer 2: Behavioral Divergence Test
# ============================================================================

def generate_micro_instances(n_instances: int = 20) -> list[dict]:
    """Generate small LC743 instances for behavioral testing."""
    instances = []
    rng = __import__("random").Random(42)

    # Connected graphs
    for i in range(8):
        n = rng.randint(2, 5)
        k = rng.randint(1, n)
        edges = []
        for _ in range(rng.randint(n - 1, min(n * (n - 1), 10))):
            u = rng.randint(1, n)
            v = rng.randint(1, n)
            if u != v:
                w = rng.randint(1, 10)
                edges.append([u, v, w])
        if edges:
            expected = lc743_oracle(edges, n, k)
            instances.append({"times": edges, "n": n, "k": k, "expected": expected, "connected": True})

    # Disconnected graphs
    for i in range(8):
        n = rng.randint(3, 6)
        k = rng.randint(1, n)
        edges = []
        # Only connect first half of nodes
        for u in range(1, n // 2):
            v = u + 1
            w = rng.randint(1, 5)
            edges.append([u, v, w])
        if edges:
            expected = lc743_oracle(edges, n, k)
            instances.append({"times": edges, "n": n, "k": k, "expected": expected, "connected": False})

    # Single edge graphs
    for i in range(4):
        n = rng.randint(2, 4)
        k = 1
        v = rng.randint(2, n)
        w = rng.randint(1, 10)
        edges = [[k, v, w]]
        expected = lc743_oracle(edges, n, k)
        instances.append({"times": edges, "n": n, "k": k, "expected": expected, "connected": v == n})

    return instances[:n_instances]


def run_solvers_on_instances(solvers: dict[str, callable], instances: list[dict]) -> dict[str, list]:
    """Run all solvers on all instances, return outputs."""
    outputs = {}
    for name, fn in solvers.items():
        solver_outputs = []
        for inst in instances:
            try:
                result = fn(inst["times"], inst["n"], inst["k"])
            except Exception:
                result = None
            solver_outputs.append(result)
        outputs[name] = solver_outputs
    return outputs


def compute_output_entropy(outputs: dict[str, list]) -> dict[str, float]:
    """Compute output entropy per instance across solvers."""
    n_instances = len(next(iter(outputs.values())))
    entropies = []
    for i in range(n_instances):
        instance_outputs = [outputs[name][i] for name in outputs]
        counter = Counter(instance_outputs)
        total = len(instance_outputs)
        entropy = 0.0
        for count in counter.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        entropies.append(entropy)
    return entropies


def compute_output_clustering(outputs: dict[str, list]) -> float:
    """Compute average pairwise output agreement across instances."""
    names = sorted(outputs.keys())
    n_instances = len(next(iter(outputs.values())))
    agreements = []
    for i in range(n_instances):
        instance_outputs = [outputs[name][i] for name in names]
        counter = Counter(instance_outputs)
        max_count = max(counter.values())
        agreements.append(max_count / len(names))
    return sum(agreements) / len(agreements) if agreements else 0.0


# ============================================================================
# Layer 3: Template Reuse Detection
# ============================================================================

def extract_helper_patterns(code: str) -> set[str]:
    """Extract common helper function patterns from solver code."""
    patterns = set()
    # Look for common graph construction patterns
    if "defaultdict(list)" in code:
        patterns.add("defaultdict_list")
    if "heapq" in code:
        patterns.add("heapq")
    if "deque" in code:
        patterns.add("deque")
    if "float(\"inf\")" in code or "float('inf')" in code:
        patterns.add("inf_init")
    if "while heap:" in code or "while stack:" in code:
        patterns.add("while_heap")
    if "heappop" in code:
        patterns.add("heappop")
    if "heappush" in code:
        patterns.add("heappush")
    if "for v, w in graph" in code:
        patterns.add("for_v_w_graph")
    if "dist[node] == INF" in code:
        patterns.add("dist_inf_check")
    if "max_dist" in code:
        patterns.add("max_dist_var")
    return patterns


def detect_control_flow_skeletons(solvers: dict[str, str]) -> dict[str, set[str]]:
    """Detect common control flow skeletons across solvers."""
    skeletons = {}
    for name, code in solvers.items():
        skeleton = set()
        # Check for Dijkstra-like structure
        if "heapq" in code and "heappop" in code and "heappush" in code:
            skeleton.add("dijkstra_like")
        # Check for BFS-like structure
        if "deque" in code and "popleft" in code:
            skeleton.add("bfs_like")
        # Check for DFS-like structure
        if "stack" in code and "pop()" in code:
            skeleton.add("dfs_like")
        # Check for relaxation loop
        if "nd < dist[v]" in code or "nd < dist[v]:" in code:
            skeleton.add("relaxation")
        # Check for graph construction
        if "graph[u].append" in code:
            skeleton.add("graph_build")
        skeletons[name] = skeleton
    return skeletons


# ============================================================================
# Layer 4: Collapse Metric
# ============================================================================

def compute_collapse_score(structural_sim: float, output_convergence: float) -> float:
    """Compute collapse_score = structural_similarity × output_convergence."""
    return structural_sim * output_convergence


# ============================================================================
# Main diagnostic
# ============================================================================

def import_solvers_from_file(filepath: Path) -> dict[str, callable]:
    """Dynamically import solver functions from a file."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("solvers", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    solvers = {}
    for name in dir(module):
        if name.startswith("s") and name[1:].isdigit():
            fn = getattr(module, name)
            if callable(fn):
                solvers[name] = fn
    return solvers


def main():
    print("=" * 70)
    print("LC756 COLLAPSE PROBE — Structural and Behavioral Identifiability")
    print("=" * 70)

    # Paths
    lc743_path = ROOT / "doctor" / "solvers" / "lc_743_solvers.py"
    lc756_path = ROOT / "doctor" / "solvers" / "lc756" / "lc_756_solvers.py"

    # Extract solver source code
    print("\n[1] Extracting solver source code...")
    lc743_solvers_src = extract_solvers_from_file(lc743_path)
    lc756_solvers_src = extract_solvers_from_file(lc756_path)
    print(f"    LC743: {len(lc743_solvers_src)} solvers")
    print(f"    LC756: {len(lc756_solvers_src)} solvers")

    # Layer 1: Structural similarity
    print("\n" + "=" * 70)
    print("LAYER 1: Solver Identity Collapse Test")
    print("=" * 70)

    # Pairwise similarity within LC756
    lc756_pairwise = compute_pairwise_similarity(lc756_solvers_src)
    sims = list(lc756_pairwise.values())
    avg_sim = sum(sims) / len(sims) if sims else 0
    max_sim = max(sims) if sims else 0
    min_sim = min(sims) if sims else 0

    print(f"\n  LC756 pairwise token overlap (within population):")
    print(f"    Average: {avg_sim:.4f}")
    print(f"    Max:     {max_sim:.4f}")
    print(f"    Min:     {min_sim:.4f}")

    # Find most similar pairs
    sorted_pairs = sorted(lc756_pairwise.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  Most similar pairs:")
    for (a, b), sim in sorted_pairs[:5]:
        print(f"    {a} <-> {b}: {sim:.4f}")

    # Cross-population similarity (LC743 vs LC756)
    cross_sims = []
    for name_a, code_a in lc743_solvers_src.items():
        tokens_a = tokenize_python(code_a)
        for name_b, code_b in lc756_solvers_src.items():
            tokens_b = tokenize_python(code_b)
            sim = token_overlap(tokens_a, tokens_b)
            cross_sims.append(sim)
    avg_cross = sum(cross_sims) / len(cross_sims) if cross_sims else 0

    print(f"\n  Cross-population similarity (LC743 vs LC756):")
    print(f"    Average: {avg_cross:.4f}")

    # Signature overlap
    sig_overlap = compute_signature_overlap(lc743_solvers_src, lc756_solvers_src)
    print(f"\n  Function signature overlap:")
    print(f"    {sig_overlap:.4f}")

    # Layer 2: Behavioral divergence
    print("\n" + "=" * 70)
    print("LAYER 2: Behavioral Divergence Test")
    print("=" * 70)

    # Import solvers for execution
    lc743_solvers_fn = import_solvers_from_file(lc743_path)
    lc756_solvers_fn = import_solvers_from_file(lc756_path)

    # Generate micro-instances
    instances = generate_micro_instances(20)
    print(f"\n  Generated {len(instances)} micro-instances")

    # Run solvers
    lc743_outputs = run_solvers_on_instances(lc743_solvers_fn, instances)
    lc756_outputs = run_solvers_on_instances(lc756_solvers_fn, instances)

    # Compute output entropy
    lc743_entropy = compute_output_entropy(lc743_outputs)
    lc756_entropy = compute_output_entropy(lc756_outputs)

    avg_lc743_entropy = sum(lc743_entropy) / len(lc743_entropy) if lc743_entropy else 0
    avg_lc756_entropy = sum(lc756_entropy) / len(lc756_entropy) if lc756_entropy else 0

    print(f"\n  Output entropy per instance (across solvers):")
    print(f"    LC743 average: {avg_lc743_entropy:.4f} bits")
    print(f"    LC756 average: {avg_lc756_entropy:.4f} bits")

    # Compute output clustering
    lc743_cluster = compute_output_clustering(lc743_outputs)
    lc756_cluster = compute_output_clustering(lc756_outputs)

    print(f"\n  Output clustering (avg max-agreement per instance):")
    print(f"    LC743: {lc743_cluster:.4f}")
    print(f"    LC756: {lc756_cluster:.4f}")

    # Layer 3: Template reuse
    print("\n" + "=" * 70)
    print("LAYER 3: Template Reuse Detection")
    print("=" * 70)

    lc743_patterns = defaultdict(set)
    lc756_patterns = defaultdict(set)

    for name, code in lc743_solvers_src.items():
        lc743_patterns[name] = extract_helper_patterns(code)

    for name, code in lc756_solvers_src.items():
        lc756_patterns[name] = extract_helper_patterns(code)

    # Count pattern frequency
    lc743_pattern_counts = Counter()
    lc756_pattern_counts = Counter()

    for patterns in lc743_patterns.values():
        for p in patterns:
            lc743_pattern_counts[p] += 1

    for patterns in lc756_patterns.values():
        for p in patterns:
            lc756_pattern_counts[p] += 1

    print(f"\n  Helper pattern frequency (LC743):")
    for pattern, count in lc743_pattern_counts.most_common():
        print(f"    {pattern}: {count}/30")

    print(f"\n  Helper pattern frequency (LC756):")
    for pattern, count in lc756_pattern_counts.most_common():
        print(f"    {pattern}: {count}/30")

    # Control flow skeletons
    lc743_skeletons = detect_control_flow_skeletons(lc743_solvers_src)
    lc756_skeletons = detect_control_flow_skeletons(lc756_solvers_src)

    lc743_skeleton_counts = Counter()
    lc756_skeleton_counts = Counter()

    for skeletons in lc743_skeletons.values():
        for s in skeletons:
            lc743_skeleton_counts[s] += 1

    for skeletons in lc756_skeletons.values():
        for s in skeletons:
            lc756_skeleton_counts[s] += 1

    print(f"\n  Control flow skeleton frequency (LC743):")
    for skeleton, count in lc743_skeleton_counts.most_common():
        print(f"    {skeleton}: {count}/30")

    print(f"\n  Control flow skeleton frequency (LC756):")
    for skeleton, count in lc756_skeleton_counts.most_common():
        print(f"    {skeleton}: {count}/30")

    # Layer 4: Collapse metric
    print("\n" + "=" * 70)
    print("LAYER 4: Collapse Metric")
    print("=" * 70)

    # Compute structural similarity (average pairwise within LC756)
    structural_sim = avg_sim

    # Compute output convergence (1 - average entropy / max possible entropy)
    max_entropy = math.log2(30)  # 30 solvers
    output_convergence = 1 - (avg_lc756_entropy / max_entropy) if max_entropy > 0 else 0

    collapse_score = compute_collapse_score(structural_sim, output_convergence)

    print(f"\n  Structural similarity (avg pairwise token overlap): {structural_sim:.4f}")
    print(f"  Output convergence (1 - norm_entropy):             {output_convergence:.4f}")
    print(f"  Collapse score (struct × output):                  {collapse_score:.4f}")

    # Interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)

    if collapse_score > 0.5:
        regime = "HIGH COLLAPSE — system is effectively single-solver in disguise"
    elif structural_sim > 0.7 and output_convergence < 0.3:
        regime = "ORACLE-DRIVEN CHAOS — high structure + high divergence"
    elif structural_sim < 0.3 and output_convergence < 0.3:
        regime = "NOISE / BROKEN GENERATION — low structure + low divergence"
    else:
        regime = "MEANINGFUL DIVERSITY — low structure + high divergence"

    print(f"\n  Regime: {regime}")

    if avg_cross > avg_sim * 0.8:
        print(f"\n  WARNING: Cross-population similarity ({avg_cross:.4f}) is within 80%")
        print(f"           of within-population similarity ({avg_sim:.4f}).")
        print(f"           LC756 may not be structurally distinct from LC743.")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n  collapse_score = {collapse_score:.4f}")
    print(f"  structural_sim = {structural_sim:.4f}")
    print(f"  output_convergence = {output_convergence:.4f}")
    print(f"  cross_population_sim = {avg_cross:.4f}")
    print(f"  verdict: {'COLLAPSED' if collapse_score > 0.5 else 'DISTINCT'}")

    # Write results
    results = {
        "layer1_structural": {
            "avg_pairwise_similarity": avg_sim,
            "max_pairwise_similarity": max_sim,
            "min_pairwise_similarity": min_sim,
            "cross_population_similarity": avg_cross,
            "signature_overlap": sig_overlap,
        },
        "layer2_behavioral": {
            "avg_entropy_lc743": avg_lc743_entropy,
            "avg_entropy_lc756": avg_lc756_entropy,
            "clustering_lc743": lc743_cluster,
            "clustering_lc756": lc756_cluster,
        },
        "layer3_template": {
            "lc743_patterns": dict(lc743_pattern_counts),
            "lc756_patterns": dict(lc756_pattern_counts),
            "lc743_skeletons": dict(lc743_skeleton_counts),
            "lc756_skeletons": dict(lc756_skeleton_counts),
        },
        "layer4_collapse": {
            "structural_similarity": structural_sim,
            "output_convergence": output_convergence,
            "collapse_score": collapse_score,
            "regime": regime,
        },
    }

    out_path = ROOT / "results" / "lc756_collapse_probe.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n  Written -> {out_path}")


if __name__ == "__main__":
    main()

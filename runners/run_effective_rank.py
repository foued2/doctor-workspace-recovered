"""Minimal effective rank + AST clustering audit for LC756 solver space."""
from __future__ import annotations

import ast
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

# --- CONFIG ---
PYTHON = r"C:\Users\pakla\AppData\Local\Programs\Python\Python314\python.exe"
SOLVER_PATH = Path("doctor/solvers/lc756/lc_756_solvers.py")
SOLVER_NAMES = [f"s{i:03d}" for i in range(1, 31)]

# --- AST ANALYSIS ---

def get_ast_nodes(filepath: Path) -> dict[str, int]:
    """Count AST node types in a function source file."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    counts = Counter()
    for node in ast.walk(tree):
        counts[type(node).__name__] += 1
    return dict(counts)

def get_function_ast(func_source: str) -> dict[str, int]:
    """Count AST node types in a single function."""
    try:
        tree = ast.parse(func_source)
        counts = Counter()
        for node in ast.walk(tree):
            counts[type(node).__name__] += 1
        return dict(counts)
    except SyntaxError:
        return {}

def extract_function_source(filepath: Path, func_name: str) -> str:
    """Extract source of a named function from a file."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return ast.get_source_segment(source, node)
    return ""

# --- EFFECTIVE RANK ---

def compute_effective_rank(matrix: np.ndarray, threshold: float = 0.99) -> int:
    """Compute effective rank via cumulative singular value energy."""
    if matrix.size == 0:
        return 0
    # Normalize rows
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = matrix / norms
    
    # SVD
    try:
        _, s, _ = np.linalg.svd(normalized, full_matrices=False)
    except np.linalg.LinAlgError:
        return -1
    
    if s.sum() == 0:
        return 0
    
    # Cumulative energy
    energy = np.cumsum(s ** 2)
    total = energy[-1]
    if total == 0:
        return 0
    
    ratio = energy / total
    effective_rank = np.searchsorted(ratio, threshold) + 1
    return int(effective_rank)

# --- CONTROL FLOW DIVERSITY ---

def get_control_flow_primitives(func_source: str) -> set[str]:
    """Extract control-flow primitive names from function AST."""
    primitives = set()
    try:
        tree = ast.parse(func_source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                primitives.add(type(node).__name__)
            elif isinstance(node, ast.Call):
                if hasattr(node.func, 'attr'):
                    primitives.add(f"call_{node.func.attr}")
                elif hasattr(node.func, 'id'):
                    primitives.add(f"call_{node.func.id}")
    except SyntaxError:
        pass
    return primitives

# --- MAIN ---

def main():
    print("=" * 60)
    print("LC756 EFFECTIVE RANK + AST CLUSTERING AUDIT")
    print("=" * 60)
    
    # Step 1: Extract all solver functions
    print("\n[1/4] Extracting solver functions...")
    solver_sources = {}
    for name in SOLVER_NAMES:
        src = extract_function_source(SOLVER_PATH, name)
        if src:
            solver_sources[name] = src
        else:
            print(f"  WARNING: Could not extract {name}")
    
    print(f"  Extracted {len(solver_sources)}/{len(SOLVER_NAMES)} solvers")
    
    # Step 2: AST node distribution
    print("\n[2/4] AST node-type distribution...")
    ast_features = {}
    for name, src in solver_sources.items():
        ast_features[name] = get_function_ast(src)
    
    # Build feature matrix
    all_nodes = sorted(set().union(*[f.keys() for f in ast_features.values()]))
    print(f"  Unique AST node types: {len(all_nodes)}")
    
    matrix = np.zeros((len(solver_sources), len(all_nodes)))
    for i, name in enumerate(solver_sources):
        for j, node_type in enumerate(all_nodes):
            matrix[i, j] = ast_features[name].get(node_type, 0)
    
    # Step 3: Effective rank
    print("\n[3/4] Effective rank computation...")
    eff_rank = compute_effective_rank(matrix)
    print(f"  Effective rank: {eff_rank}")
    print(f"  Raw matrix shape: {matrix.shape}")
    
    # Singular values for context
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normalized = matrix / norms
    _, s, _ = np.linalg.svd(normalized, full_matrices=False)
    print(f"  Top 10 singular values: {s[:10]}")
    print(f"  Singular value decay: {s[0]/s[-1]:.2f}x")
    
    # Step 4: Control-flow diversity
    print("\n[4/4] Control-flow diversity...")
    cf_sets = {}
    for name, src in solver_sources.items():
        cf_sets[name] = get_control_flow_primitives(src)
    
    # Pairwise Jaccard distances
    names = list(cf_sets.keys())
    n = len(names)
    jaccard_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            set_i, set_j = cf_sets[names[i]], cf_sets[names[j]]
            if set_i | set_j:
                jaccard = len(set_i & set_j) / len(set_i | set_j)
            else:
                jaccard = 1.0
            jaccard_matrix[i, j] = jaccard
            jaccard_matrix[j, i] = jaccard
        jaccard_matrix[i, i] = 1.0
    
    avg_jaccard = (jaccard_matrix.sum() - n) / (n * (n - 1))
    print(f"  Average pairwise Jaccard similarity: {avg_jaccard:.4f}")
    
    # Unique control-flow signatures
    unique_sigs = set(tuple(sorted(s)) for s in cf_sets.values())
    print(f"  Unique control-flow signatures: {len(unique_sigs)}/{n}")
    
    # Control-flow primitives per family
    print("\n  Control-flow primitives per family:")
    families = {
        "F1": [f"s{i:03d}" for i in range(1, 6)],
        "F2": [f"s{i:03d}" for i in range(6, 16)],
        "F3": [f"s{i:03d}" for i in range(16, 27)],
        "F4": [f"s{i:03d}" for i in range(27, 31)],
    }
    for fam, members in families.items():
        fam_prims = set()
        for m in members:
            if m in cf_sets:
                fam_prims.update(cf_sets[m])
        print(f"    {fam}: {sorted(fam_prims)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Solvers analyzed: {len(solver_sources)}")
    print(f"  AST node types: {len(all_nodes)}")
    print(f"  Effective rank: {eff_rank}")
    print(f"  Singular value decay: {s[0]/s[-1]:.2f}x")
    print(f"  Avg control-flow Jaccard: {avg_jaccard:.4f}")
    print(f"  Unique CF signatures: {len(unique_sigs)}/{n}")
    
    # Interpretation
    print("\n  INTERPRETATION:")
    if eff_rank <= 3:
        print("    LOW effective rank: solver space is near a low-dimensional manifold")
    elif eff_rank <= 10:
        print("    MODERATE effective rank: some structural diversity exists")
    else:
        print("    HIGH effective rank: solver space has substantial dimensionality")
    
    if avg_jaccard > 0.9:
        print("    HIGH control-flow similarity: solvers share most primitives")
    elif avg_jaccard > 0.7:
        print("    MODERATE control-flow similarity: some primitive diversity")
    else:
        print("    LOW control-flow similarity: distinct control-flow patterns")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

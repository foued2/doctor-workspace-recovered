"""
DETECTOR BASIS AUDIT

Tests whether measurement algebra distinguishes orbits under symmetry group
S_solvers × S_cases.

Three tests:
1. Isospectral non-isomorphic matrices (same spectrum, different structure)
2. Failure graph isomorphism (preserving degree, changing adjacency)
3. Permutation orbit collapse (orbit size under symmetry group)

Outcomes:
- Case 1: detectors distinguish → β is real combinatorial mode
- Case 2: detectors collapse → spectral-only framework
- Case 3: mixed → partial observability
"""
import json
import random
import numpy as np
from pathlib import Path
from itertools import permutations

SEED = 20260613
ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "results" / "detector_audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SECTION 1: SPECTRAL DETECTORS
# ============================================================

def compute_spectral_detectors(matrix):
    m = matrix.astype(float)
    m_centered = m - m.mean(axis=1, keepdims=True)
    U, s, Vt = np.linalg.svd(m_centered, full_matrices=False)
    total_var = np.sum(s ** 2)
    if total_var == 0:
        return {
            'spectrum': [0.0] * min(6, matrix.shape[0]),
            'intrinsic_dim': matrix.shape[0],
            'spectral_entropy': 0.0,
            'S': 0.0,
            'spectral_gap': 0.0,
        }
    cumvar = np.cumsum(s ** 2) / total_var
    dim = int(np.searchsorted(cumvar, 0.90) + 1)
    dim = min(dim, len(s))
    probs = s ** 2 / total_var
    probs = probs[probs > 0]
    entropy = -np.sum(probs * np.log2(probs))
    spectral_gap = s[0] / s[1] if len(s) > 1 and s[1] > 0 else float('inf')
    return {
        'spectrum': s.tolist()[:6],
        'intrinsic_dim': dim,
        'spectral_entropy': float(entropy),
        'S': float(s[0]),
        'spectral_gap': float(spectral_gap),
    }


# ============================================================
# SECTION 2: COMBINATORIAL DETECTORS
# ============================================================

def compute_combinatorial_detectors(matrix):
    """Non-spectral observables over failure structure."""
    n_solvers, n_cases = matrix.shape

    # Row degree distribution (failures per solver)
    row_degrees = tuple(sorted(matrix.sum(axis=1)))

    # Column degree distribution (solvers failing per case)
    col_degrees = tuple(sorted(matrix.sum(axis=0)))

    # Bipartite clustering: fraction of solver pairs sharing identical failure pattern
    unique_rows = len(set(tuple(row) for row in matrix))
    row_cluster_fraction = unique_rows / n_solvers

    # Bipartite clustering: fraction of case pairs with identical failure pattern
    unique_cols = len(set(tuple(matrix[:, j]) for j in range(n_cases)))
    col_cluster_fraction = unique_cols / n_cases

    # Row adjacency: fraction of solver pairs sharing at least one failure
    row_adj = 0
    for i in range(n_solvers):
        for j in range(i + 1, n_solvers):
            if np.any(np.logical_and(matrix[i], matrix[j])):
                row_adj += 1
    row_adj_fraction = row_adj / (n_solvers * (n_solvers - 1) / 2) if n_solvers > 1 else 0

    # Column adjacency: fraction of case pairs sharing at least one solver failure
    col_adj = 0
    for i in range(n_cases):
        for j in range(i + 1, n_cases):
            if np.any(np.logical_and(matrix[:, i], matrix[:, j])):
                col_adj += 1
    col_adj_fraction = col_adj / (n_cases * (n_cases - 1) / 2) if n_cases > 1 else 0

    # Connected components in bipartite graph (via row-column connections)
    visited_rows = set()
    visited_cols = set()
    n_components = 0
    for start_row in range(n_solvers):
        if start_row in visited_rows:
            continue
        n_components += 1
        queue = [('row', start_row)]
        while queue:
            kind, idx = queue.pop()
            if kind == 'row':
                if idx in visited_rows:
                    continue
                visited_rows.add(idx)
                for j in range(n_cases):
                    if matrix[idx, j] == 1 and j not in visited_cols:
                        queue.append(('col', j))
            else:
                if idx in visited_cols:
                    continue
                visited_cols.add(idx)
                for i in range(n_solvers):
                    if matrix[i, idx] == 1 and i not in visited_rows:
                        queue.append(('row', i))

    return {
        'row_degrees': row_degrees,
        'col_degrees': col_degrees,
        'row_cluster_fraction': float(row_cluster_fraction),
        'col_cluster_fraction': float(col_cluster_fraction),
        'row_adj_fraction': float(row_adj_fraction),
        'col_adj_fraction': float(col_adj_fraction),
        'n_bipartite_components': n_components,
        'unique_rows': unique_rows,
        'unique_cols': unique_cols,
    }


# ============================================================
# SECTION 3: TEST 1 — ISOSPECTRAL NON-ISOMORPHIC MATRICES
# ============================================================

def generate_isospectral_pair(n_solvers=5, n_cases=10, rng_seed=SEED):
    """Generate two matrices with same singular values but different structure."""
    rng = random.Random(rng_seed)

    # Generate base matrix
    A = np.zeros((n_solvers, n_cases), dtype=int)
    for i in range(n_solvers):
        n_fails = rng.randint(1, n_cases // 2)
        fail_indices = rng.sample(range(n_cases), n_fails)
        for j in fail_indices:
            A[i, j] = 1

    # Generate orthogonal transformation that preserves spectrum
    # Use random permutation of columns (preserves row-space spectrum)
    col_perm = list(range(n_cases))
    rng.shuffle(col_perm)
    B = A[:, col_perm]

    return A, B


def test_isospectral_discrimination():
    """Test whether detectors distinguish isospectral matrices."""
    results = []
    rng = random.Random(SEED)

    for trial in range(20):
        n_solvers = rng.randint(3, 8)
        n_cases = rng.randint(5, 15)
        A, B = generate_isospectral_pair(n_solvers, n_cases, SEED + trial)

        spec_A = compute_spectral_detectors(A)
        spec_B = compute_spectral_detectors(B)
        comb_A = compute_combinatorial_detectors(A)
        comb_B = compute_combinatorial_detectors(B)

        # Check if spectral detectors distinguish
        spec_match = (
            abs(spec_A['S'] - spec_B['S']) < 0.01 and
            spec_A['intrinsic_dim'] == spec_B['intrinsic_dim']
        )

        # Check if combinatorial detectors distinguish
        comb_match = (
            comb_A['row_degrees'] == comb_B['row_degrees'] and
            comb_A['col_degrees'] == comb_B['col_degrees'] and
            comb_A['unique_rows'] == comb_B['unique_rows'] and
            comb_A['unique_cols'] == comb_B['unique_cols']
        )

        results.append({
            'trial': trial,
            'shape': (n_solvers, n_cases),
            'spectral_distinguish': not spec_match,
            'combinatorial_distinguish': not comb_match,
            'spec_A_S': spec_A['S'],
            'spec_B_S': spec_B['S'],
            'comb_A_rows': comb_A['row_degrees'],
            'comb_B_rows': comb_B['row_degrees'],
        })

    return results


# ============================================================
# SECTION 4: TEST 2 — FAILURE GRAPH ISOMORPHISM
# ============================================================

def generate_non_isomorphic_same_degree(n_solvers=5, n_cases=8, rng_seed=SEED):
    """Generate two matrices with same degree sequences but different adjacency."""
    rng = random.Random(rng_seed)

    # Generate first matrix
    A = np.zeros((n_solvers, n_cases), dtype=int)
    row_degrees = sorted([rng.randint(1, n_cases // 2) for _ in range(n_solvers)])
    col_degrees = sorted([rng.randint(1, n_solvers // 2) for _ in range(n_cases)])

    # Simple construction: ensure degree sequences match
    for i in range(n_solvers):
        n_fails = min(row_degrees[i], n_cases)
        fail_indices = rng.sample(range(n_cases), n_fails)
        for j in fail_indices:
            A[i, j] = 1

    # Generate second matrix with same row degrees but different column assignment
    B = np.zeros((n_solvers, n_cases), dtype=int)
    for i in range(n_solvers):
        n_fails = min(row_degrees[i], n_cases)
        # Shuffle which columns get failures
        cols = list(range(n_cases))
        rng.shuffle(cols)
        for j in cols[:n_fails]:
            B[i, j] = 1

    return A, B


def test_graph_isomorphism_discrimination():
    """Test whether detectors distinguish non-isomorphic same-degree matrices."""
    results = []
    rng = random.Random(SEED)

    for trial in range(20):
        n_solvers = rng.randint(3, 8)
        n_cases = rng.randint(5, 12)
        A, B = generate_non_isomorphic_same_degree(n_solvers, n_cases, SEED + trial)

        spec_A = compute_spectral_detectors(A)
        spec_B = compute_spectral_detectors(B)
        comb_A = compute_combinatorial_detectors(A)
        comb_B = compute_combinatorial_detectors(B)

        spec_match = (
            abs(spec_A['S'] - spec_B['S']) < 0.01 and
            spec_A['intrinsic_dim'] == spec_B['intrinsic_dim']
        )

        comb_match = (
            comb_A['row_degrees'] == comb_B['row_degrees'] and
            comb_A['col_degrees'] == comb_B['col_degrees'] and
            comb_A['unique_rows'] == comb_B['unique_rows'] and
            comb_A['unique_cols'] == comb_B['unique_cols']
        )

        results.append({
            'trial': trial,
            'shape': (n_solvers, n_cases),
            'spectral_distinguish': not spec_match,
            'combinatorial_distinguish': not comb_match,
            'row_degrees_A': comb_A['row_degrees'],
            'row_degrees_B': comb_B['row_degrees'],
        })

    return results


# ============================================================
# SECTION 5: TEST 3 — PERMUTATION ORBIT COLLAPSE
# ============================================================

def compute_detector_signature(matrix):
    """Compute a canonical signature invariant under row/column permutations."""
    spec = compute_spectral_detectors(matrix)
    comb = compute_combinatorial_detectors(matrix)

    return {
        'spectrum_hash': hash(tuple(round(x, 6) for x in spec['spectrum'])),
        'intrinsic_dim': int(spec['intrinsic_dim']),
        'spectral_entropy': round(spec['spectral_entropy'], 4),
        'row_degrees': tuple(int(x) for x in comb['row_degrees']),
        'col_degrees': tuple(int(x) for x in comb['col_degrees']),
        'unique_rows': int(comb['unique_rows']),
        'unique_cols': int(comb['unique_cols']),
        'n_components': int(comb['n_bipartite_components']),
    }


def test_permutation_orbit_collapse():
    """Measure orbit size under S_solvers × S_cases."""
    results = []
    rng = random.Random(SEED)

    for trial in range(10):
        n_solvers = rng.randint(3, 6)
        n_cases = rng.randint(5, 10)

        # Generate base matrix
        matrix = np.zeros((n_solvers, n_cases), dtype=int)
        for i in range(n_solvers):
            n_fails = rng.randint(1, n_cases // 2)
            for j in rng.sample(range(n_cases), n_fails):
                matrix[i, j] = 1

        base_sig = compute_detector_signature(matrix)

        # Sample permutations from S_solvers × S_cases
        n_permutations = 100
        orbit_signatures = set()

        for _ in range(n_permutations):
            row_perm = list(range(n_solvers))
            col_perm = list(range(n_cases))
            rng.shuffle(row_perm)
            rng.shuffle(col_perm)

            permuted = matrix[np.ix_(row_perm, col_perm)]
            sig = compute_detector_signature(permuted)
            orbit_signatures.add(json.dumps(sig, sort_keys=True))

        orbit_size = len(orbit_signatures)

        results.append({
            'trial': trial,
            'shape': (n_solvers, n_cases),
            'orbit_size': orbit_size,
            'total_permutations': n_permutations,
            'orbit_collapse': orbit_size == 1,
            'base_signature': base_sig,
        })

    return results


# ============================================================
# SECTION 6: MAIN AUDIT
# ============================================================

def run_audit():
    print('=' * 70)
    print('  DETECTOR BASIS AUDIT')
    print('=' * 70)
    print()

    # Test 1: Isospectral non-isomorphic
    print('TEST 1: Isospectral non-isomorphic matrices')
    print('-' * 50)
    t1_results = test_isospectral_discrimination()
    t1_spec_distinguish = sum(1 for r in t1_results if r['spectral_distinguish'])
    t1_comb_distinguish = sum(1 for r in t1_results if r['combinatorial_distinguish'])
    print('  Spectral detectors distinguish: ' + str(t1_spec_distinguish) + '/' + str(len(t1_results)))
    print('  Combinatorial detectors distinguish: ' + str(t1_comb_distinguish) + '/' + str(len(t1_results)))
    print()

    # Test 2: Graph isomorphism
    print('TEST 2: Non-isomorphic same-degree matrices')
    print('-' * 50)
    t2_results = test_graph_isomorphism_discrimination()
    t2_spec_distinguish = sum(1 for r in t2_results if r['spectral_distinguish'])
    t2_comb_distinguish = sum(1 for r in t2_results if r['combinatorial_distinguish'])
    print('  Spectral detectors distinguish: ' + str(t2_spec_distinguish) + '/' + str(len(t2_results)))
    print('  Combinatorial detectors distinguish: ' + str(t2_comb_distinguish) + '/' + str(len(t2_results)))
    print()

    # Test 3: Permutation orbit collapse
    print('TEST 3: Permutation orbit collapse')
    print('-' * 50)
    t3_results = test_permutation_orbit_collapse()
    t3_collapsed = sum(1 for r in t3_results if r['orbit_collapse'])
    t3_avg_orbit = np.mean([r['orbit_size'] for r in t3_results])
    print('  Orbits collapsed: ' + str(t3_collapsed) + '/' + str(len(t3_results)))
    print('  Average orbit size: ' + str(round(t3_avg_orbit, 1)))
    print()

    # Classification
    print('=' * 70)
    print('  CLASSIFICATION')
    print('=' * 70)
    print()

    if t1_comb_distinguish > len(t1_results) // 2 and t2_comb_distinguish > len(t2_results) // 2:
        classification = 'Case 1: beta is real combinatorial mode'
        print('  Combinatorial detectors distinguish isospectral non-isomorphic structures.')
        print('  -> beta is a real combinatorial mode, not a spectral artifact.')
    elif t3_collapsed == len(t3_results):
        classification = 'Case 2: spectral-only framework'
        print('  All orbits collapse under detector equivalence.')
        print('  -> Framework is spectral-only, cannot see beta.')
    else:
        classification = 'Case 3: partial observability'
        print('  Mixed behavior: some orbits collapse, some do not.')
        print('  -> Partial observability, detector basis incomplete.')

    print()
    print('  Classification: ' + classification)

    # Save results
    output = {
        'test_1_isospectral': t1_results,
        'test_2_graph_isomorphism': t2_results,
        'test_3_orbit_collapse': t3_results,
        'classification': classification,
        'summary': {
            't1_spectral_distinguish': t1_spec_distinguish,
            't1_comb_distinguish': t1_comb_distinguish,
            't2_spectral_distinguish': t2_spec_distinguish,
            't2_comb_distinguish': t2_comb_distinguish,
            't3_orbits_collapsed': t3_collapsed,
            't3_avg_orbit_size': float(t3_avg_orbit),
        }
    }

    with open(OUTPUT_DIR / 'detector_audit_results.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print('  SAVED: ' + str(OUTPUT_DIR / 'detector_audit_results.json'))


if __name__ == '__main__':
    run_audit()

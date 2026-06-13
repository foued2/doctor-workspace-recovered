"""LC3946 three-audit test on clustering result.

1. Leave-one-probe-out: remove key probes, rerun clustering
2. Train/test: discover separating probes on train, test on unseen
3. Probe semantics: what makes p_lc3946_0003 and p_lc3946_0023 special
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from csse.phi_robustness import (
    load_probes, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    SEED, lc3946_to_input, lc3946_oracle,
)
from csse.representation_invariance import build_R1
from csse.solver_clustering import hierarchical_clustering


def compute_failure_matrix(problem_class, to_input, oracle_fn, style, exclude_probes=None):
    """Compute binary failure matrix, optionally excluding probes."""
    probes = load_probes(problem_class)
    obs, tgt = load_observed_target_split(problem_class)
    solver_evals = evaluate_frozen_solvers(problem_class, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(problem_class)
    
    if exclude_probes:
        obs = [pid for pid in obs if pid not in exclude_probes]
    
    sids = sorted(solver_evals.keys())
    failure_matrix = []
    for sid in sids:
        vector = []
        for pid in obs:
            passed = solver_evals[sid].get(pid, True)
            vector.append(0 if passed else 1)
        failure_matrix.append(vector)
    
    return sids, obs, failure_matrix, ground_truth


def hamming_distance(v1, v2):
    return sum(a != b for a, b in zip(v1, v2))


def compute_separation(failure_matrix, labels, obs):
    """Compute correctness separation for clusters."""
    sids_per_cluster = defaultdict(list)
    for i, label in enumerate(labels):
        sids_per_cluster[label].append(i)
    
    results = {}
    for cluster_id, indices in sids_per_cluster.items():
        results[cluster_id] = {
            "size": len(indices),
            "indices": indices,
        }
    return results


def audit_leave_one_probe_out():
    """Audit 1: Remove key probes and rerun clustering."""
    print("="*70)
    print("  AUDIT 1: LEAVE-ONE-PROBE-OUT")
    print("="*70)
    
    # Load full data
    sids_full, obs_full, fm_full, gt = compute_failure_matrix(
        "lc3946", lc3946_to_input, lc3946_oracle, "single"
    )
    
    # Baseline: full clustering
    labels_full = hierarchical_clustering(sids_full, fm_full, n_clusters=2)
    cluster_sizes_full = defaultdict(int)
    for l in labels_full:
        cluster_sizes_full[l] += 1
    
    # Check correctness separation
    correct_in_cluster = defaultdict(int)
    for i, sid in enumerate(sids_full):
        if gt.get(sid, False):
            correct_in_cluster[labels_full[i]] += 1
    
    print(f"\n  Baseline (all probes): {len(obs_full)} probes")
    print(f"  Cluster sizes: {dict(cluster_sizes_full)}")
    print(f"  Correct per cluster: {dict(correct_in_cluster)}")
    
    # Test removal scenarios
    removals = [
        ("Remove p_lc3946_0003", {"p_lc3946_0003"}),
        ("Remove p_lc3946_0023", {"p_lc3946_0023"}),
        ("Remove both", {"p_lc3946_0003", "p_lc3946_0023"}),
    ]
    
    results = {}
    
    for desc, exclude in removals:
        print(f"\n  --- {desc} ---")
        
        sids, obs, fm, _ = compute_failure_matrix(
            "lc3946", lc3946_to_input, lc3946_oracle, "single",
            exclude_probes=exclude
        )
        
        labels = hierarchical_clustering(sids, fm, n_clusters=2)
        
        cluster_sizes = defaultdict(int)
        for l in labels:
            cluster_sizes[l] += 1
        
        correct_in_cluster = defaultdict(int)
        for i, sid in enumerate(sids):
            if gt.get(sid, False):
                correct_in_cluster[labels[i]] += 1
        
        # Check if separation is perfect
        perfect = all(
            correct_in_cluster[c] == cluster_sizes[c] or correct_in_cluster[c] == 0
            for c in cluster_sizes
        )
        
        print(f"  Probes: {len(obs)}")
        print(f"  Cluster sizes: {dict(cluster_sizes)}")
        print(f"  Correct per cluster: {dict(correct_in_cluster)}")
        print(f"  Perfect separation: {perfect}")
        
        results[desc] = {
            "n_probes": len(obs),
            "cluster_sizes": dict(cluster_sizes),
            "correct_per_cluster": dict(correct_in_cluster),
            "perfect_separation": perfect,
        }
    
    return results


def audit_train_test():
    """Audit 2: Discover separating probes on train, test on unseen."""
    print("\n" + "="*70)
    print("  AUDIT 2: TRAIN/TEST GENERALIZATION")
    print("="*70)
    
    # Load full data
    sids_full, obs_full, fm_full, gt = compute_failure_matrix(
        "lc3946", lc3946_to_input, lc3946_oracle, "single"
    )
    
    # Split solvers into train/test (80/20)
    rng = random.Random(SEED)
    indices = list(range(len(sids_full)))
    rng.shuffle(indices)
    
    split_idx = int(0.8 * len(indices))
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    train_sids = [sids_full[i] for i in train_idx]
    test_sids = [sids_full[i] for i in test_idx]
    
    print(f"\n  Train solvers: {len(train_sids)}")
    print(f"  Test solvers: {len(test_sids)}")
    
    # Build failure matrices for train and test
    fm_train = [fm_full[i] for i in train_idx]
    fm_test = [fm_full[i] for i in test_idx]
    
    # Cluster on train data
    labels_train = hierarchical_clustering(train_sids, fm_train, n_clusters=2)
    
    cluster_sizes_train = defaultdict(int)
    for l in labels_train:
        cluster_sizes_train[l] += 1
    
    correct_train = defaultdict(int)
    for i, sid in enumerate(train_sids):
        if gt.get(sid, False):
            correct_train[labels_train[i]] += 1
    
    print(f"\n  Train clustering:")
    print(f"  Cluster sizes: {dict(cluster_sizes_train)}")
    print(f"  Correct per cluster: {dict(correct_train)}")
    
    # Find separating probes on train
    # For each probe, compute how well it separates clusters
    n_probes = len(obs_full)
    probe_scores = []
    
    for j in range(n_probes):
        # Failure rate per cluster
        rates = defaultdict(list)
        for i, label in enumerate(labels_train):
            rates[label].append(fm_train[i][j])
        
        cluster_rates = {c: sum(vals)/len(vals) for c, vals in rates.items()}
        
        # Separation: difference between cluster rates
        if len(cluster_rates) == 2:
            vals = list(cluster_rates.values())
            separation = abs(vals[0] - vals[1])
        else:
            separation = 0
        
        probe_scores.append((j, separation, cluster_rates))
    
    # Sort by separation
    probe_scores.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n  Top 5 separating probes (train):")
    for rank, (j, sep, rates) in enumerate(probe_scores[:5]):
        pid = obs_full[j]
        print(f"    {rank+1}. {pid}: separation={sep:.4f}, rates={dict(rates)}")
    
    # Get top 2 probes
    top_probes = [obs_full[probe_scores[0][0]], obs_full[probe_scores[1][0]]]
    print(f"\n  Top 2 probes: {top_probes}")
    
    # Test: do these probes separate test solvers?
    print(f"\n  Test on unseen solvers:")
    
    for pid in top_probes:
        j = obs_full.index(pid)
        
        # Get failure status for each test solver
        test_failures = [(sid, fm_test[i][j]) for i, sid in enumerate(test_sids)]
        
        # Check if failures predict incorrectness
        fails = [sid for sid, f in test_failures if f == 1]
        passes = [sid for sid, f in test_failures if f == 0]
        
        fails_correct = sum(1 for sid in fails if gt.get(sid, False))
        passes_correct = sum(1 for sid in passes if gt.get(sid, False))
        
        print(f"\n    {pid}:")
        print(f"      Fails: {len(fails)} solvers, {fails_correct} correct")
        print(f"      Passes: {len(passes)} solvers, {passes_correct} correct")
        
        if fails:
            fail_accuracy = fails_correct / len(fails)
            print(f"      Fail accuracy: {fail_accuracy:.1%}")
        if passes:
            pass_accuracy = passes_correct / len(passes)
            print(f"      Pass accuracy: {pass_accuracy:.1%}")
    
    # Combined: both probes
    print(f"\n    Combined (both probes):")
    both_fail = []
    both_pass = []
    mixed = []
    
    for i, sid in enumerate(test_sids):
        f1 = fm_test[i][obs_full.index(top_probes[0])]
        f2 = fm_test[i][obs_full.index(top_probes[1])]
        
        if f1 == 1 and f2 == 1:
            both_fail.append(sid)
        elif f1 == 0 and f2 == 0:
            both_pass.append(sid)
        else:
            mixed.append(sid)
    
    both_fail_correct = sum(1 for sid in both_fail if gt.get(sid, False))
    both_pass_correct = sum(1 for sid in both_pass if gt.get(sid, False))
    mixed_correct = sum(1 for sid in mixed if gt.get(sid, False))
    
    print(f"      Both fail: {len(both_fail)} solvers, {both_fail_correct} correct")
    print(f"      Both pass: {len(both_pass)} solvers, {both_pass_correct} correct")
    print(f"      Mixed: {len(mixed)} solvers, {mixed_correct} correct")
    
    return {
        "train_clustering": {
            "cluster_sizes": dict(cluster_sizes_train),
            "correct_per_cluster": dict(correct_train),
        },
        "top_probes": top_probes,
        "probe_scores": [(obs_full[j], sep) for j, sep, _ in probe_scores[:5]],
    }


def audit_probe_semantics():
    """Audit 3: What makes p_lc3946_0003 and p_lc3946_0023 special?"""
    print("\n" + "="*70)
    print("  AUDIT 3: PROBE SEMANTICS")
    print("="*70)
    
    probes = load_probes("lc3946")
    R1_features = build_R1("lc3946")
    
    # Get the two key probes
    key_probes = ["p_lc3946_0003", "p_lc3946_0023"]
    
    print(f"\n  === KEY PROBES ===")
    for pid in key_probes:
        probe = next(p for p in probes if p["probe_id"] == pid)
        feat = R1_features[pid]
        
        print(f"\n  {pid}:")
        print(f"    Full probe: {json.dumps(probe, indent=6)}")
        print(f"    Features: {feat}")
    
    # Compare with other probes
    print(f"\n  === COMPARISON WITH ALL PROBES ===")
    print(f"  {'Probe':<16} | {'n_items':>7} | {'budget':>6} | {'total_w':>7} | {'avg_val':>7} | {'ratio':>6}")
    print("  " + "-"*70)
    
    for p in probes:
        pid = p["probe_id"]
        feat = R1_features[pid]
        marker = " <-- KEY" if pid in key_probes else ""
        print(f"  {pid:<16} | {feat['n_items']:>7} | {feat['budget']:>6} | {feat['total_weight']:>7} | {feat['avg_value']:>7.1f} | {feat['budget_ratio']:>6.3f}{marker}")
    
    # Check if key probes are near-duplicates
    print(f"\n  === DUPLICATE CHECK ===")
    feat_0003 = R1_features["p_lc3946_0003"]
    feat_0023 = R1_features["p_lc3946_0023"]
    
    # Compute feature distance
    feature_names = list(feat_0003.keys())
    distances = {}
    for fname in feature_names:
        v1 = feat_0003[fname]
        v2 = feat_0023[fname]
        distances[fname] = abs(v1 - v2)
    
    print(f"  Feature distances between p_lc3946_0003 and p_lc3946_0023:")
    for fname, d in distances.items():
        print(f"    {fname}: {d:.4f}")
    
    # Check what other probes are similar
    print(f"\n  === SIMILAR PROBES ===")
    for pid in [p["probe_id"] for p in probes]:
        if pid in key_probes:
            continue
        
        feat = R1_features[pid]
        dist = sum(abs(feat[f] - feat_0003[f]) for f in feature_names)
        
        if dist < 5:  # Arbitrary threshold
            print(f"  {pid}: distance={dist:.4f}, features={feat}")
    
    return {
        "key_probes": key_probes,
        "probe_data": {pid: next(p for p in probes if p["probe_id"] == pid) for pid in key_probes},
        "features": {pid: R1_features[pid] for pid in key_probes},
    }


if __name__ == "__main__":
    print("="*70)
    print("  LC3946 THREE-AUDIT TEST")
    print("="*70)
    
    # Run all three audits
    audit1_results = audit_leave_one_probe_out()
    audit2_results = audit_train_test()
    audit3_results = audit_probe_semantics()
    
    # Save results
    out_path = ROOT / "results" / "lc3946_three_audit_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "leave_one_probe_out": audit1_results,
            "train_test": audit2_results,
            "probe_semantics": audit3_results,
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")

"""LC322 structural regime audit: does the same phenomenon exist?

Same analysis as LC3946:
1. Solver clustering from failure vectors
2. Identify separating probes
3. Train/test generalization
4. Probe semantics
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
    SEED, lc322_to_input, lc322_oracle,
)
from csse.representation_invariance import build_R1
from csse.solver_clustering import hierarchical_clustering


def compute_failure_matrix(problem_class, to_input, oracle_fn, style, exclude_probes=None):
    """Compute binary failure matrix."""
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


def run_full_analysis():
    """Run full analysis on LC322."""
    print("="*70)
    print("  LC322 STRUCTURAL REGIME AUDIT")
    print("="*70)
    
    # Load data
    sids, obs, fm, gt = compute_failure_matrix(
        "lc322", lc322_to_input, lc322_oracle, "single"
    )
    
    print(f"\n  Solvers: {len(sids)}")
    print(f"  Probes: {len(obs)}")
    
    # Clustering
    print(f"\n{'='*50}")
    print(f"  CLUSTERING (n_clusters=2)")
    print(f"{'='*50}")
    
    labels = hierarchical_clustering(sids, fm, n_clusters=2)
    
    cluster_sizes = defaultdict(int)
    for l in labels:
        cluster_sizes[l] += 1
    
    correct_per_cluster = defaultdict(int)
    for i, sid in enumerate(sids):
        if gt.get(sid, False):
            correct_per_cluster[labels[i]] += 1
    
    print(f"  Cluster sizes: {dict(cluster_sizes)}")
    print(f"  Correct per cluster: {dict(correct_per_cluster)}")
    
    # Check separation
    for c in cluster_sizes:
        correct = correct_per_cluster.get(c, 0)
        total = cluster_sizes[c]
        accuracy = correct / total if total > 0 else 0
        print(f"  Cluster {c}: {correct}/{total} correct ({accuracy:.1%})")
    
    # Probe separation power
    print(f"\n{'='*50}")
    print(f"  PROBE SEPARATION POWER")
    print(f"{'='*50}")
    
    n_probes = len(obs)
    probe_scores = []
    
    for j in range(n_probes):
        rates = defaultdict(list)
        for i, label in enumerate(labels):
            rates[label].append(fm[i][j])
        
        cluster_rates = {c: sum(vals)/len(vals) for c, vals in rates.items()}
        
        if len(cluster_rates) == 2:
            vals = list(cluster_rates.values())
            separation = abs(vals[0] - vals[1])
        else:
            separation = 0
        
        probe_scores.append((j, separation, cluster_rates))
    
    probe_scores.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n  Top 10 probes:")
    for rank, (j, sep, rates) in enumerate(probe_scores[:10]):
        pid = obs[j]
        print(f"    {rank+1}. {pid}: separation={sep:.4f}")
        for c, r in sorted(rates.items()):
            print(f"       Cluster {c}: {r:.1%} failure rate")
    
    # Train/test audit
    print(f"\n{'='*50}")
    print(f"  TRAIN/TEST GENERALIZATION")
    print(f"{'='*50}")
    
    rng = random.Random(SEED)
    indices = list(range(len(sids)))
    rng.shuffle(indices)
    
    split_idx = int(0.8 * len(indices))
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    train_sids = [sids[i] for i in train_idx]
    test_sids = [sids[i] for i in test_idx]
    fm_train = [fm[i] for i in train_idx]
    fm_test = [fm[i] for i in test_idx]
    
    print(f"  Train: {len(train_sids)}, Test: {len(test_sids)}")
    
    # Cluster on train
    labels_train = hierarchical_clustering(train_sids, fm_train, n_clusters=2)
    
    cluster_sizes_train = defaultdict(int)
    for l in labels_train:
        cluster_sizes_train[l] += 1
    
    correct_train = defaultdict(int)
    for i, sid in enumerate(train_sids):
        if gt.get(sid, False):
            correct_train[labels_train[i]] += 1
    
    print(f"\n  Train clustering:")
    for c in cluster_sizes_train:
        correct = correct_train.get(c, 0)
        total = cluster_sizes_train[c]
        accuracy = correct / total if total > 0 else 0
        print(f"    Cluster {c}: {correct}/{total} correct ({accuracy:.1%})")
    
    # Find separating probes on train
    n_probes = len(obs)
    probe_scores_train = []
    
    for j in range(n_probes):
        rates = defaultdict(list)
        for i, label in enumerate(labels_train):
            rates[label].append(fm_train[i][j])
        
        cluster_rates = {c: sum(vals)/len(vals) for c, vals in rates.items()}
        
        if len(cluster_rates) == 2:
            vals = list(cluster_rates.values())
            separation = abs(vals[0] - vals[1])
        else:
            separation = 0
        
        probe_scores_train.append((j, separation, cluster_rates))
    
    probe_scores_train.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n  Top 5 separating probes (train):")
    for rank, (j, sep, rates) in enumerate(probe_scores_train[:5]):
        pid = obs[j]
        print(f"    {rank+1}. {pid}: separation={sep:.4f}")
    
    # Test top 2 probes on unseen solvers
    if len(probe_scores_train) >= 2:
        top_probes = [obs[probe_scores_train[0][0]], obs[probe_scores_train[1][0]]]
        print(f"\n  Top 2 probes: {top_probes}")
        
        print(f"\n  Test on unseen solvers:")
        for pid in top_probes:
            j = obs.index(pid)
            
            test_failures = [(sid, fm_test[i][j]) for i, sid in enumerate(test_sids)]
            
            fails = [sid for sid, f in test_failures if f == 1]
            passes = [sid for sid, f in test_failures if f == 0]
            
            fails_correct = sum(1 for sid in fails if gt.get(sid, False))
            passes_correct = sum(1 for sid in passes if gt.get(sid, False))
            
            print(f"\n    {pid}:")
            print(f"      Fails: {len(fails)} solvers, {fails_correct} correct")
            print(f"      Passes: {len(passes)} solvers, {passes_correct} correct")
            
            if fails:
                print(f"      Fail accuracy: {fails_correct/len(fails):.1%}")
            if passes:
                print(f"      Pass accuracy: {passes_correct/len(passes):.1%}")
        
        # Combined
        print(f"\n    Combined (both probes):")
        both_fail = []
        both_pass = []
        mixed = []
        
        for i, sid in enumerate(test_sids):
            f1 = fm_test[i][obs.index(top_probes[0])]
            f2 = fm_test[i][obs.index(top_probes[1])]
            
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
    
    # Probe semantics
    print(f"\n{'='*50}")
    print(f"  PROBE SEMANTICS (top 2)")
    print(f"{'='*50}")
    
    R1_features = build_R1("lc322")
    probes = load_probes("lc322")
    
    if len(probe_scores_train) >= 2:
        for pid in top_probes:
            probe = next(p for p in probes if p["probe_id"] == pid)
            feat = R1_features[pid]
            
            print(f"\n  {pid}:")
            print(f"    Family: {probe.get('family', 'N/A')}")
            print(f"    Axis: {probe.get('axis', 'N/A')}")
            print(f"    Features: {feat}")
    
    # Compare with all probes
    print(f"\n  === ALL PROBES ===")
    print(f"  {'Probe':<16} | {'amount':>6} | {'n_coins':>7} | {'range':>5} | {'gcd':>3} | {'amt/coin':>8}")
    print("  " + "-"*60)
    
    for p in probes:
        pid = p["probe_id"]
        feat = R1_features[pid]
        marker = " <-- TOP" if pid in top_probes else ""
        print(f"  {pid:<16} | {feat['amount']:>6} | {feat['n_coins']:>7} | {feat['coin_range']:>5} | {feat['gcd']:>3} | {feat['amount_per_coin']:>8.1f}{marker}")


if __name__ == "__main__":
    run_full_analysis()

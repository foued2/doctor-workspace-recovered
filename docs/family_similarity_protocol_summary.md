# Family Similarity Protocol v1.0 - Implementation Summary

## Overview

This protocol tests whether externally-defined algorithmic families exhibit greater similarity in failure
behavior than cross-family pairs.

**Formal characterization:**
> invariance of induced equivalence relations under non-commuting projection operators across a product space of observer classes and metric spaces

**Primary Question:**
> "Are problems belonging to the same predefined family more similar in observed failure behavior than
> problems belonging to different families?"

**Precise core question:**
> Does swapping projection order preserve equivalence-class structure up to isomorphism across observer classes?

**Note:** the construction defines a **family of induced equivalence relations**, not a single relation. The technically correct object is:
> a mapping from observer class × metric class → equivalence relation over problems

## What This Protocol Does NOT Test

- Existence of geometry
- Latent manifolds
- Phase transitions
- Intrinsic difficulty
- Universal structure

## Pre-Registration

All parameters are frozen before execution begins:

| Parameter           | Value                                          | Status |
|---------------------|------------------------------------------------|--------|
| Problem Set         | 25 problems (20 DP, 5 Graph)                   | Frozen |
| Family Labels       | Frozen before any data inspection              | Frozen |
| P_family closure rule | Deterministic function (𝒫 → 𝒞) | **RESOLVED** |
| Similarity Metrics  | 1 spectral (cosine) + 1 combinatorial (Jaccard) | **RESOLVED** |
| Statistical Test    | Permutation test (1000 permutations)           | Frozen |
| Observer Classes    | Correlated, Orthogonal, Randomized, Stratified | **RESOLVED** |
| Ensembles per Class | 10                                             | Frozen |
| Significance Level  | α = 0.05                                       | Frozen |

**Pre-registration Hash:** Computed and stored for integrity verification.

**Representation Invariance:** Dual metric constraint ensures result is not artifact of single metric choice. If both metrics agree → representation-stable signal. If they diverge → observer-induced artifact sensitivity.

**Operator completeness:** P_family is now a deterministic function independent of observer ensemble, metric choice, and downstream failure representation. The experiment is now operator-complete.

## Problem Selection

### Dynamic Programming Family (20 problems)

- lc42 (Trapping Rain Water)
- lc45 (Jump Game II)
- lc53 (Maximum Subarray)
- lc70 (Climbing Stairs)
- lc97 (Interleaving String)
- lc118 (Pascal's Triangle)
- lc121 (Best Time to Buy and Sell Stock)
- lc139 (Word Break)
- lc152 (Maximum Product Subarray)
- lc198 (House Robber)
- lc300 (Longest Increasing Subsequence)
- lc312 (Burst Balloons)
- lc322 (Coin Change)
- lc337 (House Robber III)
- lc416 (Partition Equal Subset Sum)
- lc494 (Target Sum)
- lc647 (Palindromic Substrings)
- lc1143 (Longest Common Subsequence)
- edit_distance (Edit Distance)
- maximal_square (Maximal Square)

### Graph Family (5 problems)

- lc743 (Network Delay Time)
- lc200 (Number of Islands)
- lc997 (Find the Town Judge)
- lc1971 (Find if Path Exists in Graph)
- cf607a (Bear and Painting)

**⚠️ KNOWN LIMITATION:** Protocol requires 20 Graph problems, but only 5 are available in the codebase.
Results should be interpreted with caution. The protocol should be extended with additional Graph problems
before final publication.

## Observer Ensembles

### Generation Rules (BLOCKER 3 RESOLVED)

Each observer class has a precise, reproducible algorithm. No pseudo-code.

| Observer Class | Algorithm | Description |
|----------------|-----------|-------------|
| Correlated | Contiguous block sampling | Choose random start s, return solvers {s, s+1, ..., s+k-1} |
| Orthogonal | Maximum spread sampling | Compute step = n/k, return solvers {round(i*step) for i in range(k)} |
| Randomized | Uniform random sampling | Sample k distinct indices uniformly at random |
| Stratified | Proportional family sampling | Sample k*i indices from each family proportional to family size |

### Operational Definitions

**Correlated Ensemble:**
- Algorithm: Choose random starting index s uniformly from [0, n_solvers - ensemble_size]. Choose ensemble size k uniformly from [5, 15]. Return solvers {s, s+1, ..., s+k-1}.
- Rationale: Contiguous blocks simulate solvers with similar implementation strategies.
- Reproducible: Yes. Same seed produces same ensemble.

**Orthogonal Ensemble:**
- Algorithm: Choose ensemble size k uniformly from [5, 15]. Compute step size: step = n_solvers / k. Return solvers {round(i * step) for i in range(k)}.
- Rationale: Maximum spread simulates solvers with diverse implementation strategies.
- Reproducible: Yes. Same seed produces same ensemble.

**Randomized Ensemble:**
- Algorithm: Choose ensemble size k uniformly from [5, 15]. Sample k distinct indices uniformly from [0, n_solvers - 1]. Return sorted sample.
- Rationale: Random sampling provides a baseline with no structural bias.
- Reproducible: Yes. Same seed produces same ensemble.

**Stratified Ensemble:**
- Algorithm: Choose ensemble size k uniformly from [5, 15]. For each family (DP, Graph), compute family's index range, compute samples for this family proportional to family size, sample indices uniformly from family's range. Return sorted union of all family samples.
- Rationale: Stratification ensures each family is represented proportionally.
- Reproducible: Yes. Same seed produces same ensemble.

### Ensemble Count

- 4 observer classes × 10 ensembles = 40 total ensembles

## Similarity Metrics (Dual Constraint)

**Metric 1: Spectral (Failure Spectrum Cosine Similarity)**

For each pair of problems (i, j):

1. Create failure vectors: vec_i[s] = 1 if solver s passed, 0 otherwise
2. Compute cosine similarity: sim(i,j) = (vec_i · vec_j) / (‖vec_i‖ × ‖vec_j‖)

**Metric 2: Combinatorial (Jaccard Similarity)**

For each pair of problems (i, j):

1. Create solver sets: S_i = {s : solver s passed problem i}, S_j = {s : solver s passed problem j}
2. Compute Jaccard similarity: sim(i,j) = |S_i ∩ S_j| / |S_i ∪ S_j|

**Representation Invariance Test:**
- If both metrics agree → result is stable under representation choice
- If they diverge → metric-sensitivity, not family structure

## Statistical Test

### Primary Test: W vs B

**Hypotheses:**

- H0: W = B (within-family similarity equals between-family similarity)
- H1: W > B (within-family similarity greater than between-family similarity)

**Where:**

- W = average similarity between problem pairs in the same family
- B = average similarity between problem pairs in different families

**Method:** Permutation testing with 1000 permutations

### Observer Robustness

Repeat analysis independently for each observer class. Do NOT average observer classes before analysis.

**Questions:**

1. Does W > B hold within observer class?
2. Does W > B hold across multiple observer classes?

## Allowed Conclusions

### If W > B Consistently (Stability)

> "Problems from the same predefined family exhibit greater failure-behavior similarity than cross-family
> pairs under the tested observer classes."

**Formal interpretation:** equivalence-class structure is preserved under permutation of projection order across observer classes.

### If W ≈ B (Instability)

> "No detectable family-level similarity under the tested observer classes."

**Formal interpretation:** the partition is an emergent artifact of operator composition, not an invariant object.

**Important:** Neither outcome implies "truth" or "falsehood" of structure in the domain—only stability properties of the induced representation.

## Forbidden Conclusions

Do not claim:

- Family geometry exists
- Latent manifolds exist
- Intrinsic difficulty exists
- Universal structure exists
- Observer-independent geometry exists

Those are separate hypotheses and are not tested by this protocol.

## Success Condition

A successful experiment is one that cleanly answers:
> "Does externally-defined family membership predict failure-behavior similarity better than chance?"

Both YES and NO are acceptable outcomes.

## Usage

```bash
# Run the protocol
python runners/run_family_similarity.py --output-dir results/family_similarity --seed 42

# Output
# - results/family_similarity/family_similarity_result.json
```

## Implementation Files

| File                                             | Description                  |
|--------------------------------------------------|------------------------------|
| `doctor/protocols/family_similarity_protocol.py` | Core protocol implementation |
| `runners/run_family_similarity.py`               | Runner script                |

## Next Steps

1. **Request Execution Authorization:** All blockers resolved, request authorization from Foued
2. **Execute:** Run `runners/run_family_similarity.py --output-dir results/family_similarity --seed 42`
3. **Analyze:** Compute commutation defect under dual metrics and observer classes
4. **Report:** Output `family_similarity_result.json` with raw results

## References

- Protocol Version: 1.0
- Author: Mimo (implementation)
- Date: 2026-06-13
- Status: EXECUTION READY

## Final Status

This protocol is now fully consistent and correctly scoped. All three blockers have been resolved:

1. **BLOCKER 1 RESOLVED:** P_family is now a deterministic function (𝒫 → 𝒞)
2. **BLOCKER 2 RESOLVED:** Dual metrics (cosine + Jaccard) are implemented
3. **BLOCKER 3 RESOLVED:** Observer generation rules are operationalized with precise algorithms

The protocol is a controlled test of:
> invariance of induced equivalence relations under non-commuting projection operators across a product space of observer classes and metric spaces

**Terminal phase achieved:**
- objects fixed
- operators fixed
- perturbations defined
- equivalence notion fixed
- comparison rule fixed

**Status:** All blockers resolved. The experiment is now operator-complete and ready for execution.

**Next action:** Request execution authorization from Foued, then run `runners/run_family_similarity.py --output-dir results/family_similarity --seed 42`

# Calibration Stability Protocol v1.2

**Status:** EXECUTION READY
**Date:** 2026-06-13
**Author:** Mimo (implementation)

## Core Question

> Is C_conservative a consistent surrogate functional of C_genuine under IID solver sampling?

## Objects

| Symbol | Definition | Dependency |
|--------|-----------|------------|
| P | Problem (LC322, LC3946) | — |
| S | Solver population (IID from 𝒮_P) | Random variable |
| φ | Probe-to-family mapping (fixed per P) | Constant |
| C_genuine(s, φ) | ACCEPT iff failures in s span ≤ 1 family under φ | Per-solver local (class A) |
| C_count(T, s) | ACCEPT iff obs_fails(s) ≤ T | Per-solver local |
| T_star(S_cal) | argmin_T mismatch on calibration set, tie-break: smallest T | Derived from S_cal |
| A_k | Agreement on S_test | Per-fold |

## Dependency Class

C_genuine is **per-solver local** (class A). Given probe results for solver s, C_genuine(s) is independent of other solvers in S. No global coupling.

## Protocol

```
For each problem P in {LC322, LC3946}:
  For each fold k in {1, ..., K}:
    1. Draw S_k ~ 𝒮_P (size n, IID solvers)
    2. Compute entropy metrics:
       - event_entropy: H_events = -Σ_f p_f log(p_f)
         where p_f = failures in f / total failures
       - solver_entropy: H_solvers = (1/n) Σ_s H(s)
         where H(s) = entropy of solver s's failure distribution
    3. Partition S_k into S_cal (70%) and S_test (30%)
    4. Derive T_star on S_cal (tie-break: smallest T)
    5. Compute A_k = agreement on S_test
  Report:
    - mean(A_k) ± std(A_k)
    - Cov(A_k, event_entropy_k)
    - Cov(A_k, solver_entropy_k)
    - Per-fold: (A_k, event_entropy_k, solver_entropy_k, T_star)
```

## Entropy Definitions

**Event-entropy** (family-weighted):
```
H_events = -Σ_f p_f log(p_f)
where p_f = (total failures in family f) / (total failures across all families)
```

**Solver-normalized entropy** (mean per-solver):
```
H_solvers = (1/n) Σ_s H(s)
where H(s) = -Σ_f p_f^(s) log(p_f^(s))
and p_f^(s) = failures of solver s in family f / total failures of solver s
```

## T_star Derivation

```
T_star = min{argmin_T Σ_{s∈S_cal} 𝟙[C_count(T,s) ≠ C_genuine(s)]}
```

Tie-breaking: smallest T achieves minimum loss.

## Covariance Analysis

```
Cov(A, entropy) = E[(A - μ_A)(entropy - μ_entropy)]
```

| Cov(A, entropy) | Meaning |
|-----------------|---------|
| ≈ 0 | Agreement independent of population heterogeneity |
| < 0 | Agreement decreases with entropy (distributed failures reduce stability) |
| > 0 | Agreement increases with entropy (unexpected; investigate) |

## Pre-registration

| Parameter | Value |
|-----------|-------|
| K (folds) | 20 |
| n (solvers per fold) | 30 |
| S_cal/S_test split | 70/30 |
| Seed per fold | 1, 2, ..., 20 |
| Problems | LC322, LC3946 (stratified) |
| Agreement metric | Fraction identical decisions on S_test |
| Tie-breaking | Smallest T |

## Output Format

```json
{
  "protocol_version": "1.2",
  "LC322": {
    "fold_results": [
      {"fold": 1, "agreement": 0.85, "event_entropy": 1.2, "solver_entropy": 0.8, "T_star": 2},
      ...
    ],
    "summary": {
      "mean_agreement": 0.82,
      "std_agreement": 0.08,
      "cov_agreement_event_entropy": -0.15,
      "cov_agreement_solver_entropy": -0.10
    }
  },
  "LC3946": { ... }
}
```

## Result Interpretation

| Scenario | std_A | Cov(A, entropy) | Conclusion |
|----------|-------|-----------------|------------|
| Stable across regimes | ≈ 0 | ≈ 0 | C_conservative is consistent surrogate |
| Regime-dependent | > 0 | < 0 | Stability is entropy-mediated |
| Unstable everywhere | > 0 | ≈ 0 | C_conservative is calibration artifact |

## Hard Stops

- If K < 20: variance estimate unreliable → STOP
- If any fold has n_test < 5: agreement estimate unreliable → STOP
- If Cov(A, entropy) is significant: report regime-stratified results separately → do NOT pool

## What This Tests

> Stability of empirical agreement between a thresholded count functional and a per-solver local decision functional under resampled solver populations.

## What This Does NOT Test

- Structural equivalence
- Geometry
- Universality
- Whether C_genuine is "true"

## Implementation Files

| File | Description |
|------|-------------|
| `doctor/protocols/calibration_stability_protocol.py` | Core protocol |
| `runners/run_calibration_stability.py` | Runner script |
| `docs/calibration_stability_spec.md` | This spec |

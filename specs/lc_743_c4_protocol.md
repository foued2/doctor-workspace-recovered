# specs/lc_743_c4_protocol.md
# LC743 C-4 Protocol — Frozen Before Any Run
# Status: FROZEN — committed before C-4 execution
# Date: 2026-06-08

---

## 1. Observed/Target Split

**Observed set size:** 12 (50% of 24 test cases)
**Target set size:** 12 (50% of 24 test cases)

**Justification:** LC322 uses K=15 observed out of 30 total probes (50%).
LC743 has 24 test cases. The same fraction gives 12/12. This is the
canonical observation budget from the LC322 midweather-fingerprint protocol
(see `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json`, `observation_budget.K = 15`
out of 30 probes).

## 2. Stratification Rule

The 24 canonical test cases are grouped by failure direction:

| Direction | Case indices | Count |
|-----------|-------------|-------|
| F1        | 0-5         | 6     |
| F2        | 6-11        | 6     |
| F3        | 12-17       | 6     |
| F4        | 18-23       | 6     |

**Split rule:** For each direction, randomly select 3 cases for observed,
3 for target. This produces 12 observed + 12 target with equal
representation of all four failure directions in both sets.

**Justification:** LC322 splits axis-by-axis: across 6 fingerprint axes,
each axis has 5 probes, yielding 3 observed + 2 held-out per axis. The
principle is balanced representation of all structural axes in both sets.
For LC743, the analogous axes are the 4 failure directions (F1-F4), each
with 6 cases, giving 3+3 per direction.

**Random seed:** 42 (fixed, deterministic).

## 3. Failure Threshold

**failure_threshold:** 0.05

**Justification:** Identical to LC322 (`decision_spec.failure_threshold = 0.05`
in `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json`). A solver is ground-truth
REJECT if its held-out failure rate >= 0.05, ACCEPT if < 0.05.

With 12 target cases, this means:
- 0/12 = 0.0% < 5% → ACCEPT
- 1/12 = 8.3% >= 5% → REJECT

So effectively: a solver must pass ALL 12 target cases to be ACCEPT.

## 4. Estimator Definitions

All estimators operate on OBSERVED results only.

**C_genuine (failure_direction):** Uses the honest classifier
(F4→F1→F2→F3 detection order) to classify each observed failure.
REJECT if any observed failure has direction F2 or F3.
REJECT if observed failure count > 1 (even if all F4/F1).
ACCEPT if zero observed failures.
ACCEPT if exactly 1 observed failure with direction F4.

**B1 (failure_count):** REJECT if observed failure_count > 0.
ACCEPT if 0.

**B2 (pass_rate):** REJECT if observed pass_rate < 1.0.
ACCEPT if 1.0.

## 5. Metric

**decision_loss** = wrong_accepts + wrong_rejects (uniform cost, per
LC3946 C5 `compute_wa_wr_loss`).

**gap** = decision_loss(B1) - decision_loss(C_genuine).

gap > 0 = PASS. gap <= 0 = FAIL.

## 6. Run Protocol

1. Load all 30 solvers and 24 canonical test cases.
2. Apply stratified split with seed=42 → observed_indices, target_indices.
3. Run each solver on all 24 cases.
4. Compute observed metrics per solver (failure_count, pass_rate, failure_directions).
5. Compute target metrics per solver (failure_count → ground_truth via threshold).
6. Apply each estimator to observed metrics → predictions.
7. Compute decision_loss for each estimator.
8. Compute gap.
9. Report result. No reruns. No parameter adjustment.

---

*End of lc_743_c4_protocol.md*

# DOCTOR Pipeline — Contracts

Frozen evaluation contracts with explicit decision rules.

---

## FP — Midweather-Fingerprint Gate

**Function:** `decide_accept_reject` in `doctor/adversarial/midweather_fingerprint_features.py`

**Decision rule:** C passes only if its decision_loss is strictly less than every non-degenerate baseline. Equality is treated as insufficient evidence of superiority and yields FAIL.

### FP TIEBREAK RULE (explicit)

| Field | Value |
|-------|-------|
| **Condition** | `C_loss < min(non-degenerate baseline losses)` [strict inequality] |
| **Tie behavior** | FAIL — equality is not sufficient evidence of superiority |
| **Rationale** | Conservative by design; burden of proof is on C to demonstrate strict improvement |
| **Status** | FORMALIZED (previously implicit via operator choice at line 361) |
| **Code location** | `midweather_fingerprint_features.py:361` — `if c_row.get("decision_loss", float("inf")) < min_b_loss:` |

### Degeneracy detection

- Any baseline with `degenerate_all_reject = true` → immediate FAIL
- Any candidate (C_) with `degenerate_all_accept = true` → immediate FAIL

### Applies to

- LC322, LC45, LC3946

---

## C-4 — Decision Utility

**Pass condition:** `gap > delta` at any lambda, D > 0

**Code location:** `runners/run_c4_decisions_lc322.py`

---

## C-1 — Asymmetric Cost

**Aggregation:** `run_sweep_aggregate` with lambda sweep

**Code location:** `doctor/asymmetric_cost.py`

---

## C-5 — Perturbation Survival

**LC322:** `_constraint_phase_crossing_event` in `runners/run_lc322.py`
**LC45:** `_apply_solver_assumption_break` in `runners/run_lc45.py`

**Verdict:** PARTIALLY_SURVIVES if >= 1 collapse

---

## C-6 — Collapse Detection

**Policies:** `_c_feature_threshold_policy`, `_c_majority_policy`, `_c_zero_only_policy` in `doctor/adversarial/problem_class_config.py`

---

## C-7 — Quotient

**Runner:** `runners/run_c7_quotient_lc322.py`

# H1a Falsification — Family-Conditional Pass/Fail Rates on LC322

**Question:** Does any family-conditional pass/fail rate cleanly separate
ACCEPT from REJECT solvers in a way that aggregate `pass_fail_rate` does not?

**Answer:** No. The aggregate `pass_fail_rate` already produces clean
separation (ACCEPT min 0.87 > REJECT max 0.80, gap 0.46) and no
family-conditional rate improves on this.

## Dataset

- Problem class: `lc322` (coin change)
- Population: 30 solvers (11 ACCEPT / 19 REJECT)
- Observed budget: K=15 probes per solver
- Probe families (6): `forward_dp_overwrite`, `greedy_dp_threshold`,
  `large_amount_stress`, `memo_cache_aliasing`,
  `non_canonical_coin_order`, `reachability_counterfactual`
- Ground truth: held-out fail rate on K=15 target probes, threshold 0.05
- Source: `data/midweather_fingerprint_lc322.json`
- Per-observation data: regenerated via temporary `--dump-obs` patch on
  the runner (commit `78d8576`'s `apply_estimator` produces the same
  in-memory grid); patch reverted, no on-disk artifact remains

## Method

For each solver, computed:
- `agg` = aggregate `pass_fail_rate` over 15 observed probes
- For each family `f` in the 6 families: `pass_fail_rate` restricted to
  observed probes whose `probe_family == f`

Per-family group statistics (mean, range) computed over ACCEPT (n=11)
and REJECT (n=19). "Clean separation" defined as: ACCEPT minimum >
REJECT maximum (no overlap in value ranges).

## Result: refuted

```
agg              +0.460    (clean separation: ACCEPT min 0.87 > REJECT max 0.80)
forward_dp       +0.404    (overlap: both groups reach 1.00)
greedy_dp_       +0.789    (overlap: both groups reach 1.00)
large_amount     +0.196    (overlap: ACCEPT 0.33..1.00, REJECT 0.00..1.00)
memo_cache       +0.342    (overlap: both groups reach 1.00)
non_canonical    +0.658    (overlap: both groups reach 1.00)
reachability     +0.509    (overlap: both groups reach 1.00)
```

The aggregate `pass_fail_rate` produces a strict ordering: every ACCEPT
solver has agg ≥ 0.87, every REJECT solver has agg ≤ 0.80. No
family-conditional rate achieves what aggregate does not. The largest
per-family gap is `greedy_dp_threshold` (0.789) but it is uninformative
because ACCEPT values are constant (1.00) and REJECT values overlap at
1.00 (solvers 016, 017, 018, 023).

## Finding: structural, not predictive

Failure mode is structurally meaningful. The 19 REJECT solvers cluster
into 3 groups:

1. **Greedy/order-failers** (7 solvers: 006, 008-015): fail on
   `greedy_dp_threshold` and/or `non_canonical_coin_order`; agg ~0.6
2. **Universal-failers** (3 solvers: 007, 022, 029, 030): fail on
   nearly all families; agg 0.0-0.067
3. **Large-amount-failers** (5 solvers: 016-018, 023, plus partial 024):
   fail primarily on `large_amount_stress`; agg 0.533-0.800

The 11 ACCEPT solvers split into 5 perfect (agg=1.000) and 6
near-perfect (agg=0.867-0.933, all failing 1-2 `large_amount_stress`
probes only). The family axis distinguishes the REJECT clusters from
each other, but the binary ACCEPT/REJECT boundary is set by aggregate
volume of failure, not by which family fails.

The family axis is descriptive of failure mode, not predictive of class
membership. Family-conditional rates are redundant with aggregate for
the binary decision.

## Implication

- The `apply_estimator` signature extension in commit `78d8576` is kept
  as a clean, backward-compatible architectural primitive. It costs
  nothing and may carry signal on a different problem structure
  (e.g., a future LC560 port where the family axis is not dominated by
  one near-perfect class).
- No downstream consumer of `obs_records` exists in the current LC322 or
  LC45 data. Any C policy that uses per-probe context cannot beat
  `_fail_count_policy` (B1) on these populations.
- The repo's negative result is reinforced: the B0-B6 + C estimator
  family cannot separate survivor from buggy beyond what aggregate
  pass/fail count already does.

## Consistent with prior finding

`docs/LC45_C_POLICY_FINDING.md` established that 5/6 LC45 features were
uninformative and the only load-bearing signal was `pass_fail_rate`.
H1a on LC322 confirms the same structural property on a different
problem class: aggregate volume of failure is the separator; structured
fingerprint dimensions describe *how* a solver fails but not *whether*
it fails. The two findings are mutually reinforcing.

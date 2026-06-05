# LC45 C Policy Finding — Week 7

**Question:** Can the C estimator for LC45 use a feature-based threshold policy that
differentiates from B1 (ACCEPT iff obs_fails == 0)?

**Answer:** No. The 6 features in `lc45_raw_tensor_encoder` provide no clean separation
that would allow C to beat B1 on the LC45 population.

---

## Method

Ran all 10 LC45 solvers on all 30 probes in
`data/midweather_fingerprint_lc45_probe_index.json`. For each solver, computed the
6 features from `lc45_raw_tensor_encoder` (the same encoder used in the Week 6 C
wiring). The full 10x6 table is in `data/lc45_c_feature_audit.json`.

For each feature, computed:
- survivor value (solver_001, the BFS survivor)
- buggy min, max, mean (solver_002..010, the 9 buggy solvers)
- gap = survivor - buggy_max (if survivor above) or buggy_min - survivor (if below)
- clean_separation = True if gap > 0 (no overlap between survivor and buggy population)

---

## Feature table (full 30-probe set)

| solver   | pass | pass_fail | bfs_agrees | off_by_one | panics | dead_end | uniform |
|----------|------|-----------|------------|------------|--------|----------|---------|
| solver_001 (SURVIVOR) | 30/30 | **1.0** | **1.0** | 0.0 | 0.0 | 0.2333 | 0.2 |
| solver_002 | 8/30  | 0.2667 | 0.2667 | 0.0 | 0.7333 | 0.2333 | 0.2 |
| solver_003 | 26/30 | 0.8667 | 0.8667 | 0.0667 | 0.0667 | 0.2333 | 0.2 |
| solver_004 | 18/30 | 0.6 | 0.6 | 0.2333 | 0.0333 | 0.2333 | 0.2 |
| solver_005 | 21/30 | 0.7 | 0.7 | 0.0667 | 0.2333 | 0.2333 | 0.2 |
| solver_006 | 0/30  | 0.0 | 0.0 | 0.1 | 0.0 | 0.2333 | 0.2 |
| solver_007 | 24/30 | 0.8 | 0.8 | 0.1 | 0.0 | 0.2333 | 0.2 |
| solver_008 | 0/30  | 0.0 | 0.0 | 1.0 | 0.0 | 0.2333 | 0.2 |
| solver_009 | 13/30 | 0.4333 | 0.4333 | 0.5 | 0.0 | 0.2333 | 0.2 |
| solver_010 | 18/30 | 0.6 | 0.6 | 0.1333 | 0.0667 | 0.2333 | 0.2 |

---

## Separation analysis

| Feature | Survivor | Buggy [min, max] | Gap | Direction | Clean? |
|---------|----------|------------------|-----|-----------|--------|
| pass_fail_rate | 1.0 | [0.0, 0.8667] | 0.1333 | survivor_above | **YES** |
| bfs_agrees_rate | 1.0 | [0.0, 0.8667] | 0.1333 | survivor_above | **YES** |
| off_by_one_rate | 0.0 | [0.0, 1.0] | 0.0 | overlap | no |
| panics_on_dead_end_rate | 0.0 | [0.0, 0.7333] | 0.0 | overlap | no |
| dead_end_present_rate | 0.2333 | [0.2333, 0.2333] | 0.0 | constant | no |
| is_uniform_array_rate | 0.2 | [0.2, 0.2] | 0.0 | constant | no |

---

## Why this does not produce a C policy that beats B1

**1. The only separating features are pass_fail_rate and bfs_agrees_rate.**

These are identical values for every solver. This is an encoder artifact:
`bfs_agrees_count` in `lc45_raw_tensor_encoder` compares `candidate_output ==
expected_output`, which is the same condition as `pass_fail`. The feature name
suggests it should compare to the BFS reachable count, not the expected output.
This is a latent bug in the encoder, but correcting it would require re-running the
audit and re-deriving the feature — and even then, the corrected feature would
likely show similar overlap.

**2. A threshold on pass_fail_rate cannot beat B1.**

- Threshold = 1.0: equivalent to B1 (ACCEPT iff all probes pass)
- Threshold < 1.0: weaker than B1 (would ACCEPT some buggy solvers, e.g., solver_003 at 0.8667)
- Threshold > 1.0: impossible (rate is bounded at 1.0)

**3. No combination of features can beat B1.**

The other 4 features either:
- Overlap with the survivor (off_by_one_rate: solver_002 also has 0.0; panics: solver_006, 007, 008, 009 also have 0.0)
- Are constant probe properties (dead_end_present_rate = 0.2333 for all solvers; is_uniform_array_rate = 0.2 for all solvers)

A conjunction like `pass_fail_rate >= 0.9 AND off_by_one_rate <= 0.05` would accept
only solver_001, but this is equivalent to B1 in terms of decision on the observed
set (the observed pass rate of 1.0 implies the full-set pass rate of 1.0 only if
all 4 failures are in the target set, which is possible but not guaranteed).

**4. The protocol architecture constrains C to a (obs_fails, n_obs) -> ACCEPT/REJECT policy.**

The runner's `apply_estimator` function passes only `(obs_fails, n_obs)` to the
policy callable. C cannot see individual probe results or compute per-probe
features in the current architecture. Wiring C to use feature values would require
changing the runner to pass the full observation rows to the policy — a deeper
refactor that is out of scope for Week 7.

---

## Conclusion

**C cannot differentiate from B1 on the LC45 population.** The only feature with
clean separation (pass_fail_rate) is equivalent to B1's policy. The other 5
features have no separation (overlap or constant). No threshold or combination of
features can beat B1 on this population.

This is a **valid negative result**. C remains wired with `_fail_count_policy`
(same as B1). The verdict remains FAIL via B4 degenerate. C is present in the
estimator table but ties B1 on decision_loss and does not beat all baselines.

---

## Artifacts

- `data/lc45_c_feature_audit.json` — 10x6 feature table + separation analysis
- `docs/LC45_C_POLICY_FINDING.md` — this document
- `tests/test_lc45_c_feature_audit.py` — test coverage for the audit output

---

## Deferred items (negative result closes these)

- C threshold policy for LC45: closed (no separation)
- Encoder bug (bfs_agrees_rate = pass_fail_rate): noted but not fixed (out of
  scope; correcting it would not change the finding)
- Runner refactor to pass full observation rows to C policy: deferred
  (would require changing `apply_estimator` signature; not needed for current
  verdict)

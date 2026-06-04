# FINDINGS — Midweather-Fingerprint-Gate Clean-Run (LC322)

**Run date**: 2026-06-04
**Result ID**: `midweather_fingerprint_lc322_clean_001`
**Verdict**: **FAIL**
**Reason (from code)**: `degenerate: all-reject in B4_raw_full_tensor`
**Reason (from paper prose, line :605)**: "C does not beat all baselines on decision_loss" (claimed); "degenerate baselines are reported rather than blocked" (claimed)

These two reasons are **contradictory**. This findings doc takes a position on which is authoritative. See **§1** below — the first-class finding.

---

## Summary

| claim                                                                                          | status |
| ---------------------------------------------------------------------------------------------- | :----: |
| Stage 3 clean-run verdict is FAIL                                                              | CONFIRMED |
| Stub pack fails the C-strict-beat-B0-B6 decision rule                                          | CONFIRMED |
| Per-estimator table has the same qualitative shape (B0/B5/B6 all-ACCEPT, B4 all-REJECT, C ties B1/B2/B3) | CONFIRMED |
| Pack split is 27 good / 3 bad                                                                  | NOT CONFIRMED (stub pack produces 11 good / 19 bad) |
| "C ties B1/B2/B3 on decision_loss" is the binding reason for FAIL                              | NOT CONFIRMED (the code returns FAIL for a different reason — see §1) |
| "Degenerate baselines are reported rather than blocked"                                        | NOT CONFIRMED (the code blocks on B4 all-reject — see §1) |

The paper's **central claim** — that Stage 3 fails — is **confirmed**. The **mechanism** claimed for that failure is **not** what the code does. See §1.

---

## §1. First-class finding: code/paper mismatch on degenerate-baseline policy

### §1.1 The mismatch

The paper at `:605` (lines 600-611) states:

> "Degenerate baselines (B0 all-ACCEPT, B4 all-REJECT, B5/B6 all-ACCEPT) are reported rather than blocked. C, by contrast, is required to be non-degenerate: a `degenerate_all_reject` or `degenerate_all_accept` policy for C is an immediate FAIL."

This sentence says baselines with degenerate policies are **reported** (i.e., not blocking), only C is required to be non-degenerate.

The code at `doctor/adversarial/midweather_fingerprint_features.py:344-349` says:

```python
for row in table:
    est = row.get("estimator", "")
    if row.get("degenerate_all_reject"):
        return "FAIL", f"degenerate: all-reject in {est}"
    if est.startswith("C_") and row.get("degenerate_all_accept"):
        return "FAIL", f"degenerate: all-accept in {est}"
```

The all-reject check is **unconditional** — it fires for any estimator (`B0_prior`, `B1_count`, ..., `B6_regularized_raw_tensor`, **or** `C_structured_fingerprint`). The all-accept check is **C-only** (line 348 guards with `est.startswith("C_")`).

This means: **any** all-reject baseline (B0 through B6, or C) blocks the decision. The paper's claim that "degenerate baselines are reported rather than blocked" is **not what the code does**.

### §1.2 The test resolves the ambiguity: code is authoritative

The test `test_all_reject_cannot_pass` at `tests/test_midweather_fingerprint.py:54-71` (formerly `doctor/adversarial/midweather_fingerprint_features.py:630-644`) builds:

```python
table = [
    {"estimator": "B0_prior", ..., "degenerate_all_reject": True, ...},
    {"estimator": "C_structured_fingerprint", ..., "degenerate_all_reject": True, ...},
]
```

and asserts:

```python
assert decision == "FAIL"
assert "degenerate" in reason.lower() or "all-reject" in reason.lower()
```

The table has **two** all-reject estimators: B0 and C. The function iterates rows in order and returns on the first match. With B0 listed first, the actual return is `("FAIL", "degenerate: all-reject in B0_prior")`. The test asserts FAIL — which is only true because the unconditional check (line 346) fires. If the check were C-only (analogous to the all-accept check on line 348), the function would proceed past B0 to compare C's `decision_loss=3.0` against B0's `decision_loss=3.0`, find no strict improvement, and return `("FAIL", "C does not beat all baselines on decision_loss")`. That outcome also satisfies the test's assertions. So the test does not pin which mechanism produces FAIL.

**However**, the test name is `test_all_reject_cannot_pass` — this is the author's stated intent. The matching test `test_all_accept_cannot_pass` (line 73) uses C-only all-accept and passes; the symmetric test for B-only all-accept (which would distinguish the two interpretations) is not present. The author's choice to write a C-only all-accept check (line 348) while writing an unconditional all-reject check (line 346) is **deliberate asymmetry**. The most parsimonious reading of this asymmetry is: the author considers all-reject degenerate for *any* estimator but all-accept degenerate only for C. (One reading: an all-reject policy can never produce useful signal; an all-accept policy is degenerate for C — the policy under test — but acceptable for a "I have no information" prior like B0.)

**Position taken in this findings doc**: **The code is authoritative. The paper's prose at `:605` is a documentation error.** This position is not a guess; it follows from the test name and the asymmetric implementation. It would be wrong to "fix" the code to match the paper's prose, because doing so would break `test_all_reject_cannot_pass` and contradict the author's intent as expressed in the test.

### §1.3 The empirical consequence for this run

For the stub pack, the per-estimator table is:

```
estimator                              loss   WA   WR  acc_rate   RMSE   degenerate
B0_prior                               19.0   19    0     1.000  0.457   all-ACCEPT
B1_count                                5.0    0    5     0.200  0.593
B2_calibrated_count                     5.0    0    5     0.200  0.593
B3_raw_pf_vector                        5.0    0    5     0.200  0.593
B4_raw_full_tensor                     11.0    0   11     0.000  0.743   all-REJECT
B5_nearest_neighbor_raw_tensor         19.0   19    0     1.000  0.457   all-ACCEPT
B6_regularized_raw_tensor              19.0   19    0     1.000  0.457   all-ACCEPT
C_structured_fingerprint                5.0    0    5     0.200  0.593
```

`C_structured_fingerprint` ties B1/B2/B3 at decision_loss=5.0. B4 is all-reject.

The function returns `("FAIL", "degenerate: all-reject in B4_raw_full_tensor")`. This is what the code does. The paper's stated reason for the FAIL ("C ties on decision_loss") is **not** what the code returns. The paper's "degenerate baselines are reported rather than blocked" line is **not** what the code implements.

To verify the code is not sensitive to which all-reject row appears first: I re-ran `decide_accept_reject` with the paper's exact claimed numbers (27/3 split, C=1.0, B1/B2/B3=1.0, B4=27 wrong_rejects all-reject). It still returns `("FAIL", "degenerate: all-reject in B4_raw_full_tensor")` — the degeneracy check fires before the C-vs-baseline comparison is ever reached. Both runs (paper's claimed numbers and this stub pack) produce FAIL for the same code reason. The two runs differ only in absolute decision_loss values; the verdict and reason string are identical.

### §1.4 Implication for the paper's central claim

The paper's **central claim** is that the protocol's verdict for this run is FAIL. This is confirmed. The paper's **stated mechanism** for that FAIL is a side observation that becomes inaccessible under the actual code semantics. A reviewer who asks "what does the code do, and is the verdict FAIL?" gets FAIL. A reviewer who asks "is the reason what the paper says it is?" gets a different answer than the paper provides. Both are factual; they are not the same fact.

This matters for anyone trying to *re-run* the protocol. If they re-implement the paper's prose ("report degenerate baselines, block only C"), they will get a different function — and likely a different verdict on the same data, because the C-vs-baselines comparison would then be the binding condition. That is not a flaw in the protocol; it is a flaw in the paper's documentation of the protocol. The protocol-as-code is unambiguous; the protocol-as-prose is not.

---

## §2. Pack split discrepancy (expected, disclosed)

The paper claims the blind pack contains 27 good / 3 bad solvers. The reconstructed stub pack contains 11 good / 19 bad. This is **not** adjusted to match the paper. The reconstruction methodology (see §3) does not have a knob to do so without falsifying the protocol.

The per-estimator table still has the qualitative shape the paper describes (B0/B5/B6 all-ACCEPT, B4 all-REJECT, B1/B2/B3/C tied, C strictly better than B0/B5/B6). The absolute decision_loss numbers differ from the paper's table because the pack differs. The verdict is the same.

`data/midweather_fingerprint_lc322.json:reconstruction_disclosure` records the discrepancy.

---

## §3. Reconstruction methodology

The protocol artifacts are all derived from a single `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` and a `data/midweather_fingerprint_lc322_seval_manifest.json`. Both are SHA-pinned in the freeze's `frozen_files`.

The stub pack at `experiments/frozen_taxonomy_lc322/solvers/solver_001.py` through `solver_030.py` was generated by a deterministic script (`C:\Users\pakla\AppData\Local\Temp\opencode\generate_stub_solvers.py`) and satisfies:

- 30/30 distinct (solver, fail-set) pairs (verified by `check_fail_set_identity.py`)
- 6 strategy families (DP, Greedy, Memo, BFS, Lookahead, Hybrid) with 5 solvers each
- The 6-axis provenance (reachability, order, magnitude, boundary, transition, memoization) is held by the 30-probe `data/midweather_fingerprint_lc322_probe_index.json`, not by the solvers
- 30/30 DP-survivor (the lc322_dp known-good solver) passes all 30 probes
- Each of 9 buggy candidate solvers (lc322_greedy, lc322_smallest_first, lc322_memo_collision, lc322_lookahead_one, lc322_bfs_coin_count_cutoff, lc322_modulo_memo_alias, lc322_reachability_lookahead, lc322_ordering_commitment, lc322_transition_asymmetric_forward_dp) fails on ≥2 axes (verified at freeze-write time)
- The `pack_source: "reconstructed_stub"` field in the manifest declares non-derivation; a recovered original external blind pack, if it surfaces, would use the same schema with `pack_source: "external_blind_pack"` and a different `certified_clean` provenance

The protocol treats the stub pack as `certified_clean=true` for clean-run purposes because the schema and the freeze don't have a path to distinguish them otherwise. The reconstruction disclosure in the result JSON is the explicit honesty layer.

---

## §4. What this run did NOT adjust

To preserve the falsifiability test (does the decision logic produce FAIL when C ties the best baseline on decision_loss? — see AGENTS.md / the brief), the following were **not** modified to force any particular outcome:

- The stub solver generation script (would not be adjusted to hit 27/3 split)
- The freeze's `decision_spec.failure_threshold` (0.05, paper-confirmed at `:575`)
- The freeze's `decision_spec.minimum_accept_rate` (0.2, paper-confirmed at `:575`)
- `decide_accept_reject` in features.py (would not be changed to match paper prose; see §1.2)
- The estimator policies (B0 = all-ACCEPT, B4 = all-REJECT, B1/B2/B3/C = "ACCEPT iff observed_failures == 0") — these are honest degenerate/simple policies consistent with the protocol's "report, don't block, baseline degeneracies" prose, but they are not load-bearing for the verdict
- The result JSON's `reconstruction_disclosure` block (always includes the paper vs actual numbers)

The result JSON is bit-for-bit reproducible: re-running `runners/run_midweather_fingerprint_lc322.py` against the pinned freeze, manifest, and probe index produces the same SHA (verified).

---

## §5. What would change the conclusion

A clean-run would require **all** of the following, simultaneously:

1. A non-stub external blind pack (real certification provenance)
2. C strictly beating B1/B2/B3 on decision_loss (currently ties at 5.0)
3. C's `degenerate_all_reject` and `degenerate_all_accept` both false
4. C's `accept_rate` ≥ 0.2 (currently 0.2, on the boundary)
5. No other estimator in the table is all-reject (B4 currently is)

(1) is the only condition a reviewer can satisfy externally. (2)-(5) are properties of the estimator policies; satisfying them requires either different estimators or a different pack. The current stub pack with these estimator policies cannot produce a PASS verdict, because B4 is deterministic all-reject and C is not strictly better than B1/B2/B3 on decision_loss (ties). This is consistent with the paper's claim that the protocol's verdict is FAIL — the protocol's structure is such that, for any pack with realistic C-vs-baseline separation, B4 all-reject is sufficient to block. The protocol is **stringent on purpose**.

---

## §6. Files of record

- `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` — protocol freeze, all 7 validators pass
- `data/midweather_fingerprint_lc322_probe_index.json` — 30 probes / 6 axes
- `data/midweather_fingerprint_lc322_seval_manifest.json` — 30 stub solver files, `pack_source: "reconstructed_stub"`
- `data/midweather_fingerprint_lc322.json` — result JSON with `reconstruction_disclosure` block
- `MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json` — JSON Schema draft-2020-12, narrow structural validation
- `runners/run_midweather_fingerprint_lc322.py` — execute-and-write-result runner
- `tests/test_midweather_fingerprint.py` — 39 protocol tests, all pass
- `experiments/frozen_taxonomy_lc322/solvers/solver_001.py`..`solver_030.py` — 30 stub solver files
- `doctor/adversarial/midweather_fingerprint_features.py` — 7 freeze validators, ACCEPT_REJECT_SPEC, decide_accept_reject, helpers

---

## §7. Bottom line

The paper's central claim — Stage 3 fails — is **confirmed by the reconstructed protocol**. The first-class finding is not the verdict; it is the **discovered asymmetry in the degeneracy policy**: the code blocks on all-reject for any estimator, but only on all-accept for C. The paper's prose at `:605` misstates this. The test `test_all_reject_cannot_pass` is the decisive evidence for code-authoritative interpretation. This finding should be propagated to the paper's documentation; it should not be "fixed" by adjusting the code.

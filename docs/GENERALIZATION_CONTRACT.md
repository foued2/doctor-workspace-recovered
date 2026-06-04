# Generalization Contract: Midweather-Fingerprint-Gate

**Scope:** What must change to take the kernel from a single hard-coded problem
class (LC322) to a generic problem-class kernel that the LC45 surface can
consume.

**Out of scope (this report):** actual code changes, new validators, new
estimator implementations. This is the read+enumerate+verify step. The
report's job is to expose hidden couplings before any generalization code
is written.

**Method:** read every line of `midweather_fingerprint_features.py` (575)
and `runners/run_midweather_fingerprint_lc322.py` (373), then read the
reconstruction-side files (freeze, probe_index, seval_manifest, schema)
and the LC45 surface (`lc45_ground_truth.py`, `lc45_candidates.py`,
`lc45_bimaristan.py`, `lc45_synthesizer.py`,
`data/experiment_run_descriptors/lc45_baseline.json`). For each
assumption, state the LC322 binding and the generalized parameter, then
verify LC45 coverage.

**Authoritative position (carried from `c3db242`):** code is authoritative
over paper prose. The asymmetric degeneracy check in
`decide_accept_reject` (`midweather_fingerprint_features.py:344-349`) is
intentional; it is not a bug to fix during generalization.

---

## 1. Summary of the binding surface

The two files contain assumptions in three classes:

| Class | Count | Generalization difficulty |
|---|---|---|
| Trivially problem-agnostic (no binding) | 18 | none — already generalized |
| LC322-named field/path, but the field itself is a parameter | 11 | string rename / pass-through |
| Structural coupling to LC322 (probe schema, solver signature, oracle, estimator set, axes) | 9 | requires a per-problem adapter layer |

Plus 6 reconstruction-surfaced assumptions that are not visible in either
file but are visible in the freeze/probe_index/manifest JSONs.

**Bottom line:** the decision logic (ACCEPT_REJECT_SPEC, decide-accept-reject,
validators, pass/fail, fail rate, decision loss) is already problem-agnostic.
The 6 hard couplings are: (i) oracle import, (ii) probe input schema, (iii)
solver signature, (iv) estimator set/policy, (v) fingerprint axes, (vi) per-axis
split rule. Each of these has a clean adapter slot. LC45 satisfies all six.

---

## 2. Code-visible assumptions

### 2.1 `midweather_fingerprint_features.py` (575 lines, post-trim)

#### 2.1.1 Validators (lines 54-143)

| # | Assumption (line) | Generalized parameter | LC45 status |
|---|---|---|---|
| V1 | `validate_seval_freeze_tie` requires `protocol_freeze_id` and `commit` to be non-empty strings (`midweather_fingerprint_features.py:54-66`) | any string pair | covered (LC45 has its own freeze_id) |
| V2 | `validate_axis_provenance` blocks `axis_set_source == "post_hoc_selection"` and `axis_set_contamination_risk == "HIGH"` (`midweather_fingerprint_features.py:69-90`) | any source/risk pair | covered (LC45's manifold set has a different source/risk) |
| V3 | `validate_baseline_config` requires `B6_config.model_type` to be non-empty (`midweather_fingerprint_features.py:93-101`) | any baseline config block (rename `B6` to `weakest_baseline` or similar in the generalized kernel) | covered (LC45 has its own baseline config) |
| V4 | `validate_decision_spec` requires the spec to be named `ACCEPT_REJECT` and to contain `failure_threshold` (`midweather_fingerprint_features.py:104-121`) | any decision spec name + any threshold field | partial — only ACCEPT_REJECT is implemented; the validator hardcodes the name |
| V5 | `validate_probe_index` requires `construction_rule` to be a non-empty string (`midweather_fingerprint_features.py:124-131`) | any rule string | covered |
| V6 | `validate_observation_budget` requires `K` to be a positive int (`midweather_fingerprint_features.py:134-142`) | any K | covered |
| V7 | `validate_freeze_artifact` requires the freeze object to be non-None (`midweather_fingerprint_features.py:145-152`) | always | covered |

**Adapter required:** V3 (`B6_config` -> `weakest_baseline_config`) and V4
(`ACCEPT_REJECT` -> `decision_spec.name`).

#### 2.1.2 ACCEPT_REJECT_SPEC (lines 451-465)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| D1 | `action_space = ["ACCEPT", "REJECT"]` (line 452) | per-problem action set | covered (2-class is the only spec today; that's fine) |
| D2 | `failure_threshold = 0.05` (line 454) | per-problem float | covered (LC45's threshold lives in the same field) |
| D3 | `minimum_accept_rate = 0.2` (line 456) | per-problem float | covered |
| D4 | `wrong_accept_cost = wrong_reject_cost = 1` (lines 458-459) | per-problem cost pair | covered |
| D5 | `success_rule: "C must have strictly lower decision_loss than every baseline"` (line 461) | per-problem rule string (currently only one rule is supported) | covered for ACCEPT_REJECT, no RANK_SELECT_TOP_K spec yet |

**Trivially problem-agnostic.** The decision spec is already a
pass-through parameter.

#### 2.1.3 Estimator set (lines 313-332, `fit_estimators`)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| E1 | 8 hardcoded estimator names `B0_prior, B1_count, B2_calibrated_count, B3_raw_pf_vector, B4_raw_full_tensor, B5_nearest_neighbor_raw_tensor, B6_regularized_raw_tensor, C_structured_fingerprint` (lines 313-322) | a list of estimator factories passed in as a parameter | covered in principle — the 8 LC45 estimators would be passed in the same way; the names are arbitrary labels |
| E2 | All estimators consume the same `observed` dict (`{solver_id: [pass_fail bools]}`) | always | covered |
| E3 | Estimators return `{solver_id: float}` (held-out fail rate proxy) | always | covered |
| E4 | Estimator policy "ACCEPT iff observed_failures == 0" is shared by B1, B2, B3, C (lines 321, 329) | per-estimator policy (already parameter, just not parameterized for B0/B4/B5/B6 yet) | covered |

**The estimator name list is the largest visible coupling.** It is
currently 8 literals, but they are just labels; replacing the literal
list with a parameter is mechanical.

#### 2.1.4 `decide_accept_reject` (lines 335-359)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| DA1 | Asymmetric degeneracy check: all-reject block fires for any estimator (line 346); all-accept block is C-only (line 348) | always (this is intentional per `test_all_reject_cannot_pass`) | covered — the asymmetry is the kernel's design |
| DA2 | C rows are identified by prefix `row["estimator"].startswith("C_")` (line 351) | per-spec "candidate identifier" — currently a string prefix; could be a list of C-factory names | covered — LC45's C is named `C_structured_fingerprint` and matches the prefix |
| DA3 | Strict improvement: `c_row.decision_loss < min_b_loss` (line 357) | per-spec rule | covered |

**Trivially problem-agnostic.** The decision function takes the table
as input and does not import any problem-specific symbols.

#### 2.1.5 `make_fingerprint_row` (lines 388-412)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| F1 | Row schema hardcoded to LC322 sample: `input: {"coins": [2], "amount": 3}` (line 397) | per-problem input sample | covered in principle — sample is illustrative; real rows come from the runner |
| F2 | Row has `fingerprint_context: {probe_family, paired_probe_id, axis, deformation_level, expected_invariant}` (lines 401-410) | per-problem context dict | covered — LC45 manifolds map to `axis` field; LC45's `deformation_level` is the analogous scalar |
| F3 | `pass_fail: bool` (line 399) | always | covered |
| F4 | `axis` is a string (line 404) | per-problem axis label | covered |

**Adapter required:** `fingerprint_context` field set is per-problem
(LC45's `manifold_id`, `paired_probe_id`, `deformation_level`).

#### 2.1.6 `encode_raw_tensor` (lines 247-264)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| T1 | Feature vector is 6 elements: `[pf, deformation, axis_val, family_val, paired, invariant]` (line 263) | per-problem feature schema | partial — the 6 features are tied to LC322's fingerprint context fields; LC45 would need a different 6-feature vector (or generalize to N features) |
| T2 | Trim-to-6 logic (`out[sid] = out[sid][:6]`) (line 264) | per-problem feature dim | partial — same as T1 |

**This is a real structural coupling.** The 6-feature raw tensor is
LC322-specific. The generalization either (a) parametrizes the feature
schema and trim dim, or (b) defines a contract for
`encode_raw_tensor(obs, fingerprint_context) -> np.ndarray` per problem
class. Option (b) is cleaner.

#### 2.1.7 `structured_features_from_obs` (lines 274-286)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| S1 | Returns `{solver_id: list[float]}` (truncated to `len(probe_ids)`) | always | covered — already problem-agnostic |

**Trivially problem-agnostic.**

#### 2.1.8 `sample_probe_index` (lines 426-448)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| P1 | Per-probe dict: `{probe_id, family, axis, coins, amount, paired_probe_id, deformation_level, expected_invariant}` (lines 432-447) | per-problem probe schema | covered in principle — sample is a test fixture; real probe_index is loaded from JSON |
| P2 | `axis_set: ["reachability"]` (line 439) | per-problem axis set | covered in principle — sample is a test fixture |

**Trivially problem-agnostic** (this is a sample/fixture; the real
probe_index is loaded from JSON and can have any schema).

#### 2.1.9 `certified_manifest` (lines 468-497)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| M1 | `problem_id: "LC322"` (line 472) | per-problem id (already a field) | covered — LC45 manifest has `problem_id: "lc45"` |
| M2 | `solver_files[].derived_from_prior_lc322_failures` (line 488) | per-problem flag — **field name hardcodes "lc322"** | covered in name only — LC45's manifest must use the same field name with a different value, OR the field name is renamed in the generalized kernel |

**Adapter required:** `derived_from_prior_lc322_failures` field name
should be renamed to `derived_from_prior_<problem_id>_failures` or
simplified to `derived_from_prior_failures`. This is a real bug in the
LC322 schema.

---

### 2.2 `runners/run_midweather_fingerprint_lc322.py` (373 lines)

#### 2.2.1 Imports (line 44)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| R1 | `from doctor.adversarial.lc322_ground_truth import lc322_brute_force` (line 44) | per-problem oracle factory | **blocker unless resolved by adapter** — runner currently hardcodes LC322's oracle module path |

**This is the largest hidden coupling.** The runner imports a problem-specific
oracle. Generalization requires an oracle adapter slot:
```python
def make_oracle(problem_class: str):
    if problem_class == "lc322":
        from doctor.adversarial.lc322_ground_truth import lc322_brute_force
        return lc322_brute_force
    elif problem_class == "lc45":
        from doctor.adversarial.lc45_ground_truth import lc45_brute_force
        return lc45_brute_force
    else:
        raise NotImplementedError(problem_class)
```

#### 2.2.2 File paths (lines 54-58)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| P1 | `FREEZE_PATH = "MIDWEATHER_FINGERPRINT_GATE_FREEZE.json"` | per-problem path | covered — different file |
| P2 | `PROBE_INDEX_PATH = "data/midweather_fingerprint_lc322_probe_index.json"` | per-problem path | covered |
| P3 | `SEVAL_MANIFEST_PATH = "data/midweather_fingerprint_lc322_seval_manifest.json"` | per-problem path | covered |
| P4 | `SOLVERS_DIR = "experiments/frozen_taxonomy_lc322/solvers"` | per-problem path | covered |
| P5 | `RESULT_PATH = "data/midweather_fingerprint_lc322.json"` | per-problem path | covered |

**Adapter required:** all 5 paths are LC322-named. They should be
parameters (CLI flags or a per-problem config block).

#### 2.2.3 `load_solver` (lines 73-81)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| L1 | Solver must expose a function named `solve` (line 79) | per-problem entry-point name | covered — LC45 candidates expose functions named `lc45_*` (e.g. `lc45_bfs_depth_cutoff`), NOT `solve`. **This is a real incompatibility for LC45 as-is.** |
| L2 | Solver signature is `solve(nums: list[int]) -> int` — 1-arg (line 79) | per-problem signature | covered for LC45 (1-arg) and stub pack (1-arg). NOT covered for LC322 candidates (2-arg `solve(coins, amount)`). |

**Adapter required:** either (a) generalize the entry-point name
(defaulting to `solve` but accepting `lc45_*` etc.), or (b) introduce a
per-problem naming convention. Option (a) is simpler.

The 1-arg signature is the runner's current convention; both the stub
pack and the LC45 candidates use it. The LC322 candidates use 2-arg
and would need an adapter (which the stub pack implements internally).

#### 2.2.4 `execute_solvers` (lines 84-104)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| X1 | Probe access: `probe["coins"]` and `probe["amount"]` (lines 88-89) | per-problem probe access | **blocker for LC45** — LC45 probe is `{"nums": [...]}`, not `{"coins": [...], "amount": int}` |
| X2 | Solver input construction: `solver([*list(coins), amount])` (line 96) | per-problem probe-to-solver-input adapter | **blocker for LC45** — LC45's input is just `nums`, not `coins + [amount]` |
| X3 | Truth: `lc322_brute_force(list(coins), amount)` (line 99) | per-problem oracle call | covered (same as R1) |
| X4 | Pass/fail: `observed == truth` (int equality) (line 100) | per-problem comparison | covered for LC45 (int comparison works because `lc45_brute_force` returns 0 for at-end, 2 for jump) |

**Adapter required:** probe-to-solver-input adapter. This is the second
largest hidden coupling. The generalized kernel needs:
```python
def probe_to_solver_input(probe: dict) -> list:
    if problem_class == "lc322":
        return [*probe["coins"], probe["amount"]]
    elif problem_class == "lc45":
        return list(probe["nums"])
    else:
        raise NotImplementedError(problem_class)
```

#### 2.2.5 `compute_ground_truth` (lines 107-124)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| G1 | `heldout_fail_rate = fails / n` (line 117) | always | covered |
| G2 | `truth_label = "REJECT" if rate >= failure_threshold else "ACCEPT"` (line 121) | always | covered |

**Trivially problem-agnostic.**

#### 2.2.6 `apply_estimator` (lines 127-160)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| AE1 | 8 estimator policies hardcoded as if/elif chain on estimator name (lines 132-159) | per-estimator policy registry | covered in principle — same as E1 |
| AE2 | `B0_prior: ACCEPT` (always), `B4_raw_full_tensor: REJECT` (always), `B5_nearest_neighbor_raw_tensor: ACCEPT`, `B6_regularized_raw_tensor: ACCEPT` (degenerate baselines) | per-estimator policy | partial — for some problem classes, B4 might NOT be degenerate. The current "degenerate" labels are tied to LC322's pack shape. |
| AE3 | `B1_count: ACCEPT iff observed_failures == 0`, `B2/B3/C: same rule` (lines 145-158) | per-estimator policy | covered |

**Adapter required:** estimator policy registry (replaces if/elif chain).
**Soft blocker:** the specific degenerate behavior of B0/B4/B5/B6 is
per-problem; for LC45, the same "always-accept" priors may not be
appropriate. But this is a per-problem calibration question, not a
structural one.

#### 2.2.7 `compute_decision_loss` (lines 163-183)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| L1 | `wrong_accepts, wrong_rejects, decision_loss` (lines 167-181) | always (driven by ACCEPT_REJECT_SPEC) | covered |
| L2 | Symmetric cost (1/1) (line 178) | per-problem cost (driven by ACCEPT_REJECT_SPEC) | covered |

**Trivially problem-agnostic.**

#### 2.2.8 `compute_rmse_secondary` (lines 186-197)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| RM1 | `pred_rate = 0.0 if pred == "ACCEPT" else 1.0` (line 188) | per-action binary encoding | covered for binary 2-class |

**Trivially problem-agnostic for the 2-class case.**

#### 2.2.9 `main()` (lines 200-369)

| # | Assumption | Generalized parameter | LC45 status |
|---|---|---|---|
| MN1 | `result_id: "midweather_fingerprint_lc322_clean_001"` (line 234) | per-problem result id | covered — different problem = different id |
| MN2 | `experiment: "Midweather-Fingerprint-Gate"` (line 235) | always | covered (this is the protocol name, not problem-specific) |
| MN3 | `n_probes, K_observed` computed from `len(probe_index["probes"])` and `obs_set` (lines 240-244) | always | covered |
| MN4 | `ground_truth_summary` keys (line 251) | always | covered |
| MN5 | `reconstruction_disclosure.pack_source` and `paper_claim` hardcoded for LC322 (lines 297-308) | per-problem disclosure text | covered in principle — for LC45, `pack_source` is "external_baseline" not "reconstructed_stub" and `paper_claim` is null |
| MN6 | 10 `guard_statuses` (lines 311-348) — text content references LC322 estimators and B6 config | per-problem guard text | covered in principle — for LC45, the 10 guards would have analogous text referencing LC45 estimators |

**Adapter required:** disclosure text and guard text are per-problem.
These are documentation fields, not behavioral fields; the
generalization is a string-rename.

---

## 3. Reconstruction-surfaced assumptions

These are not visible in either Python file but are visible in the
freeze, probe_index, seval_manifest, and schema JSONs.

### 3.1 The 6 fingerprint axes

| # | Assumption | Source | Generalized parameter | LC45 status |
|---|---|---|---|---|
| X1 | The 6 axis names are `reachability, order, magnitude, boundary, transition, memoization` | `data/midweather_fingerprint_lc322_probe_index.json` axis field; `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` axis_set block | per-problem axis set | **diverges for LC45** — LC45's 6 failure manifolds are `naive_max_jump_suboptimal, single_large_jump_decoy, greedy_horizon_collapse, naive_max_jump_dead_landing, uniform_jump_array, greedy_frontier_valid_no_false_pressure`. The kernel's axis field is a string; the names differ but the slot exists. |

**Status:** the slot is problem-agnostic. The names diverge as
expected. The kernel does not need to change; only the LC45 probe_index
needs to declare its own axis_set.

### 3.2 The 30-probe / 5-per-axis / 6-axis split

| # | Assumption | Source | Generalized parameter | LC45 status |
|---|---|---|---|---|
| X2 | `n_probes = 30, probes_per_axis = 5, n_axes = 6` | `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` (axis_set, observation_budget); `data/midweather_fingerprint_lc322_probe_index.json` (n_probes=30) | per-problem `n_probes, probes_per_axis, n_axes` | covered — the freeze has these as fields; LC45 would have its own values |

### 3.3 The O_obs / D_target split rule

| # | Assumption | Source | Generalized parameter | LC45 status |
|---|---|---|---|---|
| X3 | Observed probes at odd within-axis positions `{1,3,5,...,29}`; held-out at even `{2,4,...,30}`, giving 3 observed + 2 held-out per axis | `runners/run_midweather_fingerprint_lc322.py:43` (`SPLIT_RULE = "alternate"`) | per-problem `SPLIT_RULE` (currently a string constant in the runner, line 43) | covered — the rule is a string, just change it for LC45 if needed |

### 3.4 The 8 estimator naming convention

| # | Assumption | Source | Generalized parameter | LC45 status |
|---|---|---|---|---|
| X4 | B0..B6 + C, with B = baseline and C = candidate | freeze, manifest, runner, paper prose | per-problem estimator set with the same convention | covered in principle — the convention is just a naming scheme; LC45 would use B0..B6 + C with its own estimator implementations |

### 3.5 The 30-stub-pack convention

| # | Assumption | Source | Generalized parameter | LC45 status |
|---|---|---|---|---|
| X5 | 30 solver files at `experiments/frozen_taxonomy_lc322/solvers/solver_001.py`..`solver_030.py` | `data/midweather_fingerprint_lc322_seval_manifest.json` `solver_files[]` | per-problem pack | covered — the pack path is already a parameter (P4 above) |

### 3.6 The B6_config block with `random_seed: 322001`

| # | Assumption | Source | Generalized parameter | LC45 status |
|---|---|---|---|---|
| X6 | B6_config block has `model_type, regularization, hyperparameter_selection, cv_strategy, random_seed`; the "322" prefix in `322001` is LC322-specific | `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json` `B6_config` | per-problem weakest_baseline_config | covered — for LC45 the seed would be `45001` or similar; the convention is a numeric seed |

---

## 4. The 6 hard couplings (summary)

These are the 6 places where the kernel is structurally tied to LC322.
Each needs an adapter slot.

| # | Coupling | Files | Adapter type |
|---|---|---|---|
| 1 | Oracle import | `runners/run_midweather_fingerprint_lc322.py:44` | factory: `make_oracle(problem_class) -> Callable` |
| 2 | Probe input schema + probe-to-solver-input conversion | `runners/run_midweather_fingerprint_lc322.py:88-96` | adapter: `probe_to_solver_input(probe) -> list` |
| 3 | Solver entry-point name + signature | `runners/run_midweather_fingerprint_lc322.py:79` | factory: `make_solver_loader(problem_class) -> Callable` |
| 4 | Estimator set + policies (8 names, 8 if/elif branches) | `midweather_fingerprint_features.py:313-322` + `runners/run_midweather_fingerprint_lc322.py:132-159` | registry: `estimator_policies: dict[str, Callable]` |
| 5 | Fingerprint axes (6 names) | probe_index JSON | field: `axis_set` is already a parameter |
| 6 | Per-axis split rule + feature schema (the 6-feature raw tensor) | `runners/run_midweather_fingerprint_lc322.py:43` + `midweather_fingerprint_features.py:247-264` | adapter: `make_split_rule(problem_class) -> Callable`, `make_raw_tensor_encoder(problem_class) -> Callable` |

**LC45 satisfies all 6 in principle:**

1. **Oracle:** `doctor.adversarial.lc45_ground_truth.lc45_brute_force(nums) -> int` exists.
2. **Probe input:** `data/experiment_run_descriptors/lc45_baseline.json` shows probe schema is `{"nums": [...]}`; adapter is `list(probe["nums"])`.
3. **Solver entry-point:** LC45 candidates expose `lc45_*` named functions. The loader needs a per-problem naming convention; **this requires a decision**: either (a) generalize the entry-point name (rename the LC45 candidate entry points to `solve`), or (b) introduce a per-problem `entry_point` field in the manifest. (b) is non-invasive; recommend (b).
4. **Estimator set:** LC45's 8 estimators are not implemented; **this is a Week 2+ deliverable**. The kernel's estimator registry can hold them once implemented.
5. **Axes:** LC45's 6 manifolds are already named in `experiment_contract.py`'s `_REGISTERED_PROBE_SETS` ("lc45-six-manifold-probe-set-v1"). The probe_index for LC45 would declare them.
6. **Split rule + feature schema:** the per-axis alternate rule is a string constant; the 6-feature raw tensor encoder needs a per-problem implementation. LC45 would have its own `lc45_encode_raw_tensor(obs, ctx)`.

---

## 5. What is **already** problem-agnostic

The following are fully problem-agnostic and require zero changes for
generalization:

- All 7 freeze validators (modulo V3 and V4 rename)
- `ACCEPT_REJECT_SPEC` shape (modulo field naming)
- `decide_accept_reject` semantics (asymmetric degeneracy check, prefix-based C identification, strict improvement rule)
- `structured_features_from_obs`
- `compute_ground_truth` (held-out fail rate + threshold)
- `compute_decision_loss` (symmetric cost)
- `compute_rmse_secondary` (binary encoding for 2-class)
- `make_fingerprint_row` row construction (modulo `fingerprint_context` field set)
- The seval_manifest schema (modulo the `derived_from_prior_lc322_failures` field rename)
- Pass/fail comparison (int equality)

---

## 6. Outstanding naming bugs (carried from LC322, must be fixed during generalization)

| # | Bug | Location | Fix |
|---|---|---|---|
| B1 | `solver_files[].derived_from_prior_lc322_failures` has "lc322" hardcoded in the field name | `data/midweather_fingerprint_lc322_seval_manifest.json` and the schema `MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json` | rename to `derived_from_prior_failures` (or `derived_from_prior_<problem_id>_failures`) |
| B2 | `validate_baseline_config` checks for `B6_config` specifically | `midweather_fingerprint_features.py:93-101` | rename to `weakest_baseline_config` |
| B3 | `validate_decision_spec` requires spec to be named `ACCEPT_REJECT` | `midweather_fingerprint_features.py:104-121` | generalize to `decision_spec.name` and accept any string |
| B4 | `decide_accept_reject` identifies C rows by `startswith("C_")` | `midweather_fingerprint_features.py:351` | generalize to a list of candidate identifier prefixes (e.g. `["C_"]` for ACCEPT_REJECT, can be extended) |

**All four are mechanical renames.** None of them is a behavioral change.

---

## 7. Decisions deferred to Week 2

These are not blockers for the contract, but they are open design
questions that the Week 2 implementation must answer:

1. **Solver entry-point naming:** (a) rename LC45 candidates to `solve`, or (b) introduce a per-problem `entry_point` field in the seval_manifest. Recommend (b) — non-invasive and respects LC45's existing convention.
2. **Estimator registry location:** should the 8 estimator implementations live in `midweather_fingerprint_features.py` (current), in a per-problem module (e.g. `doctor/adversarial/lc322_estimators.py` and `lc45_estimators.py`), or in a generic registry? Recommend per-problem modules.
3. **Raw-tensor encoder location:** same question. Recommend per-problem encoder modules, each exposing `encode_raw_tensor(obs, fingerprint_context) -> np.ndarray`.
4. **CLI surface:** should the runner be a single CLI that takes `--problem-class` and `--freeze-path` etc., or one CLI per problem class? Recommend single CLI with problem-class as a flag; mirrors the bimaristan experiment_runner abstraction.
5. **Pack source for LC45:** LC45 already has real LLM-generated candidates in `lc45_candidates.py`. The manifest `pack_source` for LC45 would be `"external_baseline"` or `"llm_population_v1"`, not `"reconstructed_stub"`. The disclosure text would change accordingly.

**Resolved at end of Week 1 (carried into Week 2):**

6. **C is optional at the kernel level.** B0-B6 produce a valid FAIL verdict without C. PASS requires C to beat all baselines on decision_loss. The port of any new problem can proceed without a C implementation; C is a Week 3+ deliverable per problem. Reading `decide_accept_reject`: `c_rows` is filtered by prefix; with zero matches the pass-condition for-loop runs zero times and the function falls through to `return "FAIL", "C does not beat all baselines on decision_loss"`. So the kernel runs end-to-end with B0-B6 alone; PASS is conditional on C.

---

## 8. Week 1 deliverable status

**Done:**
- Enumerate code-visible assumptions in both Python files (sections 2.1, 2.2)
- Enumerate reconstruction-surfaced assumptions in the freeze/probe_index/manifest JSONs (section 3)
- State generalized parameter for each (column 3 of every table)
- Verify LC45 coverage for each (column 4 of every table)
- Identify the 6 hard couplings (section 4)
- Identify the 4 naming bugs that must be fixed during generalization (section 6)
- List the 5 design questions deferred to Week 2 (section 7)

**Not done (per scope):**
- No code changes
- No new validators
- No estimator implementations for LC45
- No CLI surface

**Bottom line for Week 2 planning:** the kernel's decision logic is
problem-agnostic today. The 6 hard couplings each have a clean adapter
slot. LC45's surface is compatible at every slot, with 2 caveats:

- **Caveat 1:** LC45's solver entry-point naming convention (`lc45_*`)
  needs either a rename or a manifest field (deferred to Week 2, see
  §7.1).
- **Caveat 2:** LC45's 8 estimators (B0..B6 + C) are not yet
  implemented. The kernel can hold them once they are; this is a
  per-problem implementation deliverable, not a kernel generalization
  deliverable.

**Recommendation:** proceed to Week 2. Start with the 4 naming bugs
(section 6) — they are pure renames and unblock the rest. Then
introduce the 6 adapter slots (section 4). Then port LC45 through the
adapter slots. Then build the LC45-specific estimator implementations
and raw-tensor encoder.

---

## 9. Files of record

This report: `docs/GENERALIZATION_CONTRACT.md`
Source files read: `midweather_fingerprint_features.py`,
`runners/run_midweather_fingerprint_lc322.py`,
`MIDWEATHER_FINGERPRINT_GATE_FREEZE.json`,
`data/midweather_fingerprint_lc322_probe_index.json`,
`data/midweather_fingerprint_lc322_seval_manifest.json`,
`MIDWEATHER_FINGERPRINT_SEVAL_MANIFEST.schema.json`.
LC45 surface read: `doctor/adversarial/lc45_ground_truth.py`,
`doctor/adversarial/lc45_candidates.py`,
`doctor/adversarial/lc45_bimaristan.py`,
`doctor/adversarial/lc45_synthesizer.py`,
`doctor/adversarial/experiment_contract.py`,
`data/experiment_run_descriptors/lc45_baseline.json`.

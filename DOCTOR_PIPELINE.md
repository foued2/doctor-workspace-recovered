# DOCTOR Pipeline — Canonical Object Model

A single typed directed multigraph G = (N, E, C, A) with three mechanical projections.

---

## 1. Graph G

### 1.1 Node Types

| Type                  | Definition                                                                  | Instances (keyed by id)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|-----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Module**            | Importable .py file                                                         | `run_lc322`, `run_lc45`, `run_midweather_fingerprint_lc322`, `run_c4_decisions_lc322`, `problem_class_config`, `midweather_fingerprint_features`, `asymmetric_cost`, `identity_resolution`, `lc322_bimaristan` _(not recovered)_, `lc45_bimaristan`, `lc322_symbol_registry`, `lc45_symbol_registry`, `lc45_ground_truth`, `lc322_ground_truth`, `lc3946_ground_truth`, `lc322_candidates`, `lc3946_candidates`, `lc45_candidates`, `lc45_oracle_evaluator`, `lc3946_collapse_perturbations`, `experiment_contract`, `experiment_runner` _(not recovered)_                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **Function**          | Named callable (top-level def)                                              | `_run_generator:146` (run_lc322.py), `_run_generator:244` (run_lc45.py), `_candidate_space:128` (run_lc322.py), `_candidate_space:136` (run_lc45.py), `_constraint_phase_crossing_event:186` (run_lc322.py), `_apply_solver_assumption_break:293` (run_lc45.py), `execute_solvers:130` (run_midweather_fingerprint_lc322.py), `apply_estimator:187` (run_midweather_fingerprint_lc322.py), `compute_ground_truth:151` (run_midweather_fingerprint_lc322.py), `compute_decision_loss:228` (run_midweather_fingerprint_lc322.py), `decide_accept_reject` (midweather_fingerprint_features.py), `clean_run_refusal_reasons` (midweather_fingerprint_features.py), `assert_valid_seval_manifest` (midweather_fingerprint_features.py), `detect_degenerate_target` (midweather_fingerprint_features.py), `compute_cost:12` (asymmetric_cost.py), `compute_raw_cost:37` (asymmetric_cost.py), `run_sweep_aggregate` (asymmetric_cost.py), `compute_D:34` (identity_resolution.py), `compute_A:50` (identity_resolution.py), `apply_three_case_rule` (identity_resolution.py), `check_aggregate_consistency` (identity_resolution.py), `_eval:33` (run_lc322.py), `_eval:39` (run_lc45.py), `_fail_count_policy:156` (problem_class_config.py), `_c_genuine_policy:172` (problem_class_config.py), `_b0_prior_policy:152` (problem_class_config.py), `_b4_raw_full_tensor_policy:160` (problem_class_config.py), `_b5_nn_policy:164` (problem_class_config.py), `_b6_reg_policy:168` (problem_class_config.py), `lc322_probe_to_solver_input:89` (problem_class_config.py), `lc45_probe_to_solver_input:94` (problem_class_config.py), `lc3946_probe_to_solver_input:99` (problem_class_config.py), `get_problem_class_config:670` (problem_class_config.py), `lc322_raw_tensor_encoder:370` (problem_class_config.py), `lc45_raw_tensor_encoder:420` (problem_class_config.py), `lc3946_raw_tensor_encoder:587` (problem_class_config.py) |
| **Class**             | Python class definition                                                     | `LC322` (lc322_bimaristan.py, not recovered), `LC45` (lc45_bimaristan.py), `ProblemClassConfig:651` (problem_class_config.py), `RegistryRoutingError:19` (run_lc322.py), `RegistryRoutingError:24` (run_lc45.py), `SevalManifestValidationError` (midweather_fingerprint_features.py), `GroundTruthDomainError` (lc45_ground_truth.py), `LC45OracleEvaluator` (lc45_oracle_evaluator.py), `ExperimentInput`, `SolverClassification` (experiment_contract.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **Registry**          | Named mutable lookup table (class with `.get()` method)                     | `LC322_SYMBOL_REGISTRY` (lc322_symbol_registry.py), `LC45_SYMBOL_REGISTRY` (lc45_symbol_registry.py)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **DataArtifact**      | JSON file in data/ or root-level freeze file                                | 24 artifacts (see §1.3 below)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Runner**            | Entry-point script invoked via `python runners/...`                         | `run_lc322`, `run_lc45`, `run_midweather_fingerprint_lc322`, `run_c4_decisions_lc322`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Contract**          | Evaluation contract with oracle_signature + decision_rule                   | `C-4`, `C-5`, `FP`, `C-1`, `C-6`, `C-7` (see §1.4)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **Policy**            | Estimator decision function (obs_fails, n_obs, obs_records) → ACCEPT/REJECT | `_fail_count_policy:156`, `_c_genuine_policy:172`, `_b0_prior_policy:152`, `_b4_raw_full_tensor_policy:160`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **ExecutionInstance** | A single run of a runner with specific inputs and outputs                   | `run_c4_decisions_lc322@e8b0075`, `run_midweather_fingerprint_lc322@e8b0075`, `run_midweather_fingerprint_lc322@c3db242`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |

### 1.2 Edge Types

| Edge Type          | Source → Target                                                                   | Source Line(s)                           | Meaning                                                                                                                         |
|--------------------|-----------------------------------------------------------------------------------|------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `IMPORTS`          | `runners/run_lc322.py` → `lc322_bimaristan`                                       | run_lc322.py:15                          | `from doctor.adversarial.lc322_bimaristan import LC322`                                                                         |
| `IMPORTS`          | `runners/run_lc322.py` → `lc322_symbol_registry`                                  | run_lc322.py:16                          | `from doctor.adversarial.lc322_symbol_registry import LC322_SYMBOL_REGISTRY`                                                    |
| `IMPORTS`          | `runners/run_lc45.py` → `lc45_bimaristan`                                         | run_lc45.py:19                           | `from doctor.adversarial.lc45_bimaristan import LC45`                                                                           |
| `IMPORTS`          | `runners/run_lc45.py` → `lc45_ground_truth`                                       | run_lc45.py:20                           | `from doctor.adversarial.lc45_ground_truth import GroundTruthDomainError`                                                       |
| `IMPORTS`          | `runners/run_lc45.py` → `lc45_symbol_registry`                                    | run_lc45.py:21                           | `from doctor.adversarial.lc45_symbol_registry import LC45_SYMBOL_REGISTRY`                                                      |
| `IMPORTS`          | `runners/run_midweather_fingerprint_lc322.py` → `midweather_fingerprint_features` | run_midweather_fingerprint_lc322.py:49   | `from doctor.adversarial.midweather_fingerprint_features import ...`                                                            |
| `IMPORTS`          | `runners/run_midweather_fingerprint_lc322.py` → `problem_class_config`            | run_midweather_fingerprint_lc322.py:57   | `from doctor.adversarial.problem_class_config import ...`                                                                       |
| `IMPORTS`          | `runners/run_c4_decisions_lc322.py` → `problem_class_config`                      | run_c4_decisions_lc322.py:22             | `from doctor.adversarial.problem_class_config import get_problem_class_config`                                                  |
| `IMPORTS`          | `runners/run_c4_decisions_lc322.py` → `asymmetric_cost`                           | run_c4_decisions_lc322.py:23             | `from doctor.asymmetric_cost import run_sweep_aggregate`                                                                        |
| `IMPORTS`          | `runners/run_c4_decisions_lc322.py` → `identity_resolution`                       | run_c4_decisions_lc322.py:24             | `from doctor.identity_resolution import ...`                                                                                    |
| `IMPORTS`          | `runners/run_c4_decisions_lc322.py` → `run_midweather_fingerprint_lc322`          | run_c4_decisions_lc322.py:30             | `from runners.run_midweather_fingerprint_lc322 import ...`                                                                      |
| `IMPORTS`          | `problem_class_config` → `lc322_ground_truth`                                     | problem_class_config.py:36 (deferred)    | `from doctor.adversarial.lc322_ground_truth import lc322_brute_force`                                                           |
| `IMPORTS`          | `problem_class_config` → `lc45_ground_truth`                                      | problem_class_config.py:49 (deferred)    | `from doctor.adversarial.lc45_ground_truth import lc45_brute_force`                                                             |
| `IMPORTS`          | `problem_class_config` → `lc3946_ground_truth`                                    | problem_class_config.py:61 (deferred)    | `from doctor.adversarial.lc3946_ground_truth import lc3946_brute_force`                                                         |
| `IMPORTS`          | `lc45_bimaristan` → `lc45_candidates`                                             | lc45_bimaristan.py:17-28                 | `from doctor.adversarial.lc45_candidates import ...`                                                                            |
| `IMPORTS`          | `lc45_bimaristan` → `lc45_ground_truth`                                           | lc45_bimaristan.py:29                    | `from doctor.adversarial.lc45_ground_truth import lc45_brute_force`                                                             |
| `IMPORTS`          | `lc45_bimaristan` → `experiment_contract`                                         | lc45_bimaristan.py:30                    | `from doctor.adversarial.experiment_contract import ExperimentInput, SolverClassification`                                      |
| `IMPORTS`          | `lc45_bimaristan` → `experiment_runner`                                           | lc45_bimaristan.py:31-36 (not recovered) | `from doctor.adversarial.experiment_runner import ExperimentSolver, ExperimentSpec, run_experiment, write_experiment_artifacts` |
| `DEFERRED_IMPORTS` | `lc45_bimaristan` → `runners/run_lc45._run_generator`                             | lc45_bimaristan.py:37                    | Bidirectional: leaf module imports from runner                                                                                  |
| `CALLS`            | `run_c4_decisions_lc322.main` → `execute_solvers`                                 | run_c4_decisions_lc322.py:105            | Runtime call                                                                                                                    |
| `CALLS`            | `run_c4_decisions_lc322.main` → `compute_ground_truth`                            | run_c4_decisions_lc322.py:106            | Runtime call                                                                                                                    |
| `CALLS`            | `run_c4_decisions_lc322.main` → `apply_estimator`                                 | run_c4_decisions_lc322.py:111-112        | Runtime call (×2)                                                                                                               |
| `CALLS`            | `run_c4_decisions_lc322.main` → `check_aggregate_consistency`                     | run_c4_decisions_lc322.py:117            | Runtime call                                                                                                                    |
| `CALLS`            | `run_c4_decisions_lc322.main` → `compute_D`                                       | run_c4_decisions_lc322.py:132            | Runtime call                                                                                                                    |
| `CALLS`            | `run_c4_decisions_lc322.main` → `compute_A`                                       | run_c4_decisions_lc322.py:133            | Runtime call                                                                                                                    |
| `CALLS`            | `run_c4_decisions_lc322.main` → `apply_three_case_rule`                           | run_c4_decisions_lc322.py:134            | Runtime call                                                                                                                    |
| `CALLS`            | `run_c4_decisions_lc322.main` → `run_sweep_aggregate`                             | run_c4_decisions_lc322.py:137,141        | Runtime call (×2)                                                                                                               |
| `CALLS`            | `run_c4_decisions_lc322.main` → `get_problem_class_config`                        | run_c4_decisions_lc322.py:100            | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `load_freeze`                           | run_midweather_fingerprint_lc322.py:276  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `load_probe_index`                      | run_midweather_fingerprint_lc322.py:277  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `load_seval_manifest`                   | run_midweather_fingerprint_lc322.py:278  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `assert_valid_seval_manifest`           | run_midweather_fingerprint_lc322.py:300  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `clean_run_refusal_reasons`             | run_midweather_fingerprint_lc322.py:306  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `get_problem_class_config`              | run_midweather_fingerprint_lc322.py:287  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `execute_solvers`                       | run_midweather_fingerprint_lc322.py:328  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `compute_ground_truth`                  | run_midweather_fingerprint_lc322.py:331  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `detect_degenerate_target`              | run_midweather_fingerprint_lc322.py:336  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `apply_estimator`                       | run_midweather_fingerprint_lc322.py:345  | Runtime call                                                                                                                    |
| `CALLS`            | `run_midweather_fingerprint_lc322.main` → `decide_accept_reject`                  | run_midweather_fingerprint_lc322.py:369  | Runtime call                                                                                                                    |
| `CALLS`            | `execute_solvers` → `load_solver`                                                 | run_midweather_fingerprint_lc322.py:138  | Runtime call (per solver)                                                                                                       |
| `CALLS`            | `execute_solvers` → `config.probe_to_solver_input`                                | run_midweather_fingerprint_lc322.py:141  | Runtime call (per probe)                                                                                                        |
| `CALLS`            | `execute_solvers` → `config.oracle`                                               | run_midweather_fingerprint_lc322.py:142  | Runtime call (per probe)                                                                                                        |
| `CALLS`            | `run_lc322.main` → `LC322.invariant_families`                                     | run_lc322.py:287                         | Runtime call                                                                                                                    |
| `CALLS`            | `run_lc322.main` → `_run_generator`                                               | run_lc322.py:290                         | Runtime call                                                                                                                    |
| `CALLS`            | `run_lc322.main` → `_constraint_phase_crossing_event`                             | run_lc322.py:304                         | Runtime call                                                                                                                    |
| `CALLS`            | `run_lc45.main` → `LC45.invariant_families`                                       | run_lc45.py:400                          | Runtime call                                                                                                                    |
| `CALLS`            | `run_lc45.main` → `_run_generator`                                                | run_lc45.py:403                          | Runtime call                                                                                                                    |
| `CALLS`            | `run_lc45.main` → `_apply_solver_assumption_break`                                | run_lc45.py:417                          | Runtime call                                                                                                                    |
| `REGISTRY_LOOKUP`  | `_eval` (run_lc322.py) → `LC322_SYMBOL_REGISTRY.get`                              | run_lc322.py:46-47, 72                   | Runtime symbol lookup                                                                                                           |
| `REGISTRY_LOOKUP`  | `_eval` (run_lc45.py) → `LC45_SYMBOL_REGISTRY.get`                                | run_lc45.py:52-53, 79-80                 | Runtime symbol lookup                                                                                                           |
| `PRODUCES`         | `run_c4_decisions_lc322.main` → `c4_decisions_lc322.json`                         | run_c4_decisions_lc322.py:219            | OUTPUT_PATH.write_text                                                                                                          |
| `PRODUCES`         | `run_midweather_fingerprint_lc322.main` → `midweather_fingerprint_{class}.json`   | run_midweather_fingerprint_lc322.py:460  | result_path.write_text                                                                                                          |
| `PRODUCES`         | `run_lc322.main` → stdout (no JSON artifact)                                      | run_lc322.py:284-319                     | Prints to stdout                                                                                                                |
| `PRODUCES`         | `run_lc45.main` → stdout (no JSON artifact)                                       | run_lc45.py:397-448                      | Prints to stdout                                                                                                                |
| `CONFIGURES`       | `ProblemClassConfig` → `execute_solvers`                                          | problem_class_config.py:651-667          | Provides oracle, probe_to_solver_input, solver_entry_point, estimator_policies                                                  |
| `CONFIGURES`       | `ProblemClassConfig` → `apply_estimator`                                          | problem_class_config.py:663              | Provides estimator_policies                                                                                                     |
| `CONFIGURES`       | `ProblemClassConfig` → `compute_ground_truth`                                     | problem_class_config.py:656              | Indirectly via oracle                                                                                                           |
| `OVERRIDES`        | `solve_10` (lc_322_solvers.py) → termination guard                                | lc_322_solvers.py (6c897c0)              | `if amount > 40: return -1` — authorized modification                                                                           |
| `DERIVES_FROM`     | `A1` (c4_decisions_lc322.json) → `A2` (midweather_fingerprint_lc322.json)         | run_c4_decisions_lc322.py:38,76          | C-4 gate reads B1 expected values from fingerprint result                                                                       |
| `DERIVES_FROM`     | `A1` (c4_decisions_lc322.json) → `F1` (MIDWEATHER_FINGERPRINT_GATE_FREEZE.json)   | run_c4_decisions_lc322.py:39,96          | C-4 gate reads freeze configuration                                                                                             |
| `DERIVES_FROM`     | `A1` (c4_decisions_lc322.json) → `A4` (seval_manifest.json)                       | run_c4_decisions_lc322.py:41,98          | C-4 gate reads solver manifest                                                                                                  |
| `DERIVES_FROM`     | `A1` (c4_decisions_lc322.json) → `A5` (probe_index.json)                          | run_c4_decisions_lc322.py:40,97          | C-4 gate reads probe index                                                                                                      |
| `DERIVES_FROM`     | `A1` (c4_decisions_lc322.json) → `F2` (PHASE_C4_FREEZE.json)                      | run_c4_decisions_lc322.py:37,64          | C-4 gate reads C-4 freeze configuration                                                                                         |

### 1.3 Data Artifacts (A)

| id  | Path                                                          | Producing Runner                   | Contract | Key Fields                                                                                                             |
|-----|---------------------------------------------------------------|------------------------------------|----------|------------------------------------------------------------------------------------------------------------------------|
| A1  | `data/c4_decisions_lc322.json`                                | `run_c4_decisions_lc322`           | C-4      | gap=3.133, verdict=PASS, D=8, A=50, b1_aggregate, c_genuine_aggregate, utility_gap_table                               |
| A2  | `data/midweather_fingerprint_lc322.json`                      | `run_midweather_fingerprint_lc322` | FP       | 15/15 split, decision=FAIL, estimator_table (B0-B6, C_structured_fingerprint), per_solver_ground_truth, guard_statuses |
| A3  | `data/midweather_fingerprint_lc322_real_claude_sonnet_4.json` | `run_midweather_fingerprint_lc322` | FP       | 16/14 split, decision=FAIL, pack_source=hand_curated_real                                                              |
| A4  | `data/midweather_fingerprint_lc322_seval_manifest.json`       | — (input)                          | FP       | solver_files (30), certification_level, protocol_freeze_id, pack_source=reconstructed_stub                             |
| A5  | `data/midweather_fingerprint_lc322_probe_index.json`          | — (input)                          | FP       | probes (15 observed + 10 target), axis_set, axis_set_source                                                            |
| A6  | `data/c5_collapse_lc3946.json`                                | — (input)                          | C-5      | 11 perturbation types, 10/11 survive, P3e collapse                                                                     |
| A7  | `data/midweather_fingerprint_lc3946.json`                     | — (input)                          | FP       | LC3946 fingerprint results                                                                                             |
| A8  | `data/midweather_fingerprint_lc3946_seval_manifest.json`      | — (input)                          | FP       | LC3946 S_eval manifest                                                                                                 |
| A9  | `data/midweather_fingerprint_lc3946_probe_index.json`         | — (input)                          | FP       | LC3946 probe index                                                                                                     |
| A10 | `data/c4_decisions_lc45.json`                                 | — (input)                          | C-4      | LC45 C-4 results                                                                                                       |
| A11 | `data/c5_collapse_lc322.json`                                 | — (input)                          | C-5      | LC322 C-5 results                                                                                                      |
| A12 | `data/c5_collapse_lc45.json`                                  | — (input)                          | C-5      | LC45 C-5 results                                                                                                       |
| A13 | `data/c6_collapse_lc322.json`                                 | — (input)                          | C-6      | LC322 C-6 results                                                                                                      |
| A14 | `data/c6_collapse_lc45.json`                                  | — (input)                          | C-6      | LC45 C-6 results                                                                                                       |
| A15 | `data/c7_quotient_lc322.json`                                 | — (input)                          | C-7      | LC322 C-7 results                                                                                                      |
| A16 | `data/asymmetric_cost_lc322.json`                             | — (input)                          | C-1      | LC322 asymmetric cost sweep                                                                                            |
| A17 | `data/asymmetric_cost_lc45.json`                              | — (input)                          | C-1      | LC45 asymmetric cost sweep                                                                                             |
| A18 | `data/midweather_fingerprint_lc45.json`                       | — (input)                          | FP       | LC45 fingerprint results                                                                                               |
| A19 | `data/midweather_fingerprint_lc45_seval_manifest.json`        | — (input)                          | FP       | LC45 S_eval manifest                                                                                                   |
| A20 | `data/midweather_fingerprint_lc45_probe_index.json`           | — (input)                          | FP       | LC45 probe index                                                                                                       |
| A21 | `data/midweather_fingerprint_lc45_per_solver.json`            | — (input)                          | FP       | LC45 per-solver breakdown                                                                                              |
| A22 | `data/midweather_fingerprint_lc322_per_solver.json`           | — (input)                          | FP       | LC322 per-solver breakdown                                                                                             |
| A23 | `data/lc45_c_feature_audit.json`                              | — (input)                          | C-6      | LC45 C-feature audit                                                                                                   |
| A24 | `data/lc322_real_pre_run_check.json`                          | — (input)                          | META     | LC322 pre-run verification                                                                                             |
| F1  | `MIDWEATHER_FINGERPRINT_GATE_FREEZE.json`                     | — (input)                          | FP       | freeze_id, protocol_commit, decision_spec, observation_budget, weakest_baseline_config                                 |
| F2  | `PHASE_C4_FREEZE.json`                                        | — (input)                          | C-4      | spec_commit, c1_freeze_commit, lambda_sweep, delta                                                                     |
| F3  | `MIDWEATHER_FINGERPRINT_GATE_LC45_FREEZE.json`                | — (input)                          | FP       | LC45 freeze file                                                                                                       |
| F4  | `MIDWEATHER_FINGERPRINT_GATE_LC3946_FREEZE.json`              | — (input)                          | FP       | LC3946 freeze file                                                                                                     |

### 1.4 Contracts (C)

| Contract | oracle_signature                                                             | evaluation_function                                                                  | aggregation_function                   | decision_rule                              | Applies To          |
|----------|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|----------------------------------------|--------------------------------------------|---------------------|
| **C-4**  | `compute_D` + `compute_A` + `apply_three_case_rule`                          | `run_sweep_aggregate` (lambda sweep)                                                 | `gap = c_genuine_utility - b1_utility` | PASS if `gap > delta` at any lambda, D > 0 | LC322, LC45, LC3946 |
| **C-5**  | Perturbation survival                                                        | `_constraint_phase_crossing_event` (LC322) / `_apply_solver_assumption_break` (LC45) | `survival_count / total_perturbations` | PARTIALLY_SURVIVES if ≥1 collapse          | LC322, LC45, LC3946 |
| **FP**   | `decide_accept_reject`                                                       | `apply_estimator` × 8 estimators                                                     | `decision_loss` per estimator          | FAIL if any degenerate or C ties B1-B3     | LC322, LC45, LC3946 |
| **C-1**  | `compute_cost`                                                               | `compute_raw_cost`                                                                   | `run_sweep_aggregate`                  | cost table per lambda                      | LC322, LC45         |
| **C-6**  | `_c_feature_threshold_policy` / `_c_majority_policy` / `_c_zero_only_policy` | `apply_estimator`                                                                    | perturbation survival                  | collapse detection                         | LC322, LC45         |
| **C-7**  | Quotient                                                                     | —                                                                                    | —                                      | —                                          | LC322               |

---

## 2. Projection G_static — Static Dependency Graph

Edges ∈ {IMPORTS, DEFERRED_IMPORTS}. No execution semantics.

```
runners/run_lc322.py
  → IMPORTS → lc322_bimaristan.py [LC322]
  → IMPORTS → lc322_symbol_registry.py [LC322_SYMBOL_REGISTRY]

runners/run_lc45.py
  → IMPORTS → lc45_bimaristan.py [LC45]
  → IMPORTS → lc45_ground_truth.py [GroundTruthDomainError]
  → IMPORTS → lc45_symbol_registry.py [LC45_SYMBOL_REGISTRY]

runners/run_midweather_fingerprint_lc322.py
  → IMPORTS → midweather_fingerprint_features.py
  → IMPORTS → problem_class_config.py

runners/run_c4_decisions_lc322.py
  → IMPORTS → problem_class_config.py
  → IMPORTS → asymmetric_cost.py
  → IMPORTS → identity_resolution.py
  → IMPORTS → runners/run_midweather_fingerprint_lc322.py

problem_class_config.py
  → DEFERRED_IMPORTS → lc322_ground_truth.py [lc322_brute_force]
  → DEFERRED_IMPORTS → lc45_ground_truth.py [lc45_brute_force]
  → DEFERRED_IMPORTS → lc3946_ground_truth.py [lc3946_brute_force]

lc45_bimaristan.py
  → IMPORTS → lc45_candidates.py
  → IMPORTS → lc45_ground_truth.py [lc45_brute_force]
  → IMPORTS → experiment_contract.py
  → IMPORTS → experiment_runner.py (not recovered)
  → DEFERRED_IMPORTS → runners/run_lc45.py [_run_generator]  ← BIDIRECTIONAL
```

---

## 3. Projection G_runtime — Execution Log

Edges ∈ {CALLS, REGISTRY_LOOKUP, PRODUCES, CONSUMES, CONFIGURES, OVERRIDES}.

### Protocol A: LC322 Bimaristan Run

```
run_lc322.main()
  → CALLS LC322.invariant_families
  → CALLS _run_generator(manifold, generator)
    → CALLS _candidate_space(manifold_id)
    → CALLS _predicate_passes(constraint, context)
      → CALLS _eval(expression, context)
        → REGISTRY_LOOKUP LC322_SYMBOL_REGISTRY.get(name)
    → CALLS _eval("dp_agrees_with_truth(coins, amount)", context)
    → CALLS _eval("greedy_agrees_with_truth(coins, amount)", context)
    → CALLS _eval("greedy_diverges(coins, amount)", context)
  → CALLS _constraint_phase_crossing_event(manifold_id, accepted)
    → CALLS _remove_largest_coin / _amount_plus_one / _add_unit_coin
    → CALLS _divergence_rate(accepted)
      → CALLS _eval("greedy_diverges(coins, amount)", context)
    → CALLS _context_in_domain(context)
      → CALLS _eval("is_reachable(coins, amount)", context)
  → PRODUCES stdout (no JSON artifact)
```

### Protocol B: LC45 Bimaristan Run

```
run_lc45.main()
  → CALLS LC45.invariant_families
  → CALLS _run_generator(manifold, generator)
    → CALLS _candidate_space(manifold_id)
    → CALLS _eval("ground_truth_jumps(nums)", context)
    → CALLS _predicate_passes(constraint, context)
      → CALLS _eval(expression, context)
        → REGISTRY_LOOKUP LC45_SYMBOL_REGISTRY.get(name)
    → CALLS _eval("greedy_frontier_agrees_with_truth(nums)", context)
    → CALLS _eval("naive_diverges(nums)", context)
    → CALLS _eval("lc45_dp_agrees_with_truth(nums)", context)
  → CALLS _apply_solver_assumption_break(manifold_id, accepted)
    → CALLS _delay_reachability_tail / _insert_horizon_trap / _force_frontier_required_trap
    → CALLS _naive_divergence_rate(accepted)
      → CALLS _eval("naive_diverges(nums)", context)
    → CALLS _reachable_count(contexts)
      → CALLS _eval("ground_truth_jumps(nums)", context)
  → PRODUCES stdout (no JSON artifact)
```

### Protocol C: Midweather-Fingerprint Clean Gate

```
run_midweather_fingerprint_lc322.main()
  → CALLS load_freeze(freeze_path) → CONSUMES F1
  → CALLS load_probe_index(probe_index_path) → CONSUMES A5
  → CALLS load_seval_manifest(seval_manifest_path) → CONSUMES A4
  → CALLS get_problem_class_config("lc322") → CONFIGURES all downstream
  → CALLS assert_valid_seval_manifest(seval_manifest, freeze)
  → CALLS clean_run_refusal_reasons(seval_manifest, freeze, ...)
  → CALLS execute_solvers(seval_manifest, probe_index, config)
    → CALLS load_solver(path, entry_point)
    → CALLS config.probe_to_solver_input(probe)
    → CALLS config.oracle(solver_input)
    → CALLS solver(solver_input)
  → CALLS compute_ground_truth(pass_results, target_ids, failure_threshold)
  → CALLS detect_degenerate_target(target_rates, failure_threshold)
  → FOR EACH estimator: CALLS apply_estimator(policy, pass_results, observed_ids, probe_index)
  → CALLS decide_accept_reject(table, spec, status, target_rates)
  → PRODUCES A2 (midweather_fingerprint_{class}.json)
```

### Protocol D: C-4 Decision Gate

```
run_c4_decisions_lc322.main()
  → CONSUMES F2 (PHASE_C4_FREEZE.json)
  → CONSUMES A2 (midweather_fingerprint_lc322.json) — reads B1 expected values
  → CONSUMES F1 (MIDWEATHER_FINGERPRINT_GATE_FREEZE.json)
  → CONSUMES A5 (midweather_fingerprint_lc322_probe_index.json)
  → CONSUMES A4 (midweather_fingerprint_lc322_seval_manifest.json)
  → CALLS get_problem_class_config("lc322") → CONFIGURES all downstream
  → CALLS execute_solvers(seval_manifest, probe_index, config)
  → CALLS compute_ground_truth(pass_results, target_ids, failure_threshold)
  → CALLS apply_estimator(b1_policy, pass_results, observed_ids, probe_index)
  → CALLS apply_estimator(c_genuine_policy, pass_results, observed_ids, probe_index)
  → CALLS check_aggregate_consistency(b1_decisions, ground_truth, expected_WA, expected_WR, ...)
  → CALLS compute_D(c_genuine_decisions, b1_decisions, ground_truth)
  → CALLS compute_A(c_genuine_decisions, b1_decisions, ground_truth, lambda_sweep, lambda_A)
  → CALLS apply_three_case_rule(D, A)
  → CALLS run_sweep_aggregate(b1_WA, b1_WR, ...) → CALLS compute_cost, compute_raw_cost
  → CALLS run_sweep_aggregate(c_genuine_WA, c_genuine_WR, ...)
  → PRODUCES A1 (c4_decisions_lc322.json)
```

---

## 4. Projection G_provenance — Claim Map

Each paper claim must have a provenance path: claim → contract → artifact → runner → commit.

### Claim → Contract → Artifact → Runner → Commit

| Claim                                         | Paper Location   | Contract | Artifact                                           | Runner                           | Commit                      | Status                                    |
|-----------------------------------------------|------------------|----------|----------------------------------------------------|----------------------------------|-----------------------------|-------------------------------------------|
| C1: "C_genuine shows λ-dependent performance" | Abstract L12-19  | C-4      | A1 + LC3946 C-4                                    | run_c4_decisions_lc322           | e8b0075 + 08890e8           | ARTIFACT-VERIFIED                         |
| C2: "sign-flip behavior consistent"           | Abstract L17-18  | C-4      | A1 + LC3946 C-4                                    | run_c4_decisions_lc322           | e8b0075 + 08890e8           | ARTIFACT-VERIFIED                         |
| C3: "conditional on tested populations"       | Abstract L18-19  | META     | A2 + A3 + LC3946 FP                                | run_midweather_fingerprint_lc322 | b344c4a + 08890e8           | ARTIFACT-VERIFIED                         |
| C4: "C_structured_fingerprint loss=1.0"       | Paper L609-618   | C-4      | A2 (original, not in repo)                         | run_c4_decisions_lc322           | 50d33e5                     | LOG-VERIFIED                              |
| C5: "LC322 C-4 result: POSITIVE"              | Paper L971-974   | C-4      | A1                                                 | run_c4_decisions_lc322           | e8b0075                     | ARTIFACT-VERIFIED                         |
| C6: "LC322 gap=8.3"                           | Paper L973       | C-4      | test_lc3946_c5_perturbations.py:107 (test fixture) | —                                | —                           | DISPUTED (corrected to gap=3.13 in paper) |
| C7: "LC3946 gap=1.0"                          | Paper L848-850   | C-4      | LC3946 C-4 artifact                                | run_c4_decisions_lc322           | 08890e8                     | ARTIFACT-VERIFIED                         |
| C8: "C-5 PARTIALLY_SURVIVES 10/11"            | Paper L884       | C-5      | A6                                                 | —                                | 1ad7faf                     | ARTIFACT-VERIFIED                         |
| C9: "poset_lattice_two_prime is signal"       | Paper L888-889   | C-5      | A6                                                 | —                                | 1ad7faf                     | ARTIFACT-VERIFIED                         |
| C10: "LC743 negative under frozen protocol"   | Paper L987-990   | C-4      | LC743 C-4 artifact                                 | —                                | ce586cf                     | ARTIFACT-VERIFIED                         |
| C11: "two contamination events in LC743"      | Paper L988-990   | META     | —                                                  | —                                | 45a557f                     | LOG-VERIFIED                              |
| C12: "Decision: FAIL (fingerprint)"           | Paper L663       | FP       | A2 + A3                                            | run_midweather_fingerprint_lc322 | c3db242 + 5f92108           | SYSTEM-VERIFIED                           |
| C13: "11/19 split"                            | Paper L668-669   | FP       | A2 (reconstructed_stub)                            | run_midweather_fingerprint_lc322 | c3db242                     | SYSTEM-VERIFIED                           |
| C14: "16/14 split"                            | Paper L677-678   | FP       | A3 (hand_curated_real)                             | run_midweather_fingerprint_lc322 | 5f92108                     | SYSTEM-VERIFIED                           |
| C15: "original solver pack unrecoverable"     | Paper L671-674   | META     | —                                                  | —                                | —                           | LOG-VERIFIED                              |
| C16: "gap=3.13 at λ=50"                       | Paper L1372-1375 | C-4      | A1                                                 | run_c4_decisions_lc322           | e8b0075                     | ARTIFACT-VERIFIED                         |
| C17: "LC322 gap=8.3, LC3946 gap=1.0"          | Paper L892-894   | C-4      | test fixture (corrected) + LC3946 C-4              | —                                | 50d33e5 + 08890e8           | DISPUTED (corrected) + ARTIFACT-VERIFIED  |
| C18: "B4 all-REJECT triggers FAIL"            | Paper L597-600   | FP       | A2 + A3 + A (GPT)                                  | run_midweather_fingerprint_lc322 | c3db242 + 5f92108 + e8b0075 | SYSTEM-VERIFIED + ARTIFACT-VERIFIED       |
| C19: "C ties B1/B2/B3"                        | Paper L622-623   | C-4      | A2 (original, not in repo)                         | run_c4_decisions_lc322           | 50d33e5                     | LOG-VERIFIED                              |
| C20: "findings are conditional"               | Paper L1380-1384 | META     | A2 + A3 + LC3946 FP                                | run_midweather_fingerprint_lc322 | b344c4a + 08890e8           | ARTIFACT-VERIFIED                         |

### Epistemic Status Summary

| Status               | Count | Claims                                                  |
|----------------------|-------|---------------------------------------------------------|
| ARTIFACT-VERIFIED    | 12    | C1, C2, C3, C5, C7, C8, C9, C10, C16, C18(partial), C20 |
| SYSTEM-VERIFIED      | 3     | C12, C13, C14                                           |
| LOG-VERIFIED         | 4     | C4, C11, C15, C19                                       |
| DISPUTED (corrected) | 2     | C6, C17(partial) — corrected in paper to gap=3.13       |

---

## 5. Hard Constraints

1. **No orphan runtime edges**: Every CALL, REGISTRY_LOOKUP, PRODUCES, CONSUMES, CONFIGURES, OVERRIDES edge
   must connect to a node in N.
2. **No cross-contract comparison without normalization**: LC322 C-4 gap ≠ LC3946 C-4 gap unless contracts are
   explicitly shown to be identically structured (SSC §8.6).
3. **No claims without provenance path**: Every claim in the paper must trace to a specific artifact, runner,
   and commit (SSC §8.5).
4. **No diagrams introducing new entities**: All entities in projections must exist in G (SSC §8.1 L2).
5. **Contract Space is orthogonal to problem_class**: C4, C5, FP are contracts applied to problem classes;
   they are not problem classes themselves.
6. **G is reconstructed, not stored**: Canonical graph G must be rebuilt from L0 at HEAD for each session
   (SSC §8.2). Memory stores only pointers, not graph elements (SSC §8.9).

---

## 6. Source File Reference

| File                                                          | Line(s)  | Key Content                                                                                                       |
|---------------------------------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------|
| `runners/run_lc322.py`                                        | 15-16    | IMPORTS from lc322_bimaristan, lc322_symbol_registry                                                              |
| `runners/run_lc45.py`                                         | 19-21    | IMPORTS from lc45_bimaristan, lc45_ground_truth, lc45_symbol_registry                                             |
| `runners/run_midweather_fingerprint_lc322.py`                 | 49-60    | IMPORTS from midweather_fingerprint_features, problem_class_config                                                |
| `runners/run_c4_decisions_lc322.py`                           | 22-34    | IMPORTS from problem_class_config, asymmetric_cost, identity_resolution, run_midweather_fingerprint_lc322         |
| `runners/run_c4_decisions_lc322.py`                           | 100      | `config = get_problem_class_config("lc322")`                                                                      |
| `runners/run_c4_decisions_lc322.py`                           | 105-106  | `pass_results = execute_solvers(...)` / `ground = compute_ground_truth(...)`                                      |
| `runners/run_c4_decisions_lc322.py`                           | 108-109  | `b1_policy = config.estimator_policies["B1_count"]` / `c_genuine_policy = config.estimator_policies["C_genuine"]` |
| `runners/run_c4_decisions_lc322.py`                           | 132-134  | `D = compute_D(...)` / `A = compute_A(...)` / `three_case = apply_three_case_rule(D, A)`                          |
| `runners/run_c4_decisions_lc322.py`                           | 137-144  | `b1_sweep = run_sweep_aggregate(...)` / `c_genuine_sweep = run_sweep_aggregate(...)`                              |
| `runners/run_c4_decisions_lc322.py`                           | 161      | `gap = cg_e["normalized_utility"] - b1_e["normalized_utility"]`                                                   |
| `runners/run_c4_decisions_lc322.py`                           | 219      | `OUTPUT_PATH.write_text(json.dumps(output, indent=2), ...)`                                                       |
| `doctor/adversarial/problem_class_config.py`                  | 156-157  | `_fail_count_policy`: ACCEPT if obs_fails == 0 else REJECT                                                        |
| `doctor/adversarial/problem_class_config.py`                  | 172-201  | `_c_genuine_policy`: ACCEPT if 0 failures OR all failures share one probe_family                                  |
| `doctor/adversarial/problem_class_config.py`                  | 298-311  | `LC322_ESTIMATOR_POLICIES` mapping                                                                                |
| `doctor/adversarial/problem_class_config.py`                  | 651-667  | `ProblemClassConfig` dataclass (6 adapter slots)                                                                  |
| `doctor/adversarial/problem_class_config.py`                  | 670-705  | `get_problem_class_config` factory                                                                                |
| `doctor/asymmetric_cost.py`                                   | 12-34    | `compute_cost`: per-decision cost                                                                                 |
| `doctor/asymmetric_cost.py`                                   | 37-60    | `compute_raw_cost`: mean cost over population                                                                     |
| `doctor/identity_resolution.py`                               | 34-47    | `compute_D`: disagreement support size                                                                            |
| `doctor/identity_resolution.py`                               | 50-60    | `compute_A`: advantage asymmetry                                                                                  |
| `data/c4_decisions_lc322.json`                                | 263      | `"gap": 3.1333333333333333`                                                                                       |
| `data/c4_decisions_lc322.json`                                | 269      | `"best_gap": 3.1333333333333333`                                                                                  |
| `data/c4_decisions_lc322.json`                                | 272      | `"reason": "PASS: utility gap > 0.1 at lambda=50, D=8 > 0"`                                                       |
| `data/midweather_fingerprint_lc322.json`                      | 165, 286 | pack_source=reconstructed_stub, 11/19 split                                                                       |
| `data/midweather_fingerprint_lc322_real_claude_sonnet_4.json` | 17, 289  | pack_source=hand_curated_real, 16/14 split                                                                        |

---

## 7. Chronological Execution Log

One entry per run. Raw numbers only. No arrows between runs.

### Regime Tags

| Tag     | Contract | Meaning                                      |
|---------|----------|----------------------------------------------|
| [C4]    | C-4      | Decision-utility gate                        |
| [C5]    | C-5      | Perturbation survival                        |
| [FP]    | FP       | Fingerprint clean gate (B0-B6 + C estimator) |
| [LC743] | LC743    | Different problem class, different oracle    |
| [META]  | —        | Paper/meta (no execution)                    |

### Log

| #                   | Run                        | Regime  | Trigger                       | Input                                 | Output                             | Artifact          | Commit  |
|---------------------|----------------------------|---------|-------------------------------|---------------------------------------|------------------------------------|-------------------|---------|
| 1                   | PhotoRec recovery          | [META]  | disk failure                  | 593 files recovered                   | adversarial layer intact           | nothing           | 61a398e |
| 2                   | Phase-c4 original          | [C4]    | spec frozen                   | 30 LLM-generated solvers (original)   | PASS, gap=8.3 at λ=50              | solver file       | 50d33e5 |
|                     |                            |         |                               |                                       | B1: WA=0/WR=3                      | wrappers          |         |
|                     |                            |         |                               |                                       | C_genuine: WA=6/WR=1               |                   |         |
|                     |                            |         |                               |                                       | D=8, A=50                          |                   |         |
|                     |                            |         |                               |                                       | verdict: DIRECTIONAL_SUPERIORITY   |                   |         |
| 3                   | Midweather fingerprint     | [FP]    | gate protocol                 | 30 solvers (reconstructed_stub)       | 11/19 split                        | fingerprint JSON  | c3db242 |
|                     | (reconstructed)            |         |                               | pack_source=reconstructed_stub        | FAIL, B4 degenerate all-reject     | (data/)           |         |
| 4                   | Midweather fingerprint     | [FP]    | gate protocol                 | 30 solvers (hand_curated_real)        | 16/14 split                        | fingerprint JSON  | 5f92108 |
| (hand-curated real) |                            |         | pack_source=hand_curated_real | FAIL, B4 degenerate all-reject        | (data/)                            |                   |
| 5                   | LC3946 C-4                 | [C4]    | spec frozen                   | 30 solvers, LC3946 population         | C_genuine: decision_loss=0.0       | LC3946 result     | 08890e8 |
|                     |                            |         |                               |                                       | B1: decision_loss=1.0              | (data/)           |         |
|                     |                            |         |                               |                                       | gap=1.0                            |                   |         |
| 6                   | LC3946 C-5                 | [C5]    | spec frozen                   | 11 perturbation types                 | PARTIALLY_SURVIVES 10/11           | C-5 results       | 1ad7faf |
|                     | NOTE: different contract   |         |                               | different oracle semantics            | P3e collapse confirmed             | (data/)           |         |
| 7                   | LC743 C-4 (original)       | [LC743] | spec frozen                   | 30 solvers, LC743 population          | PASS gap=5                         | LC743 result      | 45a557f |
|                     | NOTE: different problem    |         |                               | different oracle semantics            | C_genuine loss=0 vs B1 loss=5      | (data/)           |         |
| 8                   | LC743 C-4 (frozen rerun)   | [LC743] | protocol frozen               | 30 solvers, LC743 population          | FAIL gap=0                         | LC743 result      | ce586cf |
|                     | NOTE: contamination events |         |                               | 12/12 split                           | threshold=0.05                     | (data/)           |         |
| 9                   | LC322-v2 solver rerun      | [C4]    | user authorized               | 30 GPT-generated solvers              | 15/15 split                        | solver file       | b344c4a |
|                     | (frozen)                   |         | (Foued)                       | F1×5/F2×10/F3×11/F4×4 prior           | pack_source=llm_generated          | (doctor/solvers/) |         |
| 10                  | LC322-v2 first C-4 run     | [C4]    | user authorized               | solver file + wrappers                | Tainted (modified solver)          | reverted          | 8051044 |
|                     | (tainted)                  |         | (Foued)                       | same as #9                            | + modified wrappers                | (8051044)         |         |
| 11                  | solve_10 termination guard | [C4]    | user authorized               | amount > 40 → return -1               | Guard added to solve_10            | solver file       | 6c897c0 |
|                     | (protocol deviation)       |         | (Foued)                       | in lc_322_solvers.py                  |                                    |                   |         |
| 12                  | LC322-v2 fingerprint run   | [FP]    | user authorized               | 30 GPT solvers + guard                | 15/15 split                        | fingerprint JSON  | e8b0075 |
|                     | (clean)                    |         | (Foued)                       | pack_source=llm_generated             | FAIL, B4 degenerate                | (data/)           |         |
| 13                  | LC322-v2 C-4 gate          | [C4]    | user authorized               | fingerprint JSON from #12             | PASS, gap=3.13 at λ=50             | C-4 results       | e8b0075 |
|                     | (clean)                    |         | (Foued)                       | + C-4 freeze                          | B1: WA=0/WR=3                      | (data/)           |         |
|                     |                            |         |                               |                                       | C_genuine: WA=6/WR=1               |                   |         |
|                     |                            |         |                               |                                       | D=8, A=50                          |                   |         |
|                     |                            |         |                               |                                       | verdict: DIRECTIONAL_SUPERIORITY   |                   |         |
| 14                  | Paper rewrites             | [META]  | user authorized               | doctor_bimaristan_scientific_paper.md | Abstract, Limitations, Conclusion  | paper             | 18d886d |
|                     | (Limitations)              |         | (Foued)                       |                                       | rewritten with conditional framing |                   |         |
|                     | (Abstract)                 |         |                               |                                       | No universality claim              |                   |         |
|                     | (Conclusion)               |         |                               |                                       |                                    |                   |         |

### Cross-Regime Comparability Note

- Runs #2, #5, #9, #10, #11, #13 share the same C-4 evaluation contract.
- Runs #3, #4, #12 share the FP fingerprint gate contract.
- Run #6 (LC3946 C-5) uses a DIFFERENT contract: perturbation survival, not utility.
- Runs #7, #8 (LC743) use a DIFFERENT contract: different problem, different oracle.
- Cross-regime comparisons (e.g. LC322 gap vs LC3946 gap) are NOT identically contracted.

---

## 8. State Synchronization Contract (SSC-v1)

### 8.0 Purpose

Define a deterministic protocol for synchronizing:

- Source state (commits, files, logs)
- Canonical graph G
- Projections (G_static, G_runtime, G_provenance)
- Derived artifacts (claims, diagrams, papers)
- Conversational memory pointers

**Core Invariant:** G is always reconstructible from a declared HEAD without relying on mutable memory.

### 8.1 State Layers (Immutable Hierarchy)

| Layer  | Name                 | Contents                                                   | Constraint                                                              |
|--------|----------------------|------------------------------------------------------------|-------------------------------------------------------------------------|
| **L0** | Source Layer         | Git commits, source code, `/data` artifacts, test fixtures | Immutable except via commit history                                     |
| **L1** | Derived Graph Layer  | G = Build(Source_L0, ExtractionRules, Schema)              | Pure function of L0 + versioned extraction rules; no manual edits       |
| **L2** | Projection Layer     | G_static, G_runtime, G_provenance                          | Recomputed, never stored as authoritative state                         |
| **L3** | Interpretation Layer | Claim Map, paper text, execution summaries                 | Must reference G via explicit node/edge IDs; cannot introduce new nodes |
| **L4** | Ephemeral Interface  | Memory/chat state                                          | Only HEAD_commit, G_version_id, SSC_version; no nodes/edges/claims      |

### 8.2 Synchronization Rule

At any time:

```
G(version) = Rebuild(L0 at HEAD(version), ExtractionRules(version))
Memory_state ⊂ {HEAD_commit, version pointers}
```

### 8.3 Update Protocol (Strict Pipeline)

| Step | Action                 | Validation                                          | Failure       |
|------|------------------------|-----------------------------------------------------|---------------|
| 1    | `SET_HEAD(commit)`     | Must match git state                                | HALT          |
| 2    | `REBUILD_GRAPH`        | Node type, edge type, orphan edge, contract linkage | HALT          |
| 3    | `DERIVE_PROJECTIONS`   | Deterministic filter/closure                        | —             |
| 4    | `VALIDATE_G`           | Provenance paths, contract binding, no orphan edges | MARK UNSTABLE |
| 5    | `SYNC_MEMORY_POINTERS` | Only HEAD_commit, G_version_id, SSC_version         | —             |

### 8.4 Execution Event Ingestion Rule

A "run" is accepted only if:

```
Run_event ∈ L0 artifacts OR reproducible from L0
```

Each run becomes an ExecutionInstance node:

```
ExecutionInstance
  PRODUCES → DataArtifact
  CONSUMES → InputArtifacts
  DERIVES_FROM → PreviousArtifacts
  CONFIGURES → Contract
```

### 8.5 Claim Validity Rule

A claim is valid only if there exists a path:

```
Claim → ExecutionInstance → DataArtifact → Runner → Source
```

If not → Claim is DISPUTED by definition.

### 8.6 Cross-Version Rule

Comparisons `G(v1) vs G(v2)` are valid only if:

- Same schema version, AND
- Same extraction rules version OR explicitly mapped transformation function exists

Otherwise → comparison is "UNNORMALIZED" and invalid for inference.

### 8.7 Failure Modes

| ID | Violation               | Description                   | Impact              |
|----|-------------------------|-------------------------------|---------------------|
| F1 | Memory drift            | Memory stores graph elements  | Invalidates L3 only |
| F2 | Implicit reconstruction | G assumed without rebuild     | Invalidates L3 only |
| F3 | Cross-contract leakage  | Un-normalized comparison      | Invalidates L3 only |
| F4 | Orphan claim injection  | Claim without provenance path | Invalidates L3 only |
| F5 | Runtime-source mismatch | Run not traceable to L0       | Invalidates L3 only |

**Note:** F1–F5 invalidate interpretation layer (L3) only, not L0 (source).

### 8.8 Minimal Interface

Allowed commands only:

- `SET_HEAD(commit)`
- `REBUILD_GRAPH`
- `DERIVE_PROJECTIONS`
- `VALIDATE_G`
- `SYNC_MEMORY_POINTERS`

Nothing else modifies state.

### 8.9 Design Principle

> Memory is not a database. Memory is a pointer registry.
> G is not stored. G is reconstructed.

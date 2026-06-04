# Week 3 CLI Scope

**Goal:** Package the generalized kernel as `doctor-certify` with four subcommands, deterministic exit codes, and explicit path-flag precedence. Ship a CLI that runs LC322 and LC45 with B0-B6 today; defer C design and per-problem-class bimaristan layers to Week 4+.

**Out of scope (Week 4+):** C estimator design, LC45 bimaristan layer (`LC45OracleEvaluator`, `LC45_SYMBOL_REGISTRY`, predicate evaluation), the bimaristan-as-C-features interface, signature changes to kernel internals (`midweather_fingerprint_features.py`), schema evolution beyond additive fields.

**In scope (Week 3):** `pyproject.toml` with `doctor-certify` console script; a thin `doctor/adversarial/cli.py` that wires the four subcommands; the runner refactored to be importable (not re-implemented); exit code policy; consistency check between `--problem-class` and the resolved freeze's `freeze_id`; `docs/REPRODUCE.md` updated to point at the CLI.

---

## 1. Subcommand set

Four subcommands. `list` replaces the earlier `list-problem-classes` for brevity (matches the `doctor-certify list` framing).

| Subcommand | Purpose | Output | Exit codes |
|---|---|---|---|
| `run` | Execute the protocol for a problem class; write the result JSON | Verdict, reason, per-estimator table to **stdout**; result JSON to `--output` path | `0` PASS, `1` FAIL, `2` REFUSED, `3` ERROR |
| `validate-freeze` | Run the 7 freeze validators against a freeze file | Per-validator pass/fail to **stdout** | `0` all pass, `2` any fail, `3` ERROR |
| `validate-manifest` | Run `assert_valid_seval_manifest` + freeze-tie check | Pass/fail + reasons to **stdout** | `0` valid, `2` invalid, `3` ERROR |
| `list` | List registered problem classes and their 6 adapter slot fills | Tabular output (problem_class, slot, value) to **stdout** | `0` always |

All four subcommands accept `--help`. `run` and `validate-*` accept `--problem-class` (default `lc322`); the path flags under `run` are `--freeze`, `--probe-index`, `--seval-manifest`, `--solvers-dir`, `--output`. `list` takes no required args.

`validate-freeze` and `validate-manifest` exist for CI hooks: validate artifacts before the expensive `run`. They never invoke any solver.

`list` is the "what problem classes does this kernel know about" command. It prints, for each registered problem_class, the 6 adapter slot values (`oracle`, `probe_to_solver_input`, `solver_entry_point`, `estimator_names` + `estimator_policies`, `fingerprint_axes`, `raw_tensor_encoder`) and marks which slots come from a problem-specific implementation vs the LC322 default. This is the Week 4+ checklist: an LC45 bimaristan port fills in the slots that are still marked "LC322 default".

---

## 2. Exit code policy

Four codes. Stable across all subcommands.

| Code | Meaning | When | Distinguishing message format (stderr) |
|---|---|---|---|
| `0` | PASS | `run` completed; verdict is `PASS` | (none — verdict printed in run output) |
| `1` | FAIL | `run` completed; verdict is `FAIL` (degenerate target, C-not-beating-baselines, etc.) | (none — verdict printed in run output) |
| `2` | REFUSED | The protocol's guards rejected the run before any computation | `REFUSED: <guard>: <reason>` (one line per refusal reason) |
| `3` | ERROR | Unexpected failure (file not found, JSON parse error, unhandled exception, freeze_id mismatch) | `ERROR: <exception type>: <message>` |

**REFUSED is precisely defined:** it is the union of (a) `assert_valid_seval_manifest` raising `SevalManifestValidationError` (manifest schema + freeze tie + certification), and (b) `clean_run_refusal_reasons` returning a non-empty list (the 7 freeze validators). Both are protocol-level rejections — the run was not allowed to start. The CLI distinguishes them in the message:

- Manifest certification failure: `REFUSED: manifest_certification: <reasons>`
- Freeze-validator failure: `REFUSED: freeze_validation: <reasons>`

This is the CI hook:

```sh
doctor-certify run --problem-class=lc45
case $? in
  0) echo "PASS" ;;
  1) echo "FAIL (expected — B0-B6 only, no C)" ;;
  2) echo "REFUSED — guards blocked the run; check stderr" ;;
  3) echo "ERROR — bug; check stderr" ;;
esac
```

`validate-freeze` and `validate-manifest` also exit `2` on guard failure (their entire job is to surface guard failures). `list` always exits `0`.

---

## 3. Path-flag vs config precedence

**Rule: flag overrides config; config fills in missing paths. Partial override is allowed.**

For `run`:

- `--problem-class=lc45` selects the LC45 defaults from `_paths_for("lc45")`: freeze, probe_index, seval_manifest, solvers_dir, result.
- Each of the five path flags (`--freeze`, `--probe-index`, `--seval-manifest`, `--solvers-dir`, `--output`) overrides its corresponding default.
- Any subset may be passed. The config fills in the rest. This is the most common case: `doctor-certify run --problem-class=lc45` uses all defaults; `doctor-certify run --problem-class=lc45 --freeze=/tmp/lc45_freeze.json` overrides only the freeze.
- The axis-set cross-check (probe_index's `axis_set` must equal the config's `fingerprint_axes`) is preserved. On mismatch: exit `3`.

**Consistency check (the partial-override bug guard):**

The freeze's `freeze_id` is the authoritative source of truth for the problem class. If `--problem-class=lc45` is passed and the resolved freeze's `freeze_id` does not start with `midweather_fingerprint_lc45_`, the CLI exits `3` with:

```
ERROR: freeze_id_mismatch: freeze declares <freeze_id>, problem_class is lc45
```

This catches the "user passed `--problem-class=lc45` but pointed at the LC322 freeze" bug, which would otherwise silently use the wrong freeze's `observation_budget` and `weakest_baseline_config` while running the LC45 estimators. The check is symmetric: `--problem-class=lc322` requires the freeze's `freeze_id` to start with `midweather_fingerprint_lc322_`.

**No flag → config defaults only.** `doctor-certify run --problem-class=lc45` is the canonical invocation. The LC45 result JSON writes to `data/midweather_fingerprint_lc45.json` (the config default) unless `--output` overrides.

**Symmetric for `validate-freeze` and `validate-manifest`:** they take `--freeze` and `--seval-manifest` respectively, plus `--problem-class` for the default path lookup. No consistency check on these (they only validate one artifact, not the cross-product).

---

## Deliverables (Week 3, in commit order)

1. `docs/CLI_SCOPE.md` (this file, committed as the surface declaration)
2. `pyproject.toml` + `doctor-certify` console script
3. `doctor/adversarial/cli.py` with the four subcommands
4. Refactor `runners/run_midweather_fingerprint_lc322.py` to be importable; `cli.py` calls into it (no logic duplication)
5. Update `docs/REPRODUCE.md` to point at the CLI (`doctor-certify run --problem-class=lc322` etc.)
6. Tests for the CLI: each subcommand exits the declared code on a fixture

Each commit is a single layer. No combined commits. No C design, no bimaristan port, no signature changes to kernel internals.

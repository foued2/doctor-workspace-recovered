# REPRODUCE.md — Midweather-Fingerprint-Gate Clean-Run (LC322 + LC45)

This document is the step-by-step recipe to reproduce the run that produced
`data/midweather_fingerprint_lc322.json` (and `data/midweather_fingerprint_lc45.json`
for the B0-B6-only LC45 port). Every artifact is SHA-locked in
`ARTIFACT_MANIFEST.lock`; each protocol freeze is SHA-locked in its own
`MIDWEATHER_FINGERPRINT_GATE_*_FREEZE.json`.

## Prerequisites

- Python 3.14 (any Python that supports PEP 604 union syntax and the rest of the source works)
- A working tree at the commit recorded in `ARTIFACT_MANIFEST.lock:_meta.locked_at`
- No environment variables or secret keys required
- Optional: `pip install -e .` to expose the `doctor-certify` console script;
  the steps below work either via the console script or via `python -m doctor.adversarial.cli`

## Using the CLI

The protocol ships as a CLI with four subcommands. After `pip install -e .`,
invoke as `doctor-certify ...`; before install, invoke as
`py -m doctor.adversarial.cli ...` (or `python -m` on non-Windows).

| Subcommand | Purpose | Exit codes |
|---|---|---|
| `doctor-certify list` | Print the 6 adapter slot fills for each registered problem class | `0` always |
| `doctor-certify validate-freeze --freeze=PATH` | Run the 7 freeze validators against a freeze file | `0` all pass, `2` any fail, `3` ERROR |
| `doctor-certify validate-manifest --seval-manifest=PATH --freeze=PATH` | Schema + freeze tie + certification | `0` valid, `2` invalid, `3` ERROR |
| `doctor-certify run --problem-class=lc322` (or `lc45`) | Execute the protocol; write the result JSON | `0` PASS, `1` FAIL, `2` REFUSED, `3` ERROR |

The exit code policy is stable across all subcommands. See `docs/CLI_SCOPE.md`
for the full surface declaration and the `REFUSED: <guard>: <reason>` vs
`ERROR: <exception>: <message>` stderr format.

## Step 1: Verify the lockfile

```
python -c "import json, hashlib
m = json.load(open('ARTIFACT_MANIFEST.lock'))
ok = True
for a in m['artifacts']:
    p = open(a['path'], 'rb').read()
    if a.get('exclude_fields'):
        d = json.loads(p)
        for f in a['exclude_fields']:
            d.pop(f, None)
        content = json.dumps(d, indent=2, ensure_ascii=False).encode('utf-8')
    else:
        content = p
    if hashlib.sha256(content).hexdigest() != a['sha256']:
        print('MISMATCH', a['path']); ok = False
print('lockfile', 'OK' if ok else 'BROKEN')"
```

Expected: `lockfile OK`. If mismatches, the working tree is dirty; do not proceed.

Note: result JSON entries (`data/midweather_fingerprint_*.json`) carry an
`exclude_fields: ["wallclock_seconds"]` directive. The verifier strips that
field before SHA computation, so the lockfile SHA is stable across runs even
though `wallclock_seconds` itself is timing-dependent. The lockfile holds
56 entries (was 40 before the LC45 port; see `_meta.manifest_solver_sha_consistency`
for the cross-check against the LC322 seval_manifest).

## Step 2: Run the protocol tests (40 tests, all must pass)

```
python -m pytest -q tests/test_midweather_fingerprint.py
```

Expected: `40 passed in <1s`. The 40 tests are the protocol-level contract.
If any test fails, the protocol is broken; do not interpret the result JSON.

## Step 3: Verify the freeze validates (via the CLI)

```
doctor-certify validate-freeze --freeze=MIDWEATHER_FINGERPRINT_GATE_FREEZE.json
```

Expected: `PASS: all freeze validators passed` and exit code `0`. Any non-empty
`REFUSED: freeze_validation: <reason>` line is a freeze-validation failure; the
runner would refuse to run.

To validate the manifest separately (a CI hook before the expensive run):

```
doctor-certify validate-manifest \
  --seval-manifest=data/midweather_fingerprint_lc322_seval_manifest.json \
  --freeze=MIDWEATHER_FINGERPRINT_GATE_FREEZE.json
```

Expected: `PASS: manifest is valid (schema + freeze tie + certification)` and
exit code `0`.

## Step 4: Run the protocol (via the CLI)

```
doctor-certify run --problem-class=lc322
```

Expected output (lines truncated):

```
Wrote C:\Users\pakla\PycharmProjects\doctor-workspace-recovered\data\midweather_fingerprint_lc322.json

Decision: FAIL
Reason:   degenerate: all-reject in B4_raw_full_tensor

Ground truth: 11 good / 19 bad

Per-estimator table:
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

Process exit code: `1` (FAIL). The CLI's run subcommand propagates the verdict
via the exit code; CI can branch on it (`0=PASS, 1=FAIL, 2=REFUSED, 3=ERROR`).

If you have not run `pip install -e .`, the equivalent invocation is
`py -m doctor.adversarial.cli run --problem-class=lc322` (the CLI adds the
project root to `sys.path` at startup so the `runners/` package is importable).

Wallclock: <1s on any modern machine.

## Step 5: Verify the result JSON is bit-for-bit reproducible

```
python -c "
import hashlib
actual = hashlib.sha256(open('data/midweather_fingerprint_lc322.json', 'rb').read()).hexdigest()
expected = '1400828193bbd51795d3ad454d5b1ec32991a8505b2ae94bf91323ef783c1f2d'
print('result JSON SHA:', actual)
print('expected     SHA:', expected)
print('match:', actual == expected)
"
```

Expected: `match: True`. The result JSON is SHA-pinned; if the actual SHA
differs, the protocol has drifted (some solver, manifest, or freeze file
changed). The lockfile + freeze's frozen_files cross-check would also catch
this.

## Step 6: Re-derive the lockfile (optional sanity check)

```
python C:\Users\pakla\AppData\Local\Temp\opencode\generate_artifact_manifest.py
```

This regenerates `ARTIFACT_MANIFEST.lock` from the working tree. Expected:
`manifest solver sha consistency: ok` and 39 artifacts (9 named + 30 solver files).

## LC45 (B0-B6 port)

The LC45 port runs the same generalized kernel against the LC45 freeze, probe
index, and seval manifest. It uses estimators B0-B6 only (no C); per the
kernel contract (see `docs/GENERALIZATION_CONTRACT.md:§7 item 6`), the verdict
degenerates to FAIL when C is absent.

```
doctor-certify list
```

lists `lc45` alongside `lc322`, showing the 6 adapter slot fills and that
LC45 has 7 estimators (B0-B6) vs LC322's 8 (B0-B6 + C_structured_fingerprint).

```
doctor-certify run --problem-class=lc45
```

Expected output (lines truncated):

```
Wrote C:\Users\pakla\PycharmProjects\doctor-workspace-recovered\data\midweather_fingerprint_lc45.json

Decision: FAIL
Reason:   degenerate: all-reject in B4_raw_full_tensor

Ground truth: 1 good / 9 bad

Per-estimator table:
estimator                              loss   WA   WR  acc_rate   RMSE   degenerate
B0_prior                                9.0    9    0     1.000  0.617   all-ACCEPT
B1_count                                0.0    0    0     0.100  0.477
B2_calibrated_count                     0.0    0    0     0.100  0.477
B3_raw_pf_vector                        0.0    0    0     0.100  0.477
B4_raw_full_tensor                      1.0    0    1     0.000  0.572   all-REJECT
B5_nearest_neighbor_raw_tensor          9.0    9    0     1.000  0.617   all-ACCEPT
B6_regularized_raw_tensor               9.0    9    0     1.000  0.617   all-ACCEPT
```

Process exit code: `1` (FAIL). The 1 good solver is the BFS-survivor
(`solver_001`); solvers 2-10 fail on various held-out probes (0.2-1.0 fail rate).

The LC45 freeze, probe index, and seval manifest are at:
- `MIDWEATHER_FINGERPRINT_GATE_LC45_FREEZE.json` (18 frozen files)
- `data/midweather_fingerprint_lc45_probe_index.json` (30 probes, 5/manifold, 15/15 split)
- `data/midweather_fingerprint_lc45_seval_manifest.json` (10 LC45 candidates, pack_source=external_baseline)

To validate the LC45 artifacts before running:

```
doctor-certify validate-freeze --freeze=MIDWEATHER_FINGERPRINT_GATE_LC45_FREEZE.json
doctor-certify validate-manifest \
  --seval-manifest=data/midweather_fingerprint_lc45_seval_manifest.json \
  --freeze=MIDWEATHER_FINGERPRINT_GATE_LC45_FREEZE.json
```

A consistency check fires if the freeze's `freeze_id` prefix does not match
`--problem-class` (e.g., `--problem-class=lc45` with the LC322 freeze): the
CLI exits `3` with `freeze_id_mismatch: freeze declares '<lc322 id>',
problem_class is 'lc45'`. This catches the "wrong freeze for the wrong
problem class" bug.

## LC322 Real Benchmark (hand-curated)

The real benchmark runs the same protocol against a 30-solver hand-curated pack
(10 correct + 20 buggy, spanning 7 bug families). This pack is used in lieu of
real LLM completions (the `ANTHROPIC_API_KEY` was not set in the recovery
environment). See `docs/LC45_C_POLICY_FINDING.md` and the paper's "Real
Benchmark" section for the full design rationale.

The real benchmark uses a separate freeze and manifest:

```
doctor-certify validate-freeze --freeze=MIDWEATHER_FINGERPRINT_GATE_LC322_REAL_FREEZE.json
doctor-certify validate-manifest \
  --seval-manifest=data/midweather_fingerprint_lc322_real_claude_sonnet_4_seval_manifest.json \
  --freeze=MIDWEATHER_FINGERPRINT_GATE_LC322_REAL_FREEZE.json
```

To run the real benchmark (this invokes the same kernel with a different
freeze/manifest pair; the runner picks paths from the freeze's freeze_id
prefix or from explicit `--freeze` / `--seval-manifest` flags):

```
py -m doctor.adversarial.cli run \
  --freeze=MIDWEATHER_FINGERPRINT_GATE_LC322_REAL_FREEZE.json \
  --seval-manifest=data/midweather_fingerprint_lc322_real_claude_sonnet_4_seval_manifest.json \
  --output=data/midweather_fingerprint_lc322_real_claude_sonnet_4.json
```

Expected output (lines truncated):

```
Wrote data/midweather_fingerprint_lc322_real_claude_sonnet_4.json

Decision: FAIL
Reason:   degenerate: all-reject in B4_raw_full_tensor

Ground truth: 16 good / 14 bad
```

Process exit code: `1` (FAIL). The 30 solvers, manifest, and result JSON are
all in the repo and SHA-locked.

## LC45 C Feature Audit (research artifact)

The LC45 C feature audit runs all 10 LC45 solvers on all 30 probes and
computes the 6 features from `lc45_raw_tensor_encoder` for each solver. The
result is a 10x6 feature table written to `data/lc45_c_feature_audit.json`.
This is a research artifact, not a protocol artifact — it does not go in the
freeze.

The audit is run by a temp script (`C:\Users\pakla\AppData\Local\Temp\opencode\lc45_feature_audit.py`).
It produces the feature table + separation analysis. The finding (C cannot
differentiate from B1 on the LC45 population) is documented in
`docs/LC45_C_POLICY_FINDING.md` with the full 10x6 table and per-feature gap
analysis.

## What is NOT reproduced by this recipe

- The stub pack generation script (`generate_stub_solvers.py` in temp dir) is not in the repo; it is a one-shot script. The 30 solver files at `experiments/frozen_taxonomy_lc322/solvers/` ARE in the repo, and their SHAs are pinned in both the manifest and the lockfile.
- The held-out failure rate computation (`compute_heldout.py` in temp dir) is also not in the repo; it was a one-shot computation that wrote the per-solver truth labels into the result JSON at runner-time.
- The freeze file's `_provenance.field_provenance` documents which fields were PATCHED during reconstruction (e.g., `observation_budget.observed_probe_ids` was filled in from the probe_index JSON, not from the paper). The `clean_run_refusal_reasons` validator does not check `_provenance`; it checks the structural fields. The provenance is documentary.

## What "FAIL" means in this protocol

The decision is FAIL because `decide_accept_reject` in
`doctor/adversarial/midweather_fingerprint_features.py:344-349` returns
`("FAIL", "degenerate: all-reject in B4_raw_full_tensor")`. The B4 estimator
is structurally an all-reject policy (B4 = "raw full tensor" baseline, which
the stub pack returns "REJECT" for every solver). The function's
unconditional all-reject check fires before the C-vs-baseline comparison
is reached. This is **intentional policy**, not a bug — see
`findings/FINDINGS_MIDWEATHER_FINGERPRINT_LC322.md:§1` for the test
`test_all_reject_cannot_pass` evidence that code is authoritative over
the paper's prose at `:605`.

The verdict FAIL is **expected and consistent with the paper's central
claim** (Stage 3 fails). The mechanism is **not** the one the paper
describes ("C ties on decision_loss"); it is "B4 is all-reject". Both
explanations end in FAIL; the actual code returns the second.

## Pack provenance disclosure

The 30 solver files in the manifest use `pack_source: "reconstructed_stub"`.
This is **not** a recovered external blind pack. It is a deterministic stub
generated to satisfy the protocol's structural requirements (30 distinct
solvers, 6 strategy families, 30/30 DP-survivor pass, 9 buggy candidates
each fail on ≥2 axes). The `data/midweather_fingerprint_lc322.json:reconstruction_disclosure`
block records the paper's claimed 27/3 split vs the actual 11/19 split.
A recovered original external blind pack, if it surfaces, would use the
same manifest schema with `pack_source: "external_blind_pack"` and
different `certified_clean` provenance.

# REPRODUCE.md — Midweather-Fingerprint-Gate Clean-Run (LC322)

This document is the step-by-step recipe to reproduce the run that produced
`data/midweather_fingerprint_lc322.json`. Every artifact is SHA-locked in
`ARTIFACT_MANIFEST.lock`; the protocol freeze is SHA-locked in
`MIDWEATHER_FINGERPRINT_GATE_FREEZE.json`.

## Prerequisites

- Python 3.14 (any Python that supports PEP 604 union syntax and the rest of the source works)
- A working tree at the commit recorded in `ARTIFACT_MANIFEST.lock:_meta.locked_at`
- No environment variables or secret keys required

## Step 1: Verify the lockfile

```
python -c "import json, hashlib; m = json.load(open('ARTIFACT_MANIFEST.lock')); ok = True
for a in m['artifacts']:
    p = open(a['path'], 'rb').read()
    if hashlib.sha256(p).hexdigest() != a['sha256']:
        print('MISMATCH', a['path']); ok = False
print('lockfile', 'OK' if ok else 'BROKEN')"
```

Expected: `lockfile OK`. If mismatches, the working tree is dirty; do not proceed.

## Step 2: Run the protocol tests (39 tests, all must pass)

```
python -m pytest -q tests/test_midweather_fingerprint.py
```

Expected: `39 passed in <1s`. The 39 tests are the protocol-level contract
(see `tests/test_midweather_fingerprint.py:1-50` for the relocation provenance).
If any test fails, the protocol is broken; do not interpret the result JSON.

## Step 3: Verify the freeze validates

```
python -c "
import json, sys
from pathlib import Path
from doctor.adversarial.midweather_fingerprint_features import clean_run_refusal_reasons
freeze = json.loads(Path('MIDWEATHER_FINGERPRINT_GATE_FREEZE.json').read_text())
manifest = json.loads(Path('data/midweather_fingerprint_lc322_seval_manifest.json').read_text())
probe_index = json.loads(Path('data/midweather_fingerprint_lc322_probe_index.json').read_text())
ds = {'name': 'ACCEPT_REJECT', 'failure_threshold': 0.05, 'minimum_accept_rate': 0.2}
reasons = clean_run_refusal_reasons(
    seval_manifest=manifest, freeze=freeze, repo_root=Path('.'),
    decision_spec=ds, probe_index=probe_index, freeze_id=freeze['freeze_id'])
print('reasons:', reasons if reasons else '[] -- all 7 freeze validators pass')
"
```

Expected: `reasons: [] -- all 7 freeze validators pass`. Any non-empty list
is a freeze-validation failure; the runner will refuse to run.

## Step 4: Run the protocol

```
python runners/run_midweather_fingerprint_lc322.py
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

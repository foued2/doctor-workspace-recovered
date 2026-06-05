# Observer Dead Code Audit

**Date:** 2026-06-05
**Scope:** `doctor/adversarial/observer/`
**Status:** Dead code confirmed. No action taken. Project remains closed at `project-closure-001`.

## Summary

Eighteen files in `doctor/adversarial/observer/` are dead, broken, and unreachable.
They are remnants of the original PhotoRec sector recovery (commit `61a398e`,
"Doctor 1 recovered - foundation restored from PhotoRec sectors") and were never
reconstructed.

The canonical pipeline modules (`pipeline.py`, `registry_matcher.py`,
`agreement.py`, `problem_parser.py`, `spec_inferrer.py`, `checker_gen.py`,
`problem_registry.py`, `evidence.py`) were properly reconstructed in commit
`777a2ac` from interface analysis. The `observer/` directory was missed by
that reconstruction pass.

## Directory contents (18 files)

```
doctor/adversarial/observer/
    __init__.py
    artifact_schema.py            artifact_schema_1.py            artifact_schema_2.py
    extractor_common.py           extractor_common_1.py           extractor_common_2.py
    extractors.py                 extractors_1.py                 extractors_2.py
    relation_detector.py          relation_detector_1.py          relation_detector_2.py
    trajectory.py                 trajectory_1.py                 trajectory_2.py
                                  trajectory_3.py                 trajectory_4.py
                                  trajectory_5.py
```

Five file groups: `artifact_schema`, `extractor_common`, `extractors`,
`relation_detector`, `trajectory` (the last has six variants rather than three).

## Evidence of brokenness

All five canonical files (the ones without a `_N` suffix) contain self-imports
of names that are **not defined in the same file**. Every one of them fails at
import time:

```
ImportError: cannot import name 'DependencyDepth' from partially initialized
module 'doctor.adversarial.observer.artifact_schema' (most likely due to a
circular import)
```

The names referenced in the self-imports are defined in the `_1.py` / `_2.py`
variants only. The canonical files are empty shells. They were never meant to
be loaded; the variants were the actual content.

| Canonical file           | Self-imports names that are not defined in the file         |
|--------------------------|------------------------------------------------------------|
| `artifact_schema.py`     | `DependencyDepth, DivergenceKAxis, DivergenceProfile, DivergenceSignAxis, LocalityClass, ManifoldArtifact, PerturbationEvent, PerturbationStability, RejectionTopology` |
| `extractor_common.py`    | `ARTIFACT_ROOT`                                            |
| `extractors.py`          | `lc11_extractor, lc45_extractor, ...` (8 names)            |
| `relation_detector.py`   | `load_artifacts, score_pair_trajectory`                    |
| `trajectory.py`          | `extract_trajectory, compare_trajectories`                 |

## Reachability

```
grep -r "doctor.adversarial.observer" tests/ runners/ docs/ scratch/
```

returns zero matches. No test, runner, CLI subcommand, or documentation file
references any of the 18 files. The 276-test suite passes without ever
loading them.

The only references to `doctor.adversarial.observer.*` outside the directory
itself are from inside the same dead-code subsystem (the variants importing
the canonical files), or from sibling dead code:

- `doctor/adversarial/lc128_ingestion_gate.py` (and variants `_4.py`, `_5.py`)
  import `doctor.adversarial.observer.trajectory` -- but those files
  themselves are also part of the recovery dump and have the same broken
  self-import pattern for `lc128_nums_reordering_perturbations`.

## Canonical variant map

If these files were ever to be revived (they are not), the most-complete
variants are:

| Group              | Most complete variant   | Notes                                                       |
|--------------------|-------------------------|-------------------------------------------------------------|
| `artifact_schema`  | `artifact_schema_2.py`  | Adds `scan_records` field, `DivergenceKAxis`, `DivergenceSignAxis`, and `_compute_divergence_k_axis` / `_compute_divergence_sign_axis` helpers. 457 lines vs 356 in `_1`. |
| `trajectory`       | `trajectory_5.py`       | `_1`/`_2` are one diagnostic variant; `_3`/`_4`/`_5` are another. The two clusters differ in scoring-axis stability checks vs verdict-path diagnostics. |
| `extractor_common` | `extractor_common_2.py` | `_1` and `_2` are near-identical; `_2` is marginally newer. |
| `extractors`       | `extractors_2.py`       | `_1` and `_2` are near-identical.                           |
| `relation_detector`| `relation_detector_2.py`| `_1` and `_2` are near-identical.                           |

The user-visible behaviour any of these files would have produced cannot be
inferred without substantial work (extracting the contract from the variant
that looks most "complete" and reconciling with the rest of the adversarial
subsystem that never called into them).

## Decision

Document only. No deletion, no refactor, no commit beyond this audit note.

Rationale:
- Zero behaviour change is already proven -- nothing in the project's tested
  surface reaches any of these 18 files.
- The project is sealed at tag `project-closure-001` (commit `5966c74`).
- Deletion would buy nothing except commit noise on a closed repo.
- The audit findings have documentary value: they confirm the recovery was
  complete where it mattered (the tested pipeline) and incomplete only where
  it did not (an unused observer subsystem).

If the observer subsystem is ever revived, this document is the starting
point -- the variant map above identifies where the actual content lives.

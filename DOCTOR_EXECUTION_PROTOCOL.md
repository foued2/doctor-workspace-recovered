# DOCTOR EXECUTION PROTOCOL (Claude Layer)
# Authored by: Claude (execution layer)
# Version: 1.0 — Session close 2026-06-02
# Read AFTER DOCTOR_OPERATING_PROTOCOL.md at the start of every session.
# GPT's file governs what can be CLAIMED. This file governs what can be DONE.

---

## 0. Layer Boundary

This document does not repeat or override DOCTOR_OPERATING_PROTOCOL.md.
That file owns: epistemological validity, confound rules, forbidden claims.
This file owns: what Minimax does when it has a terminal open and a codebase in front of it.

---

## 1. Read Before Touching

Before any edit, bash command, or implementation:

```
1. Read the target file completely.
2. Read every file it imports.
3. Verify the claim being acted on is in the actual file,
   not in a report about the file.
```

### Why this rule exists

The session that found a 3-node circular import (not 2-node as reported) exists because
a coordination message was trusted over the source file.

**The source is always ground truth. Reports are approximations.**

---

## 2. One Atomic Unit Per Move

Each move must satisfy:

```
- Single verifiable claim
- Single file change (or explicitly declared multi-file change)
- pytest run immediately after
- If tests drop: REVERT before proceeding
```

No move is complete until pytest output is in hand.
Declaring a move done before running tests is a forbidden state.

---

## 3. The Brute Force Is the Oracle — Protect It First

Any session touching ground truth functions
(`lc45_brute_force`, `lc322_brute_force`, any future `lcXXX_brute_force`) must:

```
1. Run the 5-case oracle manually BEFORE any edit.
2. Run it again AFTER.
3. If any case shifts: STOP. Do not proceed.
```

### Why this rule exists

The `lc45_brute_force` off-by-one (`>= len` instead of `>= len-1`) was silent,
correct-looking, and would have contaminated all 10 solver fail-rate calculations,
all bimaristan labels, and the fingerprint — if not caught before solver implementation.

**Oracle corruption is the highest-severity failure class in this system.**
It gets privileged protection above all other rules in this file.

---

## 4. Stale Reports Are MAX Moves in Disguise

When a coordination message (from GPT, from session notes, from memory) describes
system state, Minimax must:

```
1. grep verify every claimed file path
2. Run the claimed test count independently
3. Treat any discrepancy as a threat, not a typo
```

### Why this rule exists

The session where a status report claimed "132/132" when the actual state was "159/159"
is the canonical example. A Minimax player acting on stale state makes real edits
against a phantom model of the codebase.

The 10-solver population and 7 operator invariance tests existed on disk
while the report said they were "pending." The report was wrong. The disk was right.

---

## 5. Stub Discipline

Any stub introduced must satisfy exactly two properties:

```
A. Import chain resolves (the stub earns its existence by unblocking imports)
B. Incorrect use raises loudly (not silently returns empty / None / zero)
```

### Correct stub form

```python
class LC45:
    class _StubDescriptor:
        def __get__(self, obj, objtype=None):
            raise NotImplementedError(
                "LC45.invariant_families is a stub. "
                "Recover the real definition before running manifold analysis."
            )
    invariant_families = _StubDescriptor()
```

### Forbidden stub form

```python
class LC45:
    invariant_families = None   # FORBIDDEN — silent, non-raising
```

**`invariant_families = None` violates property B.**
Silent stubs are deferred bugs. They pass import checks and corrupt downstream analysis
without raising any error.

---

## 6. Locked Invariants Are Not Re-Litigated in Execution

The following are locked and must not be touched without explicit Foued approval:

```
- OB cascade in root_ratio.py
- PS cascade in lineage.py
- grammar_ceiling_* excluded from calibration
- _classify_gap() programmatic only
- POLICY 3 HARD CAP (no NON_WORKABLE without FAILED obligation)
- structural labels cannot drive verdicts
- PS106 → UNSUPPORTED only when Output section exists
- GG > PS > EXTRACTION_CEILING > POLICY (epistemic dependency order)
- POLICY admission: representation_stable AND verdict_level_disagreement
  AND no schema reinterpretation
```

If an edit would touch any of these:
**STOP. Surface to Foued before executing. Not after.**

---

## 7. Escalation Path (When to Stop and Ask)

Minimax stops and surfaces to Foued when ANY of the following occur:

```
- Test count drops for any reason
- A file claimed in a report does not exist at the claimed path
- An edit would touch a locked invariant
- GPT flags an epistemic violation in the framing
- The confound checklist (DOCTOR_OPERATING_PROTOCOL §4.3) returns UNKNOWN
  on any axis
- A brute force oracle value shifts after an edit
- A circular import is discovered that was not in the reported dependency graph
```

**Execution does not continue past these gates on its own authority.**

---

## 8. Commit Discipline

```
- No partial commits.
- Commit message must state: what changed, what test count was before, what it is after.
- Stub commits must be explicitly labeled: "stub — raises on use — NOT a real definition"
- Cleanup commits must be explicitly labeled: "cosmetic — no behavior change"
- If a commit closes an experiment branch, the message must say so explicitly.
```

### Example of a correct commit message

```
LC45: hardened LC45 stub — raises on invariant_families access — NOT a real definition
159/159 pass (was 159/159 before)
```

### Example of a forbidden commit message

```
fix import issue
```

---

## 9. Role Summary (One Line Each)

```
GPT:     Owns what is allowed to be CLAIMED
Claude:  Owns what is allowed to be EXECUTED
Minimax: Does the work under both constraints
Foued:   The only authority who can override a hard stop
```

No role overrides another.
GPT cannot authorize an execution move.
Claude cannot authorize an inference claim.
Minimax cannot authorize either.

---

## 10. Session Start Checklist

At the start of every session, before any action:

```
[ ] Read DOCTOR_OPERATING_PROTOCOL.md (GPT layer)
[ ] Read DOCTOR_EXECUTION_PROTOCOL.md (this file)
[ ] Run pytest — record baseline test count
[ ] Read session notes / memory — flag any stale state claims
[ ] Verify locked invariants have not been touched since last session
[ ] Identify the single next move
[ ] Ask Foued for approval if the move is non-trivial
```

---

## 11. Session End Checklist

At the end of every session, before closing:

```
[ ] pytest passes at same count or higher
[ ] No silent stubs introduced (all stubs raise on incorrect use)
[ ] Commit messages written correctly
[ ] Confound checklist filled (per DOCTOR_OPERATING_PROTOCOL §4)
[ ] Any hard stops encountered are documented, not silently resolved
[ ] Next move identified and surfaced to Foued
```

---

*End of DOCTOR_EXECUTION_PROTOCOL.md*

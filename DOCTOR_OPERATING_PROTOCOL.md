# DOCTOR OPERATING PROTOCOL (Minimax Agent Contract)
# Authored by: GPT (epistemological layer)
# Version: 1.0 — Session close 2026-06-02
# Read this file at the start of every session before taking any action.

---

## 0. System Stance (Non-Negotiable)

This system is a **measurement instrument over solver populations under defined operators**.
It is NOT a theory generator.

All outputs must be traceable to:
- code
- defined sampling procedure
- explicit projection function
- reproducible seed

No interpretation is allowed unless explicitly tagged as:

> *hypothesis (non-inferential)*

---

## 1. Ontology Discipline (Critical Constraint)

The following entities are **real only if explicitly constructed in code**:

- "collapse"
- "cluster"
- "equivalence class"
- "invariance"
- "operator sensitivity"

They do NOT exist as abstract objects.

They only exist as:

> relations induced by a projection function over a sampled solver ensemble

If the projection changes, the object disappears or changes.

---

## 2. Forbidden Moves (High-Risk Failure Modes)

Minimax must NOT:

### 2.1 Attribute causality across problems unless ALL of the following are controlled:
- solver set identical or explicitly mapped
- instance distribution normalized or explicitly matched
- projection definition identical

### 2.2 Generalize across LC45 → LC322 → LCXXX without:
- explicit factor isolation test
- OR declared confound acceptance

### 2.3 Treat P1/P2/P3/P4 as "truth layers"

They are:
> coarse-to-fine partitions, not epistemic hierarchy

### 2.4 Convert observational asymmetry into structural claims

Examples of forbidden statements:
- "greedy cluster exists"
- "operator fails"
- "problem is harder"
- "LC322 has higher P1-dissolution density than LC45"

The last example is specifically forbidden because "dissolution density" is not invariant
under solver set permutation. Merging or splitting BUGGY solvers changes the count arbitrarily.

---

## 3. Allowed Moves

### A. Implementation Correctness
- verify solvers against oracle
- enforce CI invariants
- ensure deterministic reproducibility

### B. Projection Mechanics
- compute P1–P4 signatures
- detect pairwise indistinguishability under projection
- report dissolved pairs WITHOUT interpretation

### C. Confound Tracking (Core Responsibility)

Every measurement must explicitly list:
- solver set dependence
- sampling distribution dependence
- projection definition dependence

If any is missing → result is invalid.

### D. Failure Classification (Safe Version)

Only this form is allowed:

> "Under projection Pk, solvers A and B are indistinguishable on sample S under seed X"

NOT:

> "A and B are equivalent"

---

## 4. Required Reporting Format

Every session output must end with:

### (1) Construction State
- what code exists
- what changed

### (2) Measurement State
- projections computed
- dissolved pairs
- stability across seeds (if checked)

### (3) Confound Checklist
- solver-set dependency: YES / NO / UNKNOWN
- distribution dependency: YES / NO / UNKNOWN
- projection dependency: YES / NO / UNKNOWN

### (4) Allowed Inference (if any)

Only if all confounds are controlled.

Otherwise:

> "No inference permitted."

---

## 5. Role Separation (Strict)

### Minimax
- executes code
- runs tests
- computes projection metrics
- detects invariants
- refuses uncontrolled generalization

### Claude
- stress tests interpretation
- identifies hidden equivalence assumptions
- detects ontology inflation risk

### GPT
- frames closure boundaries
- forces stop conditions
- blocks premature scaling narratives

**No role may override confound rules.**

---

## 6. Core Epistemic Principle

> "No cross-problem claim is valid unless factorization is explicit."

If you compare LC45 and LC322, you MUST decompose:
- solver basis
- instance distribution
- projection operator

before any statement about "difference".

Otherwise the comparison is undefined.

---

## 7. Hard Stop Rule

If Minimax detects:
- stable pattern
- BUT confound set is not fully controlled

Output:

> "Pattern exists but is non-identifiable under current construction."

And STOP. No interpretation layer is allowed beyond that.

---

## 8. What This System Is NOT

- NOT a research paper generator
- NOT a theory of computation
- NOT a general benchmarking framework
- NOT a model of "algorithm difficulty"

It is:

> a controlled projection instrument over solver ensembles

---

## 9. Minimal Mental Model

At all times:
- solvers = functions
- projections = quotient maps
- "structure" = equivalence under quotient
- everything else = contamination unless proven controlled

---

## 10. What Is Currently Established (Clean Invariants — as of 2026-06-02)

Only three claims survive both CI suites:

### 1. Monotonicity
P4 refines P3 refines P2 refines P1 in both LC45 and LC322.

### 2. Survivor Separability
The SURVIVOR remains distinguishable from all BUGGY solvers under P1 and P3
in both problems.

### 3. Finite-Sample Projection Stability
Under fixed seed sampling, each solver has a stable projection signature
(no observed stochastic drift at n=1000).

**Everything else is interpretive load.**

---

## 11. What Is NOT Established

- Cross-problem comparison of P1-count
- "P1-count drift" as a property of problem structure
- The scalar "1 vs 6" as a meaningful comparison
- Operator invariance as a measurable cross-problem object

These were explicitly demoted in the cleanup commit (2026-06-02, 159/159).

---

*End of DOCTOR_OPERATING_PROTOCOL.md*

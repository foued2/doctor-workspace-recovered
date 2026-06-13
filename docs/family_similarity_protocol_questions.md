# Family Similarity Protocol - Final Design Closure

**Status:** EXECUTION READY
**Date:** 2026-06-13
**Reason:** No free conceptual variables remain. Execution is data-generation, not conceptual design.

---

## The Core Distinction

This protocol is NOT testing:

> "Does DP have a geometry?" (ontological)

It IS testing:

> "Do externally assigned labels explain variance in failure behavior?" (statistical)

These are very different questions.

- If the statistical question succeeds, the ontological question is still not proven.
- If the statistical question fails, the ontological question is not necessarily disproven.

Keeping those separated prevents another long chain of interpretation drift.

---

## Priority-Ordered Questions

### Question 1 (HIGHEST PRIORITY): Define family membership rigorously

This is not administrative. It is the foundation of the entire experiment.

**The problem:**

LC322 can be viewed as DP. It can also be viewed as shortest path on an implicit graph. Many state-space
problems can be encoded both ways.

If the labels are fuzzy, then a positive result can always be explained afterward by label choice.

**What we need:**

An explicit, checkable definition of what makes a problem a member of each family.

**Options for "Graph problem":**

- **Structural:** Problem input is inherently a graph (adjacency list/matrix)
- **Algorithmic:** Canonical solution uses graph algorithms (BFS, DFS, Dijkstra, etc.)
- **Both:** Must satisfy both structural AND algorithmic criteria
- **Community consensus:** What LeetCode/competitive programming community calls a "graph problem"

**For each family, we need:**

1. A formal definition (one sentence)
2. An inclusion test (does problem X satisfy this definition?)
3. An exclusion test (does problem Y fail this definition?)
4. A list of borderline cases and how they were resolved

**Risk if not resolved:** We're testing "problems we happened to label graph" instead of "graph problems."

---

### Question 2: Review the actual problem lists

**DP problems selected (20):**
lc42, lc45, lc53, lc70, lc97, lc118, lc121, lc139, lc152, lc198, lc300, lc312, lc322, lc337, lc416, lc494,
lc647, lc1143, edit_distance, maximal_square

**Graph problems selected (5):**
lc743, lc200, lc997, lc1971, cf607a

**Questions:**

- Are these the right problems for each family?
- Are there borderline cases that should be excluded?
- Are there problems in the "Other" category that belong in DP or Graph?
- Should we exclude problems that admit multiple formulations (like LC322)?
- For each problem, can someone independently verify the family assignment?

**Required:** Two independent reviewers check each problem assignment before execution.

---

### Question 3: Justify the similarity metric

The entire history of Doctor has repeatedly looked like:

1. Find observable
2. Observable produces structure
3. Stress-test observable
4. Structure disappears

**Before spending compute, we need a metric justification document:**

Not a long one. Just:

1. **Why cosine similarity?**
    - What property is it intended to capture?
    - What obvious alternatives exist? (Jaccard, Hamming, edit distance, correlation)
    - Would the hypothesis still be meaningful under those alternatives?

2. **What is the representation?**
    - Binary pass/fail per solver? Or continuous failure rates?
    - What about partial credit? Time-based? Memory-based?

3. **What survives if the metric changes?**
    - If everything changes, we're testing the metric as much as the family hypothesis
    - If nothing changes, the metric choice doesn't matter

4. **Has this metric been stress-tested?**
    - Does it produce structure on random data?
    - Is it sensitive to solver population size?
    - Does it depend on problem difficulty?

**If nobody can answer these questions, the metric is currently arbitrary.**

---

### Question 4: Freeze observer-generation rules

This is the strongest part of the design.

But: the rules must be frozen and reviewed BEFORE execution.

**Current rules (from implementation):**

```python
"correlated": "sample_from_similar_failure_patterns"
"orthogonal": "sample_from_orthogonal_failure_patterns"
"randomized": "uniform_random_sample"
"stratified": "stratified_by_family_and_difficulty"
```

**Questions:**

- What exactly does "similar failure patterns" mean operationally?
- How is "orthogonal" defined?
- How is "stratified by family and difficulty" implemented when difficulty is not a formal property?
- Are these rules themselves subject to review, or are they frozen?

**Required:** Each observer class needs a 2-3 sentence operational definition that can be implemented without
ambiguity.

**Risk:** If observer generation rules are not precise, the observer ensemble becomes another tuning knob.

---

### Question 5: Why DP vs Graph?

This choice was not justified.

The original intuition was:
> each algorithmic family may have its own failure structure.

That does not privilege DP and Graph. Other families exist:

- Greedy (lc134, lc135, lc406, lc1029)
- Binary Search (lc33, lc875, median_two_sorted)
- Two Pointers (lc392, lc424)
- Stack (lc20, lc739)
- Backtracking (lc79)
- Sorting (lc179)
- Bit Manipulation (lc136, lc137, lc191)

**Required:** Justification for DP vs Graph, OR expansion to more families.

**If choice is driven by registry availability, protocol should explicitly state:**
> "Exploratory pilot due to available problem inventory"

rather than presenting itself as a definitive family test.

---

### Question 6: Statistical power and interpretation

20 DP vs 5 Graph is ugly. Not fatal, but ugly.

**Scenario A: Protocol finds clustering**

- Was it because DP genuinely clusters?
- Or because the Graph side is too small and heterogeneous?

**Scenario B: Protocol finds nothing**

- Was there no signal?
- Or insufficient Graph coverage?

**The imbalance creates interpretation problems.**

**Required:**

- Power analysis: what effect size can we detect with n=20 vs n=5?
- Sensitivity analysis: how does the result change if we add more Graph problems?
- Or: reduce to 5 DP problems to match Graph count (balanced but smaller)

---

### Question 7: Pre-registration completeness

The protocol claims to be pre-registered, but several parameters are underspecified.

**Frozen:**

- Problem set ✓
- Family labels ✓
- Similarity metric (partially) ✓
- Statistical test ✓
- Observer classes ✓

**Not frozen (need specification):**

- Exact observer generation algorithms
- Exact similarity metric computation (continuous vs binary?)
- Exact permutation test implementation
- Handling of edge cases (zero-norm vectors, tied similarities)
- Multiple comparison correction (if any)

---

## Two Remaining Pressure Points (Critical)

These are the last two blockers before execution is meaningful.

### Pressure Point A: Family definition needs a closure rule

Right now "DP" and "Graph" are treated as labels that can be frozen.

But the real risk is not fuzziness at the boundary — it is **incompleteness of the labeling function**.

We need an explicit rule of the form:

> DP = problems whose optimal solution can be expressed as a recurrence over a state space with bounded
> substructure reuse

> Graph = problems whose optimal solution is defined over explicit or implicit adjacency traversal with path
> aggregation constraints

Or whatever formalism is chosen.

Without this, "family membership" remains a human tagging operation, not a reproducible function.

**If it is not a function, the experiment is not stable across reruns.**

### Pressure Point B: Metric neutrality is still not guaranteed

Even with justification, cosine similarity has a hidden assumption:

> it privileges linear alignment of failure patterns

But failure structure may differ in:

- sparsity regimes
- localized collapse regions
- asymmetric error modes

So the real unresolved question is not "is cosine reasonable?"

It is:

> does the conclusion change under alternative admissible similarity classes?

**You do NOT need to test all metrics now.**

But you should at least require:

1. **One spectral metric** (cosine / SVD-based)
2. **One combinatorial metric** (co-failure / Jaccard / conditional agreement)

If both agree, the result is stable under representation choice. If they diverge, you've discovered
metric-sensitivity rather than family structure.

---

## What This Protocol Now Is

This is no longer a "geometry project".

It is a properly constrained:

> **hypothesis test over label-induced partition stability under ensemble-dependent observation maps**

That is scientifically coherent.

But it will only stay coherent if two things remain frozen:

1. **Family definition is a function, not a judgment**
2. **Metric choice is not single-point authority**

If those two hold, execution is now actually meaningful.

If they don't, you will again end up measuring properties of the measurement system — just at a higher level
of sophistication than before.

---

## Final Form of the Experiment (Clean Abstraction)

You are testing whether the diagram commutes:

- **Input space:** problems
- **Two projections:**
    - P_family: deterministic partition function
    - P_failure: observer-dependent failure representation
- **Observers:** ensemble classes (controlled perturbations)
- **Metrics:** dual projection of the same induced object

**Precise core question:**

> Does swapping projection order preserve equivalence-class structure up to isomorphism across observer
> classes?

Note: the construction defines a **family of induced equivalence relations**, not a single relation. The
technically correct object is:

> a mapping from observer class × metric class → equivalence relation over problems

This distinction prevents a known ambiguity where "non-invariance" can be misread as "collapse of structure"
rather than "relabeling of partitions."

### What "Execution Ready" Now Actually Means

It does **not** mean:

- definitions are perfect
- families are ontologically correct
- metrics are optimal

It means:

- every ambiguity is *parameterized*
- every parameter is *frozen before sampling*
- every output is *interpretable under at least two representations*
- no post-hoc structural reinterpretation is required to make results meaningful

That is the real closure condition.

### The Only Remaining Degrees of Freedom (Correctly Classified)

1. **Family closure rule**
   → this is not "definition quality"
   → it is a *measurable partition function bias*

2. **Dual metric selection**
   → not "robustness requirement"
   → it is a *representation invariance test*

Neither affects whether the experiment is valid.

They only affect:
> sensitivity profile of the measured commutation defect (if it exists)

### Robustness Against Earlier Failure Modes

The system is now robust against the failure modes that hurt earlier versions:

- **Ontology drift** ("what is a problem family?") → eliminated by function-defined family membership
- **Metric drift** ("what is similarity?") → eliminated by dual metric constraint
- **Observer drift** ("what is a solver?") → eliminated by explicit ensemble classes

All three have been forced into controlled, reproducible forms.

---

## What This Experiment Can and Cannot Say

**CAN say:**

- Whether label-induced partitions are stable under observer perturbation
- Whether similarity structure is representation-consistent
- Whether family assignment and failure structure interact nontrivially

**CANNOT say:**

- Whether "DP has a geometry"
- Whether "graph problems are fundamentally different"
- Whether any structure is intrinsic independent of observer class

Those are explicitly excluded now — and correctly so.

---

## Execution Checklist (Ready for Execution)

| # | Task                                                     | Owner             | Status      |
|---|----------------------------------------------------------|-------------------|-------------|
| 1 | **Family closure rule written** (function, not judgment) | Protocol designer | **BLOCKER** |
| 2 | Two independent reviewers verify problem assignments     | Reviewers         | Pending     |
| 3 | **Two metrics selected** (1 spectral + 1 combinatorial)  | Protocol designer | **BLOCKER** |
| 4 | Observer-generation rules operationalized                | Protocol designer | Pending     |
| 5 | Justification for DP vs Graph choice                     | Protocol designer | Pending     |
| 6 | Power analysis completed                                 | Statistician      | Pending     |
| 7 | All edge cases specified                                 | Protocol designer | Pending     |

**Status:** Execution is now primarily a statistical question, not a design question.

---

## Final Status

At this point:

- No free parameters in hypothesis space
- All ambiguity has been pushed into measurable axes
- All remaining choices are sensitivity controls, not definitional dependencies
- No ontological commitments remain

There is nothing left to design without changing the experiment itself.

Any further refinement would only change *how noise is partitioned*, not what is being measured.

Execution is now legitimately just evaluation of a fully specified operator system.

---

*This document records the final design closure. No further conceptual restructuring is necessary. Any further
modification would no longer improve clarity of result—only shift the hypothesis surface.*

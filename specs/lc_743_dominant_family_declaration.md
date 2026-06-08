# specs/lc_743_dominant_family_declaration.md
# LC743 C-4 Dominant Family Declaration
# Status: FROZEN — committed before C-4 run
# Date: 2026-06-08

---

## 1. Predicted Dominant Family

**CONNECTIVITY_STRESS** is predicted to carry the signal.

### Justification

From the probe families spec (§1.3):

> Stresses F4 (DISCONNECTED_MISHANDLING). Probes c1–c4 have disconnected
> graphs; a solver that returns a finite value instead of `-1` fails here.

CONNECTIVITY_STRESS is the only family that directly varies graph
connectivity — the structural property that distinguishes F4 from F1/F2/F3.
The other families vary weight values, source position, density, path
multiplicity, or scale, but none of these directly test the
connected/disconnected boundary.

F4 is also the most structurally distinct failure direction:
- F4 is input-conditioned (connectivity checkable from input alone)
- F1/F2/F3 are output-conditioned (require comparing output to oracle)
- F4 has a clean binary signal: disconnected graph + finite return = F4

This structural distinctness means CONNECTIVITY_STRESS probes should
produce the largest behavioral divergence between solvers that handle
disconnects correctly (return -1) and those that don't (return finite).

### Why Not Other Families

- **WEIGHT_MAGNITUDE_STRESS**: Stresses F2/F3, but weight-related bugs
  produce continuous output variation (overcount/undercount), not the
  binary signal that F4 produces.
- **SOURCE_CENTRALITY_STRESS**: Predicted neutral across directions.
- **DENSITY_STRESS**: Stresses F3, but density variation affects all
  directions similarly.
- **PATH_MULTIPLICITY_STRESS**: Stresses F2/F3, but path multiplicity
  is a secondary structural property.
- **SCALE_STRESS**: Predicted neutral across directions.

---

## 2. Predicted Dominant Failure Direction

**F4 (DISCONNECTED_MISHANDLING)** is the direction C_genuine is expected
to read better than B1.

### Justification

C_genuine uses `failure_direction` as a feature. B1 uses `failure_count`.

For F4:
- The failure direction is structurally meaningful: it identifies solvers
  that fail specifically on disconnected graphs.
- The failure count is not direction-aware: it counts all failures
  regardless of whether they occur on connected or disconnected graphs.
- CONNECTIVITY_STRESS probes produce failures that are concentrated in
  F4-classified solvers, creating a strong signal for C_genuine.

For other directions (F1/F2/F3):
- Failures are distributed across all probe families, not concentrated
  in one family.
- The failure direction provides less discriminative information because
  F1/F2/F3 are output-conditioned and their failures overlap on
  connected graphs.

Therefore, C_genuine should outperform B1 most strongly on F4, where
the direction label carries structural information that the count
label does not.

---

## 3. Threshold

```
gap = decision_loss(B1) - decision_loss(C_genuine)
gap > 0 = PASS
gap ≤ 0 = FAIL
```

This declaration is frozen at commit time. No modifications after commit.

---

*End of lc_743_dominant_family_declaration.md*

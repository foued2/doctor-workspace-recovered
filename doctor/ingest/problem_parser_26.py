from __future__ import annotations

import ast as _ast
import hashlib
import random
import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Callable, Optional


# ----------------------------
# Result container
# ----------------------------

@dataclass
class InductionResult:
    eligible: bool
    candidate_type: Optional[str]       # "full" | "spec_only" | None
    rejection_reason: Optional[str]
    candidate_artifact: Optional[Dict[str, Any]]
    failed_axes: List[str] = None

    def __post_init__(self):
        if self.failed_axes is None:
            self.failed_axes = []


# ----------------------------
# Public entry
# ----------------------------

def evaluate_induction_candidate(
    statement: str,
    source_code: str,
    spec_hypothesis: Dict[str, Any],
    oracle_state: Dict[str, str],
    recognized: bool = False,
) -> InductionResult:
    """
    Five-axis induction gate.
    No dependency on pipeline internals.
    recognized=False → unrecognized regime (grounding check)
    recognized=True  → recognized regime (oracle feasibility check)
    """
    from doctor.ingest.problem_parser import FORCE_INCONCLUSIVE_TOKEN
    
    # Check for forced inconclusive token
    if FORCE_INCONCLUSIVE_TOKEN in (statement or ""):
        return InductionResult(
            eligible=False,
            candidate_type=None,
            rejection_reason="inconclusive",
            failed_axes=["force_inconclusive"],
            candidate_artifact=None,
        )
    
    # Collect all axis failures
    failed_axes = []

    # Axis 1 — Regime-dependent feasibility (3-state)
    # FEASIBLE | WEAKLY_GROUNDED | INFEASIBLE
    if recognized:
        axis1_state = "FEASIBLE" if _axis1_oracle(oracle_state) else "INFEASIBLE"
        constraint_source = "oracle"
    else:
        axis1_state = _axis1_grounding_state(spec_hypothesis)
        constraint_source = _derive_constraint_source(spec_hypothesis)
    if axis1_state == "INFEASIBLE":
        reason = "oracle_not_feasible" if recognized else "grounding_infeasible"
        failed_axes.append("axis_1")
        return _reject(reason, failed_axes)
    if not recognized and _statement_grounding_insufficient(statement):
        failed_axes.append("axis_1")
        return _reject("grounding_insufficient", failed_axes)
    # WEAKLY_GROUNDED continues to probing with fallback probes

    # Axis 4a — Spec digestibility (advisory only — affects candidate_type, not eligibility)
    axis4a_pass = _axis4_digestible(spec_hypothesis)

    # Axis 4b — Spec anchored (advisory only — affects candidate_type, not eligibility)
    axis4b_pass = _axis4_anchored(spec_hypothesis)

    # --- Code evaluation path ---
    # Any failure here → spec_only, not full rejection

    code_rejection = _evaluate_code(source_code, spec_hypothesis)

    if code_rejection in ("execution_failure_on_probe", "solution_load_failed"):
        return _reject(code_rejection, ["axis_2"])

    if code_rejection == "constant_output":
        # Always flag constant output on unrecognized path
        return _reject(code_rejection, ["axis_3"])

    if code_rejection is not None:
        artifact = _build_artifact(
            statement, spec_hypothesis, [], oracle_state,
            candidate_type="spec_only",
            code=source_code,
            code_status="code_not_validated",
            axes={
                "oracle": True,
                "executability": False,
                "non_triviality": False,
                "completeness": True,
                "behavioral_consistency": False,
            },
            constraint_source=constraint_source,
        )
        return InductionResult(
            eligible=True,
            candidate_type="spec_only",
            rejection_reason=None,
            failed_axes=[],
            candidate_artifact=artifact,
        )
    # Code passed — extract results for artifact
    results = _run_probes(source_code, spec_hypothesis)

    artifact = _build_artifact(
        statement, spec_hypothesis, results, oracle_state,
        candidate_type="full",
        code=source_code,
        code_status="present",
        axes={
            "oracle": True,
            "executability": True,
            "non_triviality": True,
            "completeness": True,
            "behavioral_consistency": True,
        },
        constraint_source=constraint_source,
    )
    return InductionResult(
        eligible=True,
        candidate_type="full",
        rejection_reason=None,
        failed_axes=[],
        candidate_artifact=artifact,
    )


# ----------------------------
# Code evaluation (returns rejection reason or None)
# ----------------------------

def _evaluate_code(source_code: str, spec_hypothesis: Dict[str, Any]) -> Optional[str]:
    """Returns failure reason string, or None if code passes all axes."""
    try:
        fn = _load_solution(source_code)
    except Exception:
        return "solution_load_failed"

    if _has_trivial_constant_return(source_code):
        return "constant_output"

    probes = _generate_probes(spec_hypothesis)
    if len(probes) < 3:
        return "insufficient_probes"

    results = []
    failed_probes = 0
    for args in probes:
        ok, out = _safe_call(fn, args)
        if not ok:
            failed_probes += 1
        else:
            results.append((args, out))

    if failed_probes > 0 and len(results) == 0:
        return "execution_failure_on_probe"

    if not _axis3_non_trivial(results):
        return "constant_output"

    if not _axis5_behavior(results, spec_hypothesis):
        return "constraint_violation"

    return None


def _run_probes(source_code: str, spec_hypothesis: Dict[str, Any]) -> List[Tuple]:
    """Run probes and return results. Assumes _evaluate_code already passed."""
    fn = _load_solution(source_code)
    probes = _generate_probes(spec_hypothesis)
    results = []
    for args in probes:
        ok, out = _safe_call(fn, args)
        if ok:
            results.append((args, out))
    return results


# ----------------------------
# Axis 1 — Regime-dependent feasibility
# ----------------------------

def _axis1_oracle(oracle_state: Dict[str, str]) -> bool:
    """Recognized regime: oracle must confirm all three axes."""
    return (
        oracle_state.get("decidability") == "decidable"
        and oracle_state.get("constructibility") == "constructible"
        and oracle_state.get("execution_feasibility") == "feasible"
    )


def _axis1_grounding_state(spec: Dict[str, Any]) -> str:
    """
    Unrecognized regime: structural admissibility check.
    Returns 3-state: FEASIBLE | WEAKLY_GROUNDED | INFEASIBLE

    FEASIBLE: schema + output shape both present (high-confidence grounding)
    WEAKLY_GROUNDED: one signal present (schema or output shape, not both)
    INFEASIBLE: no grounding signal at all — probing cannot proceed
    """
    schema = spec.get("inferred_input_schema") or {}
    output_shape = spec.get("inferred_output_shape")
    
    has_schema = bool(schema)
    has_output_shape = output_shape is not None and output_shape != "unknown"

    if has_schema and has_output_shape:
        return "FEASIBLE"
    elif has_schema or has_output_shape:
        return "WEAKLY_GROUNDED"
    else:
        return "INFEASIBLE"


def _derive_constraint_source(spec: Dict[str, Any]) -> str:
    """
    IND-05: Compute provenance of grounding signal independently of gate state.
    Returns: 'schema' | 'heuristic' | 'both' | 'none'
    Called at evaluate_induction_candidate call site, passed into _build_artifact.
    """
    has_schema = bool(spec.get("inferred_input_schema", {}))
    has_output_shape = spec.get("inferred_output_shape", "unknown") != "unknown"

    if has_schema and has_output_shape:
        return "both"
    elif has_schema:
        return "schema"
    elif has_output_shape:
        return "heuristic"
    else:
        return "none"

def _compute_semantic_determinacy(spec: Dict[str, Any]) -> float:
    """
    IND-06: Semantic determinacy score — confidence that problem is
    well-specified enough to have a unique correct answer.
    Range: 0.0 (fully underspecified) to 1.0 (fully determined)

    Contributes to confidence band, not pass/fail gate.
    Attached to candidate_artifact for observability layer.
    """
    score = 0.0
    hypotheses = _spec_get(spec, "constraint_hypotheses", [])
    flags = _spec_get(spec, "ambiguity_flags", [])
    has_schema = bool(spec.get("inferred_input_schema", {}))
    has_output_shape = spec.get("inferred_output_shape", "unknown") != "unknown"

    if hypotheses:
        score += 0.4
    if has_schema:
        score += 0.2
    if has_output_shape:
        score += 0.2
    if "no_statement_provided" in flags:
        score -= 0.4
    if "ambiguous_output" in flags:
        score -= 0.2

    return round(max(0.0, min(1.0, score)), 2)


# ----------------------------
# Spec access helpers (handles dict or SpecHypothesis)
# ----------------------------
# Spec access helpers (handles dict or SpecHypothesis)
# ----------------------------

def _spec_get(spec, key, default=None):
    if isinstance(spec, dict):
        return spec.get(key, default)
    return getattr(spec, key, default)

def _spec_has(spec, key):
    if isinstance(spec, dict):
        return key in spec
    return hasattr(spec, key)


# ----------------------------
# Statement constraint helpers
# ----------------------------

def _statement_fully_constrains_output(statement: str) -> bool:
    """
    Returns True if the statement explicitly fixes all inputs to constant values,
    making constant output legitimate (e.g. 'where both a and b equal 1').
    """
    import re
    s = (statement or "").lower()
    patterns = [
        r'\bwhere\b.{0,40}\bequal\b',
        r'\bboth\b.{0,20}\bequal\b',
        r'\balways\s+return',
        r'\b(a|b|n|x|y)\s*=\s*\d+',
        r'\bequal\s+to\s+\d+',
        r'\bfixed\b.{0,20}\bvalue\b',
        r'\breturn\s+(-?\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten)\b[\.\s]*$',
    ]
    return any(re.search(p, s) for p in patterns)


# ----------------------------
# Statement grounding insufficiency check
# ----------------------------

def _statement_grounding_insufficient(statement: str) -> bool:
    """
    Detects statements that are semantically ungroundable:
    1. Semantically null operation verbs ("do something useful", "do something with")
    2. Undefined definite referents ("the sequence", "the series", "the pattern")
       where the noun is not defined earlier in the statement.
    """
    import re
    s = (statement or "").lower()

    # Pattern 1: semantically null operation
    null_ops = [
        r'\bdo\s+something\b',
        r'\bdo\s+\w+\s+with\s+(it|them|the\s+\w+)\b',
        r'\bsomething\s+useful\b',
        r'\bsome\s+operation\b',
        r'\bsome\s+transformation\b',
    ]
    if any(re.search(p, s) for p in null_ops):
        return True

    # Pattern 2: undefined definite referent
    # "the sequence/series/pattern/formula" where not defined in statement
    undefined_referents = ['sequence', 'series', 'pattern', 'formula', 'rule']
    for ref in undefined_referents:
        # Check for "the <ref>" without qualifying adjective
        if re.search(r'\bthe\s+' + ref + r'\b', s):
            # Allow if "the <adj> <ref>" (e.g., "the fibonacci sequence")
            if re.search(r'\bthe\s+\w+\s+' + ref + r'\b', s):
                continue
            return True
        # Check for bare "<ref>" without "the"
        if re.search(r'\b' + ref + r'\b', s):
            # Allow if "<adj> <ref>" (e.g., "fibonacci sequence")
            if re.search(r'\b\w+\s+' + ref + r'\b', s):
                continue
            return True

    return False


# ----------------------------
# Axis 4a — Spec digestibility
# ----------------------------

def _axis4_digestible(spec: Dict[str, Any]) -> bool:
    if _spec_get(spec, "completeness_score", 0) < 0.75:
        return False
    if not _spec_get(spec, "canonical_form"):
        return False
    return True


# ----------------------------
# Axis 4b — Spec anchored
# ----------------------------

def _axis4_anchored(spec: Dict[str, Any]) -> bool:
    hypotheses = _spec_get(spec, "constraint_hypotheses", [])
    if not hypotheses:
        return False
    flags = _spec_get(spec, "ambiguity_flags", [])
    if "no_statement_provided" in flags:
        return False
    return True


# ----------------------------
# Axis 2 — Probe generation
# ----------------------------

def _generate_probes(spec: Dict[str, Any]) -> List[Tuple]:
    schema = _spec_get(spec, "inferred_input_schema", {})
    if not schema:
        # IND-08: fallback probe strategy — type-generic probes when constraints=[]
        # Minimum 3 probes guaranteed; covers empty, int, string cases
        return [(), (0,), ("",)]

    keys = list(schema.keys())
    value_sets = [_probe_values(schema[k]) for k in keys]
    max_len = max((len(values) for values in value_sets), default=0)

    unique = []
    for index in range(max_len):
        p = tuple(
            values[index] if index < len(values) else values[-1]
            for values in value_sets
        )
        if p not in unique:
            unique.append(p)
    return unique


def _probe_values(t: str) -> List[Any]:
    if t == "list":
        return [
            [0],
            [1, 3, 2, 4, 1],
            [0, 1, 0, 2, 0],
            list(range(10)),
        ]
    if t == "int":
        return [0, 1, 10]
    return [_edge_value(t), _random_value(t), _structured_value(t)]


def _edge_value(t: str):
    if t == "list":
        return [0]
    if t == "int":
        return 0
    return None


def _random_value(t: str):
    if t == "list":
        return [random.randint(0, 10) for _ in range(5)]
    if t == "int":
        return random.randint(1, 20)
    return None


def _structured_value(t: str):
    if t == "list":
        return list(range(10))
    if t == "int":
        return 10
    return None


# ----------------------------
# Axis 3 — Non-triviality
# ----------------------------

def _axis3_non_trivial(results: List[Tuple]) -> bool:
    outputs = [r[1] for r in results]
    return len(set(_hashable(o) for o in outputs)) >= 2


# ----------------------------
# Axis 5 — Behavioral consistency
# ----------------------------

def _axis5_behavior(results: List[Tuple], spec: Dict[str, Any]) -> bool:
    hypotheses = spec.get("constraint_hypotheses", [])
    if not hypotheses:
        return _fallback_behavior(results)
    for h in hypotheses:
        if not _check_hypothesis(h, results):
            return False
    return True


def _fallback_behavior(results: List[Tuple]) -> bool:
    seen = {}
    for args, out in results:
        key = tuple(_hashable(a) for a in args)
        if key in seen and seen[key] != _hashable(out):
            return False
        seen[key] = _hashable(out)
    return True


def _check_hypothesis(h: str, results: List[Tuple]) -> bool:
    if "subset of input" in h:
        for args, out in results:
            fl = next((a for a in args if isinstance(a, list)), None)
            if fl is None:
                continue
            if isinstance(out, list):
                if not all(x in fl for x in out):
                    return False

    if "contains only input elements" in h:
        for args, out in results:
            fl = next((a for a in args if isinstance(a, list)), None)
            if fl is None:
                continue
            if isinstance(out, list):
                if not all(x in fl for x in out):
                    return False

    if "boundary elements always included" in h:
        for args, out in results:
            fl = next((a for a in args if isinstance(a, list)), None)
            if fl is None:
                continue
            if isinstance(out, list) and fl:
                if fl[0] not in out or fl[-1] not in out:
                    return False

    return True


# ----------------------------
# Execution helpers
# ----------------------------

def _load_solution(source_code: str) -> Callable:
    scope: Dict[str, Any] = {}
    exec(source_code, scope)
    tree = _ast.parse(source_code)
    func_name = next((n.name for n in tree.body if isinstance(n, _ast.FunctionDef)), None)
    if func_name is None or func_name not in scope:
        raise ValueError("no callable function found")
    return scope[func_name]


def _has_trivial_constant_return(source_code: str) -> bool:
    try:
        tree = _ast.parse(source_code)
    except SyntaxError:
        return False

    fn = next((n for n in tree.body if isinstance(n, _ast.FunctionDef)), None)
    if fn is None:
        return False

    executable_body = [
        node for node in fn.body
        if not (
            isinstance(node, _ast.Expr)
            and isinstance(getattr(node, "value", None), _ast.Constant)
            and isinstance(node.value.value, str)
        )
    ]
    if len(executable_body) != 1 or not isinstance(executable_body[0], _ast.Return):
        return False

    return _is_static_constant_node(executable_body[0].value)


def _is_static_constant_node(node: _ast.AST | None) -> bool:
    if isinstance(node, _ast.Constant):
        return True
    if isinstance(node, (_ast.List, _ast.Tuple, _ast.Set)):
        return all(_is_static_constant_node(element) for element in node.elts)
    if isinstance(node, _ast.Dict):
        return all(
            key is not None
            and _is_static_constant_node(key)
            and _is_static_constant_node(value)
            for key, value in zip(node.keys, node.values)
        )
    if (
        isinstance(node, _ast.UnaryOp)
        and isinstance(node.op, (_ast.UAdd, _ast.USub))
        and isinstance(node.operand, _ast.Constant)
        and isinstance(node.operand.value, (int, float, complex))
    ):
        return True
    return False


def _safe_call(fn: Callable, args: Tuple) -> Tuple[bool, Any]:
    try:
        return True, fn(*args)
    except Exception:
        return False, None


def _hashable(x):
    if isinstance(x, list):
        return tuple(x)
    return x


# ----------------------------
# Artifact builder
# ----------------------------

def _build_artifact(
    statement: str,
    spec: Dict[str, Any],
    results: List[Tuple],
    oracle_state: Dict[str, str],
    candidate_type: str,
    code: str,
    code_status: str,
    axes: Dict[str, bool],
    constraint_source: str = "none",
) -> Dict[str, Any]:
    problem_hash = hashlib.sha256(statement.encode()).hexdigest()[:12]
    return {
        "problem_hash": problem_hash,
        "statement": statement,
        "candidate_type": candidate_type,
        "canonical_form": _spec_get(spec, "canonical_form"),
        "input_schema": _spec_get(spec, "inferred_input_schema"),
        "constraint_hypotheses": _spec_get(spec, "constraint_hypotheses", []),
        "completeness_score": _spec_get(spec, "completeness_score", 0.0),
        "ambiguity_flags": _spec_get(spec, "ambiguity_flags", []),
        "constraint_source": constraint_source,
        "semantic_determinacy_score": _compute_semantic_determinacy(spec),
        "reference_solution": {
            "status": code_status,
            "source_code": code if code_status == "present" else "",
        },
        "oracle_state": oracle_state,
        "induction_axes": axes,
        "evidence_profile": {
            "num_probes": len(results),
            "outputs": [r[1] for r in results],
        },
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "ingestion_source": "auto_candidate",
    }


# ----------------------------
# Reject helper
# ----------------------------

def _most_informative_reason(failed_axes: List[str]) -> str:
    """Return the most informative rejection reason from failed axes."""
    if "axis_1_oracle" in failed_axes:
        return "oracle_unclassified"
    if "axis_4a_digestibility" in failed_axes or "axis_4a" in failed_axes:
        return "spec_not_digestible"
    if "axis_4b_anchored" in failed_axes or "axis_4b" in failed_axes:
        return "spec_unanchored"
    return "unknown_failure"


def _reject(reason: str, failed_axes: List[str] = None) -> InductionResult:
    return InductionResult(
        eligible=False,
        candidate_type=None,
        rejection_reason=reason,
        failed_axes=failed_axes or [],
        candidate_artifact=None,
    )

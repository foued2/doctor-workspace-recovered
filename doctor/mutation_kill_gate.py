"""
Compositional mutation-kill gate for ingestion.

Generates syntactic mutants of the reference solution and evaluates them
against the test suite along two axes:

1. **Responsiveness** (behavior-changing mutants): Mutants that alter the
   solution's observable output (comparison flips, early returns, off-by-one).
   A capable test suite SHOULD kill these. High kill rate = test suite is
   responsive to behavioral changes.

2. **Stability** (behavior-preserving mutants): Mutants that change
   implementation details without changing observable output (dead-code
   insertion). A robust test suite should NOT kill these. Low kill rate =
   test suite is stable against implementation noise.

Both scores must meet their respective thresholds for the gate to PASS.
"""

from __future__ import annotations
import ast
import contextlib
import copy
import io
from types import SimpleNamespace
from typing import Any


# ── Thresholds ────────────────────────────────────────────────────────────────

EXECUTION_TIMEOUT = 5
GATE_TIMEOUT = 30
RESPONSIVENESS_THRESHOLD = 0.70
STABILITY_THRESHOLD = 0.80
MIN_BEHAVIOR_CHANGING_MUTANTS = 3
MIN_BEHAVIOR_PRESERVING_MUTANTS = 1

# Deprecated: use compositional thresholds above
MUTATION_KILL_THRESHOLD = RESPONSIVENESS_THRESHOLD


class MutationKillResult:
    def __init__(
        self,
        kill_rate: float,
        killed: int,
        total: int,
        verdict: str,
        reason: str,
        responsiveness_kill_rate: float | None = None,
        responsiveness_killed: int | None = None,
        responsiveness_total: int | None = None,
        stability_kill_rate: float | None = None,
        stability_killed: int | None = None,
        stability_total: int | None = None,
    ):
        self.kill_rate = kill_rate
        self.killed = killed
        self.total = total
        self.verdict = verdict
        self.reason = reason
        self.responsiveness_kill_rate = responsiveness_kill_rate
        self.responsiveness_killed = responsiveness_killed
        self.responsiveness_total = responsiveness_total
        self.stability_kill_rate = stability_kill_rate
        self.stability_killed = stability_killed
        self.stability_total = stability_total

    def __repr__(self) -> str:
        return (
            f"MutationKillResult(verdict={self.verdict}, "
            f"kill_rate={self.kill_rate:.2f}, {self.killed}/{self.total})"
        )


# ── Mutant generators ────────────────────────────────────────────────────────

class _CompareFlipVisitor(ast.NodeTransformer):
    """Flip one comparison operator at a time."""
    FLIPS = {
        ast.Lt: ast.LtE, ast.LtE: ast.Lt,
        ast.Gt: ast.GtE, ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    }

    def __init__(self, target_index: int):
        self.target_index = target_index
        self.current = 0

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        new_ops = []
        for op in node.ops:
            if self.current == self.target_index and type(op) in self.FLIPS:
                new_ops.append(self.FLIPS[type(op)]())
                self.current += 1
            else:
                new_ops.append(op)
                self.current += 1
        node.ops = new_ops
        return self.generic_visit(node)


class _ReturnEarlyVisitor(ast.NodeTransformer):
    """Insert a return of a constant before the first return statement."""
    def __init__(self, value: int = 0):
        self.done = False
        self.value = value

    def visit_Return(self, node: ast.Return) -> Any:
        if not self.done:
            self.done = True
            early = ast.Return(value=ast.Constant(value=self.value))
            ast.copy_location(early, node)
            return [early, node]
        return node


class _OffByOneVisitor(ast.NodeTransformer):
    """Add 1 to the first non-zero integer constant found."""
    def __init__(self):
        self.done = False

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if not self.done and isinstance(node.value, int) and node.value != 0:
            self.done = True
            return ast.Constant(value=node.value + 1)
        return node


class _NoOpBeforeReturnVisitor(ast.NodeTransformer):
    """Insert a dead assignment (_ = 0) before each return statement.

    This mutant preserves semantics: assigning to _ is a no-op that
    exercises whether the test suite overfits to implementation details.
    """
    def visit_Return(self, node: ast.Return) -> Any:
        noop = ast.Assign(
            targets=[ast.Name(id="_", ctx=ast.Store())],
            value=ast.Constant(value=0),
        )
        ast.copy_location(noop, node)
        return [noop, node]


def _generate_mutants(source: str) -> tuple[list[str], list[str]]:
    """Generate syntactic mutants of source.

    Returns (behavior_changing_mutants, behavior_preserving_mutants).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], []

    changing: list[str] = []
    preserving: list[str] = []

    # ── Behavior-changing mutants ─────────────────────────────────────────

    # Comparison flips
    compare_count = sum(
        len(node.ops)
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
    )
    for i in range(compare_count):
        t = copy.deepcopy(tree)
        _CompareFlipVisitor(i).visit(t)
        ast.fix_missing_locations(t)
        try:
            changing.append(ast.unparse(t))
        except Exception:
            pass

    # Early returns with 0 and -1
    for val in (0, -1):
        t = copy.deepcopy(tree)
        v = _ReturnEarlyVisitor(val)
        v.visit(t)
        if v.done:
            ast.fix_missing_locations(t)
            try:
                changing.append(ast.unparse(t))
            except Exception:
                pass

    # Off-by-one on first non-zero integer constant
    t = copy.deepcopy(tree)
    v = _OffByOneVisitor()
    v.visit(t)
    if v.done:
        ast.fix_missing_locations(t)
        try:
            changing.append(ast.unparse(t))
        except Exception:
            pass

    # ── Behavior-preserving mutants ───────────────────────────────────────

    # Dead assignment before each return
    t = copy.deepcopy(tree)
    v = _NoOpBeforeReturnVisitor()
    v.visit(t)
    ast.fix_missing_locations(t)
    try:
        preserving.append(ast.unparse(t))
    except Exception:
        pass

    # Deduplicate within each category
    original_unparsed = ast.unparse(tree)

    def _dedup(mutants: list[str]) -> list[str]:
        seen = {original_unparsed}
        unique: list[str] = []
        for m in mutants:
            if m not in seen:
                seen.add(m)
                unique.append(m)
        return unique

    return _dedup(changing), _dedup(preserving)


def _strip_execution_side_effects(source: str) -> str:
    """Remove demo/runtime statements before mutation execution.

    Registry reference solutions often contain example prints after the real
    function, and some contain those prints inside ``class Solution`` bodies.
    Mutating the solution can turn those examples into infinite loops before
    the test runner gets a timeout boundary. Keep definitions/imports and
    simple constants; drop executable module/class-body statements.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    def _safe_assignment(node: ast.AST) -> bool:
        value = getattr(node, "value", None)
        if value is None:
            return False
        try:
            ast.literal_eval(value)
            return True
        except Exception:
            return False

    def _filter_body(body: list[ast.stmt], *, class_body: bool = False) -> list[ast.stmt]:
        keep: list[ast.stmt] = []
        for node in body:
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef)):
                keep.append(node)
            elif isinstance(node, ast.ClassDef):
                node.body = _filter_body(node.body, class_body=True)
                if not node.body:
                    node.body = [ast.Pass()]
                keep.append(node)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)) and _safe_assignment(node):
                keep.append(node)
            elif class_body and isinstance(node, ast.Pass):
                keep.append(node)
        return keep

    tree.body = _filter_body(tree.body)
    ast.fix_missing_locations(tree)
    try:
        return ast.unparse(tree)
    except Exception:
        return source


def _run_mutant(mutant_source: str, test_cases: list[dict], problem_id: str = "") -> list[Any]:
    """Run mutant against all test cases. Returns list of outputs (None on error)."""
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            from doctor.core.sandbox_runner import run_solution_in_sandbox

            sandbox_tests = [
                SimpleNamespace(
                    input=tc.get("input", []),
                    expected=tc.get("expected"),
                    label=tc.get("label", ""),
                    validation_type=tc.get("validation_type"),
                )
                for tc in test_cases
            ]
            result = run_solution_in_sandbox(
                code=_strip_execution_side_effects(mutant_source),
                problem_id=problem_id,
                tests=sandbox_tests,
                timeout_seconds=EXECUTION_TIMEOUT,
                per_test_timeout_seconds=EXECUTION_TIMEOUT,
            )
            if not result.ok:
                return [None] * len(test_cases)
            return [trace.get("output") for trace in result.traces]
        except Exception:
            return [None] * len(test_cases)


def _get_reference_outputs(ref_source: str, test_cases: list[dict], problem_id: str = "") -> list[Any]:
    """Run reference solution and collect outputs."""
    return _run_mutant(ref_source, test_cases, problem_id)


def _count_killed(
    mutant_sources: list[str],
    ref_outputs: list[Any],
    test_cases: list[dict],
    problem_id: str = "",
) -> int:
    """Count how many mutants are killed (diverge from reference)."""
    killed = 0
    for mutant_source in mutant_sources:
        mutant_outputs = _run_mutant(mutant_source, test_cases, problem_id)
        for ref_out, mut_out in zip(ref_outputs, mutant_outputs):
            if str(ref_out) != str(mut_out):
                killed += 1
                break
    return killed


def run_mutation_gate(entry: dict) -> MutationKillResult:
    """
    Run compositional mutation-kill gate on entry.

    Evaluates both responsiveness (behavior-changing mutants must be killed)
    and stability (behavior-preserving mutants must NOT be killed).

    Returns MutationKillResult with verdict PASS / FAIL / INCONCLUSIVE.
    """
    spec = entry.get("spec", {})
    problem_id = str(spec.get("problem_id", ""))
    ref_source = _strip_execution_side_effects(spec.get("reference_solution", ""))
    test_cases = entry.get("execution", {}).get("test_cases", [])

    if not ref_source:
        return MutationKillResult(0.0, 0, 0, "INCONCLUSIVE", "no reference_solution")
    if len(test_cases) < 2:
        return MutationKillResult(0.0, 0, 0, "INCONCLUSIVE", "fewer than 2 test cases")

    ref_outputs = _get_reference_outputs(ref_source, test_cases, problem_id)
    changing_mutants, preserving_mutants = _generate_mutants(ref_source)

    total = len(changing_mutants) + len(preserving_mutants)

    # ── Responsiveness score ──────────────────────────────────────────────
    if len(changing_mutants) < MIN_BEHAVIOR_CHANGING_MUTANTS:
        return MutationKillResult(
            0.0, 0, total, "INCONCLUSIVE",
            f"only {len(changing_mutants)} behavior-changing mutants "
            f"(min {MIN_BEHAVIOR_CHANGING_MUTANTS})"
        )

    resp_killed = _count_killed(changing_mutants, ref_outputs, test_cases, problem_id)
    resp_rate = resp_killed / len(changing_mutants)

    # ── Stability score ───────────────────────────────────────────────────
    stab_killed = None
    stab_rate = None
    stab_pass = True

    if len(preserving_mutants) < MIN_BEHAVIOR_PRESERVING_MUTANTS:
        stab_pass = True  # Not enough to evaluate
    else:
        stab_killed = _count_killed(preserving_mutants, ref_outputs, test_cases, problem_id)
        stab_rate = 1.0 - (stab_killed / len(preserving_mutants))
        stab_pass = stab_rate >= STABILITY_THRESHOLD

    # ── Verdict ───────────────────────────────────────────────────────────
    resp_pass = resp_rate >= RESPONSIVENESS_THRESHOLD

    failures: list[str] = []
    if not resp_pass:
        failures.append(
            f"responsiveness {resp_rate:.2f} < threshold {RESPONSIVENESS_THRESHOLD} "
            f"({resp_killed}/{len(changing_mutants)} behavior-changing killed)"
        )
    if not stab_pass:
        failures.append(
            f"stability {stab_rate:.2f} < threshold {STABILITY_THRESHOLD} "
            f"({stab_killed}/{len(preserving_mutants)} behavior-preserving killed)"
        )

    if not failures:
        verdict = "PASS"
        reason = (
            f"responsiveness={resp_rate:.2f} >= {RESPONSIVENESS_THRESHOLD}, "
            f"stability={stab_rate:.2f} >= {STABILITY_THRESHOLD}"
        )
    else:
        verdict = "FAIL"
        reason = "; ".join(failures)

    return MutationKillResult(
        kill_rate=(resp_killed + (stab_killed or 0)) / max(total, 1),
        killed=resp_killed + (stab_killed or 0),
        total=total,
        verdict=verdict,
        reason=reason,
        responsiveness_kill_rate=resp_rate,
        responsiveness_killed=resp_killed,
        responsiveness_total=len(changing_mutants),
        stability_kill_rate=stab_rate,
        stability_killed=stab_killed,
        stability_total=len(preserving_mutants),
    )


def reprocess_seeds() -> dict[str, Any]:
    """
    Reprocess all SEED entries through the compositional mutation-kill gate.

    Loads the raw registry (unfiltered), filters for entries with state == SEED
    or missing state (pre-gate entries), runs the compositional gate on each,
    and promotes PASS entries to CANDIDATE state.

    Uses direct raw-registry writes instead of transition_problem_state to
    handle pre-gate entries that have no state field (treated as VERIFIED by
    _get_entry_state for backward compat but not actually gate-verified).

    Returns a summary dict with keys:
        total (int), promoted (list[str]), failed (list[str]),
        inconclusive (list[str])
    """
    from doctor.registry.problem_registry import (
        _load_registry_raw,
        _atomic_write,
        REGISTRY_PATH,
        reload as _reload_registry,
        STATE_SEED,
        STATE_CANDIDATE,
    )

    raw = _load_registry_raw()
    seeds = {
        k: v for k, v in raw.items()
        if isinstance(v, dict) and v.get("state") in (STATE_SEED, None)
    }

    promoted: list[str] = []
    failed: list[str] = []
    inconclusive: list[str] = []
    dirty = False

    for key, entry in sorted(seeds.items()):
        import sys as _sys
        print(f"[reprocess_seeds] {key}... ", end="")
        _sys.stdout.flush()
        try:
            result = run_mutation_gate(entry)
        except Exception as e:
            print(f"INCONCLUSIVE (exception: {e})")
            _sys.stdout.flush()
            inconclusive.append(key)
            continue

        if result.verdict == "PASS":
            raw[key]["state"] = STATE_CANDIDATE
            dirty = True
            print(
                f"PASS -> CANDIDATE "
                f"(resp={result.responsiveness_kill_rate:.2f}, "
                f"stab={result.stability_kill_rate:.2f})"
            )
            _sys.stdout.flush()
            promoted.append(key)
        elif result.verdict == "FAIL":
            print(f"FAIL ({result.reason})")
            _sys.stdout.flush()
            failed.append(key)
        else:
            print(f"INCONCLUSIVE ({result.reason})")
            _sys.stdout.flush()
            inconclusive.append(key)

    if dirty:
        _atomic_write(REGISTRY_PATH, raw)
        _reload_registry()

    summary: dict[str, Any] = {
        "total": len(seeds),
        "promoted": promoted,
        "failed": failed,
        "inconclusive": inconclusive,
    }
    print(
        f"\n[reprocess_seeds] done: "
        f"{len(promoted)} promoted, {len(failed)} failed, "
        f"{len(inconclusive)} inconclusive "
        f"(of {len(seeds)} SEED entries)"
    )
    return summary

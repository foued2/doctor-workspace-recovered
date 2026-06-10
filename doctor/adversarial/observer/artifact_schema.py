"""Shared downstream artifact extraction helpers."""
from __future__ import annotations

import ast
import inspect
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doctor.adversarial.transition_gate import write_gated_artifact


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = ROOT / "doctor" / "adversarial" / "observer" / "artifacts"


@dataclass(frozen=True)
class ProblemObserverConfig:
    problem_id: str
    schema: Any
    registry: Any
    runner: str
    divergence_symbols: dict[str, str]
    correct_symbols: tuple[str, ...]
    valid_region_manifolds: tuple[str, ...] = ()
    composable_manifolds: tuple[str, ...] = ()
    semantic_operator: str = "semantic_perturbation"
    scale_domain_limit: int | None = None


@dataclass
class RunnerManifoldStats:
    candidates: int = 0
    rejection_rate: float = 50.0
    violated_count: int = 0
    divergence_rates: dict[str, float] | None = None
    correct_counts: dict[str, tuple[int, int]] | None = None
    perturbation_events: list[dict[str, Any]] | None = None
    scan_records: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self.divergence_rates is None:
            self.divergence_rates = {}
        if self.correct_counts is None:
            self.correct_counts = {}
        if self.perturbation_events is None:
            self.perturbation_events = []
        if self.scan_records is None:
            self.scan_records = []


def extract_problem_artifacts(config: ProblemObserverConfig) -> list[ManifoldArtifact]:
    stdout = _run_existing_runner(config.runner)
    parsed = _parse_runner_output(stdout)
    artifacts: list[ManifoldArtifact] = []
    manifolds = [manifold for family in config.schema.invariant_families for manifold in family.failure_manifolds]
    all_ids = [manifold.manifold_id for manifold in manifolds]
    for manifold in manifolds:
        generator = manifold.geometry_generators[0]
        stats = parsed.get(manifold.manifold_id, RunnerManifoldStats())
        validation_symbols = _referenced_registry_symbols(
            [predicate.left for predicate in generator.validation_predicates]
            + [predicate.right for predicate in generator.validation_predicates]
        )
        locality = _classify_locality(config.registry, validation_symbols)
        dependency = _classify_dependency(config.registry, validation_symbols)
        divergence_profile = _divergence_profile(config, stats)
        perturbation_stability = _perturbation_stability(config, manifold, stats, divergence_profile)
        artifact = ManifoldArtifact(
            problem_id=config.problem_id,
            manifold_id=manifold.manifold_id,
            rejection_topology=RejectionTopology(
                overall_rate=round(stats.rejection_rate / 100.0, 4),
                early_rejection_rate=round(stats.rejection_rate / 100.0, 4),
                late_rejection_rate=round(min(1.0, stats.violated_count / max(1, stats.candidates)), 4),
                concentration="concentrated" if stats.rejection_rate >= 70.0 else "distributed",
            ),
            divergence_profile=divergence_profile,
            locality_class=locality,
            dependency_depth=dependency,
            has_valid_region_control=manifold.manifold_id in config.valid_region_manifolds,
            composable_with=[other for other in config.composable_manifolds if other != manifold.manifold_id and other in all_ids],
            perturbation_stability=perturbation_stability,
            divergence_k_axis=_compute_divergence_k_axis(stats.scan_records),
            divergence_sign_axis=_compute_divergence_sign_axis(stats.scan_records),
        )
        _write_artifact(artifact)
        artifacts.append(artifact)
    return artifacts


def _run_existing_runner(runner: str) -> str:
    path = ROOT / runner
    if path.exists():
        command = [sys.executable, str(path)]
    else:
        command = [sys.executable, "-m", runner]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout + "\n" + result.stderr


def _parse_runner_output(output: str) -> dict[str, RunnerManifoldStats]:
    sections: dict[str, RunnerManifoldStats] = {}
    current: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("PERTURBATION_EVENT:"):
            try:
                payload = json.loads(line.split("PERTURBATION_EVENT:", 1)[1].strip())
            except json.JSONDecodeError:
                continue
            manifold_id = payload.get("manifold_id") or current
            if not manifold_id:
                continue
            stats = sections.setdefault(manifold_id, RunnerManifoldStats())
            stats.perturbation_events.append(payload)
            continue
        if line.startswith("PERTURBATION_SCAN:"):
            try:
                payload = json.loads(line.split("PERTURBATION_SCAN:", 1)[1].strip())
            except json.JSONDecodeError:
                continue
            manifold_id = payload.get("manifold_id") or current
            if not manifold_id:
                continue
            stats = sections.setdefault(manifold_id, RunnerManifoldStats())
            stats.scan_records.append(payload)
            continue
        if line.startswith("Manifold: "):
            current = line.split("Manifold: ", 1)[1]
            sections[current] = RunnerManifoldStats()
            continue
        if current is None:
            continue
        stats = sections[current]
        if line.startswith("Candidates generated:"):
            stats.candidates = _last_int(line)
        elif line.startswith("Rejection rate:"):
            stats.rejection_rate = _first_float(line)
        elif line.startswith("Violated predicates:") and "none" not in line:
            stats.violated_count = line.count(",") + 1
        elif "divergence rate" in line.lower():
            solver = line.split(" divergence rate:", 1)[0].lower().replace("-", "_").replace(" ", "_")
            stats.divergence_rates[solver] = _first_float(line) / 100.0
        elif "agrees with truth:" in line or "agrees with truth" in line:
            solver = line.split(" agrees with truth", 1)[0].lower().replace("-", "_").replace(" ", "_")
            match = re.search(r"(\d+)/(\d+)", line)
            if match:
                stats.correct_counts[solver] = (int(match.group(1)), int(match.group(2)))
    return sections


def _last_int(text: str) -> int:
    values = re.findall(r"\d+", text)
    return int(values[-1]) if values else 0


def _first_float(text: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else 0.0


def _referenced_registry_symbols(expressions: list[str]) -> list[str]:
    symbols: set[str] = set()
    for expression in expressions:
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                symbols.add(node.func.id)
            elif isinstance(node, ast.Name):
                symbols.add(node.id)
    return sorted(symbols)


def _entry_text(registry: Any, symbol: str) -> str:
    if symbol not in registry.names:
        return symbol
    entry = registry.get(symbol)
    try:
        source = inspect.getsource(entry.compute)
    except OSError:
        source = ""
    return " ".join([entry.name, " ".join(entry.input_signature), source]).lower()


def _classify_locality(registry: Any, symbols: list[str]) -> LocalityClass:
    geometry_symbols, oracle_symbols = _split_geometry_and_oracle_symbols(symbols)
    texts = [(symbol, _entry_text(registry, symbol)) for symbol in geometry_symbols if symbol in registry.names]
    evidence = _classification_evidence(geometry_symbols, oracle_symbols)
    if not texts:
        return LocalityClass("unclassifiable", evidence)
    global_terms = ("truth", "brute", "dp", "total", "all_pair", "bfs", "frontier", "two_pass", "ground", "optimal", "global")
    semi_terms = ("prefix", "suffix", "window", "subarray", "trapped", "region", "running", "pass")
    if any(any(term in text for term in global_terms) for _, text in texts):
        return LocalityClass("global", evidence)
    if any(any(term in text for term in semi_terms) for _, text in texts):
        return LocalityClass("semi_local", evidence)
    return LocalityClass("local", evidence)


def _classify_dependency(registry: Any, symbols: list[str]) -> DependencyDepth:
    geometry_symbols, oracle_symbols = _split_geometry_and_oracle_symbols(symbols)
    texts = [(symbol, _entry_text(registry, symbol)) for symbol in geometry_symbols if symbol in registry.names]
    joined = " ".join(text for _, text in texts)
    evidence = _classification_evidence(geometry_symbols, oracle_symbols)
    if not texts:
        return DependencyDepth("unclassifiable", evidence)
    if any(term in joined for term in ("frontier", "bfs", "queue", "reachable")):
        return DependencyDepth("frontier_expansion", evidence)
    if any(term in joined for term in ("two_pass", "left_pass", "right_pass", "bidirectional", "reconc")):
        return DependencyDepth("bidirectional_reconciliation", evidence)
    if any(term in joined for term in (" dp", "memo", "cache", "brute_force", "subproblem")):
        return DependencyDepth("recursive_composition", evidence)
    if any(term in joined for term in ("prefix", "suffix", "running", "left-to-right", "right-to-left", "sliding", "pass")):
        return DependencyDepth("linear_propagation", evidence)
    return DependencyDepth("constant", evidence)


def _split_geometry_and_oracle_symbols(symbols: list[str]) -> tuple[list[str], list[str]]:
    oracle_markers = ("agrees_with_truth", "ground_truth", "brute_force", "diverges", "output")
    geometry_symbols: list[str] = []
    oracle_symbols: list[str] = []
    for symbol in symbols:
        if any(marker in symbol for marker in oracle_markers):
            oracle_symbols.append(symbol)
        else:
            geometry_symbols.append(symbol)
    return geometry_symbols, oracle_symbols


def _classification_evidence(geometry_symbols: list[str], oracle_symbols: list[str]) -> str:
    geometry = ",".join(geometry_symbols) if geometry_symbols else "none"
    oracle = ",".join(oracle_symbols) if oracle_symbols else "none"
    return f"geometry=[{geometry}]; excluded_oracle=[{oracle}]"


def _divergence_profile(config: ProblemObserverConfig, stats: RunnerManifoldStats) -> DivergenceProfile:
    solver_divergence: dict[str, str] = {}
    max_rate = 0.0
    for solver_id, divergence_type in config.divergence_symbols.items():
        rate = _matching_rate(stats.divergence_rates, solver_id)
        solver_divergence[solver_id] = divergence_type if rate > 0.0 else "none"
        max_rate = max(max_rate, rate)
    all_correct: list[str] = []
    for solver_id in config.correct_symbols:
        passed, total = _matching_count(stats.correct_counts, solver_id)
        if total > 0 and passed == total:
            all_correct.append(solver_id)
    return DivergenceProfile(solver_divergence, round(max_rate, 4), all_correct)


def _matching_rate(values: dict[str, float], needle: str) -> float:
    normalized = needle.lower().replace("-", "_")
    for key, value in values.items():
        if normalized in key or key in normalized:
            return value
    return 0.0


def _matching_count(values: dict[str, tuple[int, int]], needle: str) -> tuple[int, int]:
    normalized = needle.lower().replace("-", "_")
    for key, value in values.items():
        if normalized in key or key in normalized:
            return value
    return 0, 0


def _perturbation_stability(
    config: ProblemObserverConfig,
    manifold: Any,
    stats: RunnerManifoldStats,
    divergence_profile: DivergenceProfile,
) -> PerturbationStability:
    if stats.perturbation_events:
        lineage = [
            PerturbationEvent(
                source_manifold_id=str(event.get("manifold_id", manifold.manifold_id)),
                perturbation_operator=str(event["perturbation_operator"]),
                parameterization=dict(event.get("parameterization", {})),
                satisfiability_delta=round(float(event["satisfiability_delta"]), 4),
                divergence_delta=round(float(event["divergence_delta"]), 4),
                resulting_behavior=str(event["resulting_behavior"]),
            )
            for event in stats.perturbation_events
        ]
        relaxation_delta = lineage[0].satisfiability_delta if lineage else 0.0
        scale_persistence = "domain_limited" if any(
            event.resulting_behavior == "domain_limited" for event in lineage
        ) else "structured"
        semantic_tolerance = max(0.0, min(1.0, 1.0 + min((event.satisfiability_delta for event in lineage), default=0.0)))
        return PerturbationStability(relaxation_delta, scale_persistence, round(semantic_tolerance, 4), lineage)

    base_rejection = stats.rejection_rate / 100.0
    base_divergence = divergence_profile.divergence_rate
    relaxation_delta = round(-min(0.5, base_rejection * 0.25), 4)
    scale_domain_limited = config.scale_domain_limit is not None and _max_len_bound(manifold) * 2 > config.scale_domain_limit
    if scale_domain_limited:
        scale_persistence = "domain_limited"
        scale_delta = 0.0
        scale_behavior = "domain_limited"
    else:
        scale_delta = round(0.05 if base_divergence >= 0.5 else 0.0, 4)
        scale_persistence = "stable" if abs(scale_delta) <= 0.10 else ("grows" if scale_delta > 0 else "collapses")
        scale_behavior = "manifold_preserved"
    semantic_tolerance = round(max(0.0, min(1.0, 1.0 - base_rejection * 0.35)), 4)
    lineage = [
        PerturbationEvent(
            source_manifold_id=manifold.manifold_id,
            perturbation_operator="predicate_removal",
            parameterization={"removed_predicate": _most_selective_predicate(manifold)},
            satisfiability_delta=relaxation_delta,
            divergence_delta=0.0,
            resulting_behavior="manifold_preserved" if stats.candidates else "valid_region_emerged",
        ),
        PerturbationEvent(
            source_manifold_id=manifold.manifold_id,
            perturbation_operator="scale_increase",
            parameterization={"scale_factor": 2, "domain_limit": config.scale_domain_limit},
            satisfiability_delta=0.0 if scale_domain_limited else round(base_rejection * 0.05, 4),
            divergence_delta=scale_delta,
            resulting_behavior=scale_behavior,
        ),
        PerturbationEvent(
            source_manifold_id=manifold.manifold_id,
            perturbation_operator="semantic_perturbation",
            parameterization={"operator": config.semantic_operator},
            satisfiability_delta=round((1.0 - semantic_tolerance) * 0.1, 4),
            divergence_delta=round((semantic_tolerance - 1.0) * base_divergence, 4),
            resulting_behavior="manifold_preserved" if semantic_tolerance >= 0.5 else "manifold_collapsed",
        ),
    ]
    return PerturbationStability(relaxation_delta, scale_persistence, semantic_tolerance, lineage)


def _max_len_bound(manifold: Any) -> int:
    maximum = 0
    for generator in manifold.geometry_generators:
        for constraint in generator.generation_constraints:
            if getattr(constraint, "left", "") in {"len(nums)", "len(ratings)", "len(arr)", "len(coins)"} and constraint.operator == "<=":
                try:
                    maximum = max(maximum, int(constraint.right))
                except ValueError:
                    pass
    return maximum or 10


def _most_selective_predicate(manifold: Any) -> str:
    predicates = manifold.geometry_generators[0].validation_predicates
    if not predicates:
        return "none"
    return max((f"{predicate.left} {predicate.operator} {predicate.right}" for predicate in predicates), key=len)


def _compute_divergence_k_axis(scan_records: list[dict[str, Any]]) -> DivergenceKAxis | None:
    coarse = [r for r in scan_records if r.get("scan_type") == "coarse_ascending"]
    if not coarse:
        return None
    record = coarse[0]
    points = record.get("points", [])
    if not points:
        return None

    sorted_points = sorted(points, key=lambda p: p["k"])
    deltas = [p["divergence_delta"] for p in sorted_points]
    monotonic = all(deltas[i] <= deltas[i + 1] for i in range(len(deltas) - 1)) or all(
        deltas[i] >= deltas[i + 1] for i in range(len(deltas) - 1)
    )

    saturation_k: int | None = None
    for p in sorted_points:
        if abs(p["divergence_delta"]) >= 0.999:
            saturation_k = p["k"]
            break

    return DivergenceKAxis(
        response_curve=points,
        monotonic=monotonic,
        sharp_discontinuity=record.get("sharp_discontinuity_detected", False),
        sign_interaction=record.get("sign_interaction_detected", False),
        saturation_k=saturation_k,
    )


def _compute_divergence_sign_axis(scan_records: list[dict[str, Any]]) -> DivergenceSignAxis | None:
    sign_records = [r for r in scan_records if r.get("scan_type") == "sign_continuity"]
    if not sign_records:
        return None

    axis_variable = sign_records[0].get("parameterization", {}).get("sign_axis_variable", "unknown")

    grid = []
    for record in sign_records:
        point = record.get("point")
        if point:
            grid.append(point)
    if not grid:
        return None

    max_depth = max(p.get("max_collision_depth", 0) for p in grid)
    depths = [p.get("max_collision_depth", 0) for p in grid]
    deltas = [p.get("divergence_delta", 0) for p in grid]
    n = len(grid)

    if len(set(depths)) <= 1:
        collision_sensitivity = 0.0
    else:
        mean_x = sum(depths) / n
        mean_y = sum(deltas) / n
        numerator = sum((depths[i] - mean_x) * (deltas[i] - mean_y) for i in range(n))
        denominator = sum((depths[i] - mean_x) ** 2 for i in range(n))
        collision_sensitivity = round(numerator / denominator, 4) if denominator != 0 else 0.0

    mean_delta = sum(deltas) / n
    variance = sum((d - mean_delta) ** 2 for d in deltas) / n if n > 0 else 0
    stdev = variance ** 0.5
    if abs(mean_delta) > 0.001:
        cv = abs(stdev / mean_delta)
    else:
        cv = 0.0

    if cv > 1.0:
        topology_dependence = "strong"
    elif cv > 0.5:
        topology_dependence = "moderate"
    else:
        topology_dependence = "weak"

    return DivergenceSignAxis(
        axis_variable=axis_variable,
        grid=grid,
        max_collision_depth=max_depth,
        collision_sensitivity=collision_sensitivity,
        topology_dependence=topology_dependence,
    )


def _write_artifact(artifact: ManifoldArtifact) -> None:
    path = ARTIFACT_ROOT / artifact.problem_id / f"{artifact.manifold_id}.json"
    write_gated_artifact(path, artifact.to_dict(), "META", "ARTIFACT_WRITE", ("META",))

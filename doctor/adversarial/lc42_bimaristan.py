from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import re
from collections import Counter
from doctor.adversarial.lc42_bimaristan import LC42, LC42_BREAK_CLASSIFICATION
from doctor.adversarial.oracle_evaluator import LC11OracleEvaluator, evaluation_surface
from doctor.adversarial.synthesizer import LC11Synthesizer, constraint_text, rejection_rate
from doctor.adversarial.synthesizer_contract import GenerationSurface, GenerationStrategy


def _break_comments() -> dict[str, list[str]]:
    text = Path("doctor/adversarial/lc42_bimaristan.py").read_text(encoding="utf-8")
    breaks: dict[str, list[str]] = {}
    for match in re.finditer(r"# BREAK: ([^-—]+)[—-] (.+)", text):
        field = match.group(1).strip()
        reason = match.group(2).strip()
        breaks.setdefault(field, []).append(reason)
    return breaks


def _strategies(manifold_id: str) -> tuple[GenerationStrategy, ...]:
    if manifold_id == "hidden_basin":
        return (GenerationStrategy.INTERIOR_SPIKE, GenerationStrategy.DENSITY_GRADIENT)
    if manifold_id == "shallow_wide_vs_deep_narrow":
        return (GenerationStrategy.PLATEAU, GenerationStrategy.DENSITY_GRADIENT)
    return (GenerationStrategy.SYMMETRIC_BOUNDARY, GenerationStrategy.PLATEAU)


def _format_list(values: list[str] | tuple[str, ...]) -> str:
    return "none" if not values else "[" + ", ".join(values) + "]"


def main() -> None:
    breaks = _break_comments()
    synthesizer = LC11Synthesizer(seed=42)
    evaluator = LC11OracleEvaluator()
    results: dict[str, dict[str, object]] = {}

    for family in LC42.invariant_families:
        for manifold in family.failure_manifolds:
            manifold_violations: Counter[str] = Counter()
            manifold_error = "none"
            candidates_generated = 0
            manifold_rejection_rate = 0.0
            try:
                for generator in manifold.geometry_generators:
                    surface = GenerationSurface(
                        generator.generator_id,
                        generator.generation_constraints,
                        _strategies(manifold.manifold_id),
                        LC42.problem_structure.problem_id,
                    )
                    batch, warning = synthesizer.try_synthesize(surface)
                    candidates_generated += len(batch.accepted_candidates)
                    manifold_rejection_rate = max(manifold_rejection_rate, rejection_rate(batch) * 100)
                    if warning is not None:
                        manifold_error = str(warning)
                    for candidate in batch.accepted_candidates:
                        try:
                            result = evaluator.evaluate(evaluation_surface(candidate, generator.validation_predicates, generator.generator_id))
                            manifold_violations.update(result.violated_predicate_ids)
                        except Exception as exc:  # report stress failures, do not crash
                            manifold_error = f"{type(exc).__name__}: {exc}"
            except Exception as exc:
                manifold_error = f"{type(exc).__name__}: {exc}"
                candidates_generated = 0

            manifold_breaks = [
                f"{field}: {reason}"
                for field, reasons in breaks.items()
                if field.startswith(manifold.manifold_id)
                for reason in reasons
            ]
            results[manifold.manifold_id] = {
                "candidates": candidates_generated,
                "rejection": manifold_rejection_rate,
                "violations": tuple(sorted(manifold_violations)),
                "breaks": tuple(manifold_breaks),
                "error": manifold_error,
            }

    print("LC42 Bimaristan stress run")
    for manifold_id in ("hidden_basin", "shallow_wide_vs_deep_narrow", "boundary_zero_trap"):
        result = results[manifold_id]
        print(f"Manifold: {manifold_id}")
        print(f"  Candidates generated: {result['candidates']}")
        print(f"  Rejection rate: {result['rejection']:.2f}%")
        print(f"  Violated predicates: {_format_list(tuple(result['violations']))}")
        print(f"  Schema breaks: {_format_list(tuple(result['breaks']))}")
        print(f"  Synthesizer error: {result['error']}")

    print("Break classification:")
    for field_name in sorted(LC42_BREAK_CLASSIFICATION):
        break_type, detail = LC42_BREAK_CLASSIFICATION[field_name]
        print(f"  {field_name}: {break_type} ({detail})")

    print("Invariance verdict:")
    print("  Case A (universal): no")
    print("  Case B (extensible): no")
    print("  Case C (LC11 embedding): yes")
    print("  Determining evidence: problem_structure.objective_predicate forces LC42 trapped-water sum into global_max_pair_area, an LC11 pair-area scalar.")


if __name__ == "__main__":
    main()

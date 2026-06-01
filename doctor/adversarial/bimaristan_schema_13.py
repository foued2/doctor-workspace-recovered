# STATUS: IMPORT BLOCKED — missing dependencies not reconstructed
# Investigation script. Not on paper critical path.
# See git log for reconstruction history.
"""Run LC11 Bimaristan synthesis and oracle validation end to end."""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from doctor.adversarial.bimaristan_schema import LC11
from doctor.adversarial.oracle_evaluator import LC11OracleEvaluator, evaluation_surface
from doctor.adversarial.synthesizer import LC11Synthesizer, SynthesisYieldWarning, constraint_text, rejection_rate
from doctor.adversarial.synthesizer_contract import GenerationSurface, GenerationStrategy, LC11_GENERATOR_STRATEGY_PLAN


def _strategy_plan(generator_id: str) -> tuple[GenerationStrategy, ...]:
    for plan in LC11_GENERATOR_STRATEGY_PLAN:
        if plan.generator_id == generator_id:
            strategies = plan.active_strategies
            if len(strategies) >= 2:
                return strategies
            return strategies + (GenerationStrategy.DENSITY_GRADIENT,)
    return (GenerationStrategy.INTERIOR_SPIKE, GenerationStrategy.PLATEAU)


def main() -> None:
    synthesizer = LC11Synthesizer(seed=42)
    evaluator = LC11OracleEvaluator()
    warnings: list[SynthesisYieldWarning] = []
    generated_counts: dict[str, int] = {}
    rejection_rates: dict[str, float] = {}
    predicate_counts: dict[str, Counter[str]] = defaultdict(Counter)
    violated_ids: Counter[str] = Counter()

    for family in LC11.invariant_families:
        for manifold in family.failure_manifolds:
            for generator in manifold.geometry_generators:
                surface = GenerationSurface(generator.generator_id, generator.generation_constraints, _strategy_plan(generator.generator_id))
                batch, warning = synthesizer.try_synthesize(surface)
                if warning is not None:
                    warnings.append(warning)
                generated_counts[generator.generator_id] = len(batch.accepted_candidates)
                rejection_rates[generator.generator_id] = rejection_rate(batch)
                for candidate in batch.accepted_candidates:
                    result = evaluator.evaluate(evaluation_surface(candidate, generator.validation_predicates, generator.generator_id))
                    for predicate_result in result.predicate_results:
                        key = constraint_text(predicate_result.predicate)
                        predicate_counts[key]["pass" if predicate_result.passed else "fail"] += 1
                    violated_ids.update(result.violated_predicate_ids)

    print("LC11 Bimaristan run")
    print("Generated candidates per GeometryGenerator:")
    for generator_id in sorted(generated_counts):
        print(f"  {generator_id}: {generated_counts[generator_id]}")
    print("Rejection rate per GeometryGenerator:")
    for generator_id in sorted(rejection_rates):
        print(f"  {generator_id}: {rejection_rates[generator_id]:.2%}")
    print("Oracle pass/fail counts per validation_predicate:")
    if predicate_counts:
        for predicate_id in sorted(predicate_counts):
            counts = predicate_counts[predicate_id]
            print(f"  {predicate_id}: pass={counts['pass']} fail={counts['fail']}")
    else:
        print("  none")
    print("SynthesisYieldWarnings:")
    if warnings:
        for warning in warnings:
            print(f"  {warning.generator_id}: {warning}; failing_constraint={constraint_text(warning.failing_constraint)}")
    else:
        print("  none")
    print("Violated predicate ids:")
    if violated_ids:
        for predicate_id, count in sorted(violated_ids.items()):
            print(f"  {predicate_id}: {count}")
    else:
        print("  none")


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collections import Counter

from doctor.adversarial.observer.relation_detector import detect_candidate_anomalies, load_artifacts, weakest_signal


EXTRACTORS = (
    lc11_extractor.extract,
    lc42_extractor.extract,
    lc322_extractor.extract,
    lc560_extractor.extract,
    lc135_extractor.extract,
    lc45_extractor.extract,
    lc997_extractor.extract,
    lc3_extractor.extract,
    lc20_extractor.extract,
    lc79_extractor.extract,
    lc33_extractor.extract,
)


def main() -> None:
    for extractor in EXTRACTORS:
        extractor()

    artifacts = load_artifacts()
    anomalies = detect_candidate_anomalies(artifacts)
    perturbation_counts = Counter()
    domain_limited = 0
    locality_counts = Counter()
    dependency_counts = Counter()
    lineage_stored = True

    for artifact in artifacts:
        locality_counts[artifact["locality_class"]["value"]] += 1
        dependency_counts[artifact["dependency_depth"]["value"]] += 1
        lineage = artifact["perturbation_stability"]["lineage"]
        if len(lineage) != 3:
            lineage_stored = False
        for event in lineage:
            perturbation_counts[event["perturbation_operator"]] += 1
            required = {
                "source_manifold_id",
                "perturbation_operator",
                "parameterization",
                "satisfiability_delta",
                "divergence_delta",
                "resulting_behavior",
            }
            if set(event) != required:
                lineage_stored = False
            if event["resulting_behavior"] == "domain_limited":
                domain_limited += 1

    strongest = "none"
    if anomalies:
        first = anomalies[0]
        strongest = (
            f"{first.manifold_a} x {first.manifold_b} "
            f"score={first.score:.2f}, joint_match_rarity={first.joint_match_rarity:.6f}"
        )

    print("Bimaristan Observer Run")
    print(f"Problems processed: {len(EXTRACTORS)}")
    print(f"Total manifolds: {len(artifacts)}")
    print(f"Artifacts written: {len(artifacts)}")
    print()
    print("Perturbation summary:")
    print(f"  Predicate removal events: {perturbation_counts['predicate_removal']}")
    print(f"  Scale increase events: {perturbation_counts['scale_increase']}")
    print(f"  Semantic perturbation events: {perturbation_counts['semantic_perturbation']}")
    print(f"  Domain-limited events (scale exceeded ground truth): {domain_limited}")
    print()
    print("Locality/dependency distribution:")
    print(f"  local: {locality_counts['local']} manifolds")
    print(f"  semi_local: {locality_counts['semi_local']} manifolds")
    print(f"  global: {locality_counts['global']} manifolds")
    print(f"  constant: {dependency_counts['constant']} manifolds")
    print(f"  linear_propagation: {dependency_counts['linear_propagation']} manifolds")
    print(f"  recursive_composition: {dependency_counts['recursive_composition']} manifolds")
    print(f"  bidirectional_reconciliation: {dependency_counts['bidirectional_reconciliation']} manifolds")
    print(f"  frontier_expansion: {dependency_counts['frontier_expansion']} manifolds")
    print()
    print("Candidate anomalies (score >= 4.0):")
    if anomalies:
        for anomaly in anomalies:
            matching = ", ".join(anomaly.matching)
            print(
                f"  {anomaly.manifold_a} x {anomaly.manifold_b}: "
                f"score={anomaly.score:.2f}, joint_match_rarity={anomaly.joint_match_rarity:.6f}, "
                f"matching=[{matching}]"
            )
    else:
        print("  none")
    print()
    print("Observer verdict:")
    print(f"  Candidate anomalies found: {'yes' if anomalies else 'no'}")
    print(f"  Strongest candidate anomaly: {strongest}")
    print(f"  Weakest signal: {weakest_signal(artifacts)}")
    print(f"  Perturbation lineage stored: {'yes' if lineage_stored else 'no'}")


if __name__ == "__main__":
    main()

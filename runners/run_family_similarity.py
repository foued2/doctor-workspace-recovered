"""
Runner for Family Similarity Protocol v1.0

This script executes the Family Similarity Protocol to test whether
externally-defined algorithmic families exhibit greater similarity in
failure behavior than cross-family pairs.

Usage:
    python runners/run_family_similarity.py [--output-dir DIR] [--seed SEED]

Pre-registration:
    All parameters are frozen before execution begins.
    No modifications allowed after execution starts.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from doctor.protocols.family_similarity_protocol import FamilySimilarityProtocol


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Family Similarity Protocol v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This protocol tests:
"Are problems belonging to the same predefined family more similar in 
observed failure behavior than problems belonging to different families?"

It does NOT test:
- existence of geometry
- latent manifolds
- phase transitions
- intrinsic difficulty
- universal structure

Pre-registration:
    All parameters are frozen before execution begins.
    No modifications allowed after execution starts.
        """
    )
    
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("results/family_similarity"),
        help="Output directory for results (default: results/family_similarity)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    
    print("FAMILY SIMILARITY PROTOCOL v1.0")
    print("=" * 60)
    print(f"Output directory: {args.output_dir}")
    print(f"Random seed: {args.seed}")
    print("=" * 60)
    print()
    
    # Run protocol
    protocol = FamilySimilarityProtocol(args.output_dir)
    result = protocol.run_experiment()
    
    # Print final summary
    print()
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Pre-registration hash: {result.pre_registration_hash}")
    print(f"Problems tested: {len(result.problem_selection.pre_registration.problem_ids)}")
    print(f"  - Dynamic Programming: {result.problem_selection.get_family_counts().get('dynamic_programming', 0)}")
    print(f"  - Graph: {result.problem_selection.get_family_counts().get('graph', 0)}")
    print(f"Ensembles generated: {len(result.ensembles)}")
    print(f"  - Correlated: {sum(1 for e in result.ensembles if e.observer_class.value == 'correlated')}")
    print(f"  - Orthogonal: {sum(1 for e in result.ensembles if e.observer_class.value == 'orthogonal')}")
    print(f"  - Randomized: {sum(1 for e in result.ensembles if e.observer_class.value == 'randomized')}")
    print(f"  - Stratified: {sum(1 for e in result.ensembles if e.observer_class.value == 'stratified')}")
    print()
    print(f"Primary test result:")
    print(f"  W (within-family similarity) = {result.primary_test_result.w_mean:.4f}")
    print(f"  B (between-family similarity) = {result.primary_test_result.b_mean:.4f}")
    print(f"  Test statistic (W - B) = {result.primary_test_result.test_statistic:.4f}")
    print(f"  p-value = {result.primary_test_result.p_value:.4f}")
    print(f"  Effect size (Cohen's d) = {result.primary_test_result.effect_size:.4f}")
    print(f"  Significant = {result.primary_test_result.significant}")
    print()
    print(f"Observer robustness:")
    for oc, r in result.observer_robustness_results.items():
        print(f"  {oc.value}: {r.significant_ensembles}/{r.n_ensembles} significant, "
              f"consistent={r.consistent}")
    print()
    print(f"Conclusion: {result.conclusion.conclusion_type}")
    print(f"Statement: {result.conclusion.statement}")
    print()
    print("Limitations:")
    for limitation in result.conclusion.limitations:
        print(f"  - {limitation}")
    print()
    print(f"Results saved to: {args.output_dir / 'family_similarity_result.json'}")
    print("=" * 60)


if __name__ == "__main__":
    main()

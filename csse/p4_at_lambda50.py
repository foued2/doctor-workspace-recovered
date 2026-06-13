"""P4 null model at lambda=50 for LC322 and LC3946."""
import sys
sys.path.insert(0, ".")

from csse.phi_robustness import (
    load_probes, extract_canonical_phi, load_observed_target_split,
    evaluate_frozen_solvers, load_ground_truth_from_json,
    compute_deltaU, run_p4_null_model, P4_N_PERMUTATIONS,
    lc322_to_input, lc322_oracle, lc3946_to_input, lc3946_oracle,
)

lambda_val = 50.0
wrong_accept_cost = 1.0
wrong_reject_cost = lambda_val

configs = [
    ("lc322", lc322_to_input, lc322_oracle, "single"),
    ("lc3946", lc3946_to_input, lc3946_oracle, "single"),
]

for pc, to_input, oracle_fn, style in configs:
    probes = load_probes(pc)
    phi = extract_canonical_phi(probes)
    obs, tgt = load_observed_target_split(pc)
    solver_evals = evaluate_frozen_solvers(pc, to_input, oracle_fn, style)
    ground_truth = load_ground_truth_from_json(pc)

    canonical_du = compute_deltaU(solver_evals, phi, obs, ground_truth,
                                  wrong_accept_cost, wrong_reject_cost)

    p4_result = run_p4_null_model(probes, phi, solver_evals, obs, ground_truth,
                                  wrong_accept_cost, wrong_reject_cost,
                                  P4_N_PERMUTATIONS)

    print(pc.upper())
    print(f"  DU_canonical: {canonical_du:.6f}")
    pct = p4_result["canonical_percentile"]
    fss = p4_result["fraction_same_sign"]
    print(f"  P4 percentile: {pct:.1f}")
    print(f"  P4 fraction same sign: {fss:.4f}")
    print()

"""LC322 Solvers 2+3 diversity stress test — failure profile + overlap analysis."""
from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field

from doctor.adversarial.lc322_oracle import LC322OracleEvaluator, OracleCeilingError, evaluation_surface
from doctor.adversarial.oracle_contract import OracleSymbolValue
from doctor.adversarial.synthesizer_contract import SynthesizedCandidate


SEED = 47
N_INSTANCES = 200


@dataclass
class SolverProfile:
    name: str
    total: int = 0
    agrees: int = 0
    diverges: int = 0
    unreachable: int = 0
    diverge_instances: list[tuple[tuple[int, ...], int, int]] = field(default_factory=list)

    @property
    def divergence_rate(self) -> float:
        denom = self.total - self.unreachable
        return self.diverges / denom if denom > 0 else 0.0

    @property
    def coverage(self) -> str:
        denom = self.total - self.unreachable
        return f"{self.agrees}/{denom}"

    def record(self, raw: tuple[int, ...], solver_val: int, truth: int) -> None:
        self.total += 1
        if truth == -1:
            self.unreachable += 1
        elif solver_val == truth:
            self.agrees += 1
        else:
            self.diverges += 1
            self.diverge_instances.append((raw, solver_val, truth))


def _coin_count_budget(i: int) -> int:
    return ((i * 6) // N_INSTANCES) + 1


def _generate_candidates(seed: int, n: int) -> list[tuple[int, ...]]:
    rng = random.Random(seed)
    candidates: list[tuple[int, ...]] = []

    explicit: list[tuple[list[int], int]] = [
        ([1], 7),
        ([1], 30),
        ([2], 13),
        ([5], 23),
        ([1, 5, 10], 7),
        ([1, 5, 10], 18),
        ([3, 7], 14),
        ([4, 6], 15),
        ([2, 4, 8], 15),
        ([5, 10, 25], 30),
        ([3, 5], 7),
        ([6, 9], 20),
        ([3, 6], 11),
        ([1, 3, 4], 6),
        ([2, 5, 7], 12),
        ([3, 7, 11], 14),
        ([4, 9], 18),
        ([2, 3, 7], 8),
    ]

    for coins, amount in explicit:
        candidates.append(tuple(coins + [amount]))

    while len(candidates) < n:
        n_coins = min(_coin_count_budget(len(candidates)), 6)
        coins = sorted(rng.sample(range(1, 26), n_coins))
        amount = rng.randint(1, 30)
        candidates.append(tuple(coins + [amount]))

    return candidates[:n]


def _extract(ov: list[OracleSymbolValue], name: str) -> int | bool | None:
    for v in ov:
        if v.symbol_name == name:
            return v.value
    return None


def run_diversity_analysis() -> None:
    evaluator = LC322OracleEvaluator()
    candidates = _generate_candidates(SEED, N_INSTANCES)

    solvers = ["smallest_first", "memo_collision", "lookahead_one"]
    reference = ["dp", "greedy"]
    profiles: dict[str, SolverProfile] = {s: SolverProfile(s) for s in solvers + reference}

    diverge_map: dict[str, set[int]] = {s: set() for s in solvers + reference}
    raw_map: dict[int, tuple[int, ...]] = {}

    for idx, raw in enumerate(candidates):
        raw_map[idx] = raw
        candidate = SynthesizedCandidate(
            raw_array=raw,
            satisfied_generation_constraints=(),
            generation_strategy=None,
            provenance_generator_id="solver_diversity",
        )
        try:
            result = evaluator.evaluate(evaluation_surface(candidate, [], "solver_diversity"))
        except OracleCeilingError:
            continue

        ov = list(result.oracle_dependent_values)
        truth = _extract(ov, "min_coins_ground_truth")
        if truth is None or not isinstance(truth, int):
            continue

        for s in solvers + reference:
            val = _extract(ov, f"{s}_output")
            agrees = _extract(ov, f"{s}_agrees_with_truth")
            if val is None or agrees is None:
                continue
            profiles[s].record(raw, val, truth)
            if agrees is False and truth != -1:
                diverge_map[s].add(idx)

    print("=" * 82)
    print("LC322 SOLVER DIVERSITY STRESS TEST — FAILURE PROFILE")
    print(f"Candidate space: {len(candidates)} instances (seed={SEED})")
    print("=" * 82)

    print(f"\n{'Solver':<22} {'Agree':>7} {'Diverge':>9} {'Unreach':>9} {'Rate':>8} {'Coverage':>12}")
    print("-" * 68)
    for s in solvers + reference:
        p = profiles[s]
        print(f"{p.name:<22} {p.agrees:>7} {p.diverges:>9} {p.unreachable:>9} {p.divergence_rate:>7.2%} {p.coverage:>12}")

    print("\n--- DIVERGENCE DETAILS (first 5 per solver) ---")
    for s in solvers + reference:
        p = profiles[s]
        print(f"\n{s}:")
        if not p.diverge_instances:
            print("  (no divergences)")
            continue
        for raw, sv, tv in p.diverge_instances[:5]:
            coins = list(raw[:-1])
            amt = raw[-1]
            print(f"  coins={coins}, amount={amt}: {s}={sv}, truth={tv}")

    print("\n\n--- OVERLAP ANALYSIS ---")
    print(f"{'Comparison':<50} {'Count':>8} {'Unique %':>10}")
    print("-" * 70)

    solver_groups = [
        ("dp + greedy (S1+2)", {"dp", "greedy"}),
        ("smallest_first", {"smallest_first"}),
        ("memo_collision", {"memo_collision"}),
        ("lookahead_one", {"lookahead_one"}),
        ("S3 (memo_collision + lookahead_one)", {"memo_collision", "lookahead_one"}),
        ("All S3 (smallest_first + memo_collision + lookahead_one)", {"smallest_first", "memo_collision", "lookahead_one"}),
        ("All 5 solvers", set(solvers + reference)),
    ]

    all_indices = set(range(len(candidates)))

    for label, group in solver_groups:
        members = [m for m in group if m in diverge_map]
        if not members:
            continue
        union: set[int] = set()
        for m in members:
            union |= diverge_map[m]
        intersection = union.copy()
        for m in members:
            intersection &= diverge_map[m]
        rest = all_indices - union
        unique_to_group = union.copy()
        for other_s in solvers + reference:
            if other_s not in members:
                unique_to_group -= diverge_map[other_s]

        print(f"\n{label}:")
        print(f"  Total diverging instances (union)          : {len(union):>4}")
        print(f"  All members diverge (intersection)        : {len(intersection):>4}")
        print(f"  Exclusive to this group (no other solver) : {len(unique_to_group):>4}")

        if unique_to_group:
            print("  Examples exclusive to group:")
            for idx in sorted(unique_to_group)[:5]:
                raw = raw_map[idx]
                coins = list(raw[:-1])
                amt = raw[-1]
                details = " | ".join(f"{m}={profiles[m].diverges if idx in diverge_map[m] else 'OK'}" for m in members)
                print(f"    idx={idx:>3} coins={coins}, amt={amt:>2}  [{details}]")

    print("\n\n--- INPUT CLASS CORRELATION ---")
    amount_divergences: dict[str, defaultdict[int, int]] = {
        s: defaultdict(int) for s in solvers + reference
    }
    coin_count_divergences: dict[str, defaultdict[int, int]] = {
        s: defaultdict(int) for s in solvers + reference
    }

    for s in solvers + reference:
        for idx in diverge_map[s]:
            raw = raw_map[idx]
            amt = raw[-1]
            n_coins = len(raw) - 1
            amount_divergences[s][amt] += 1
            coin_count_divergences[s][n_coins] += 1

    print(f"\n{'Solver':<22} {'Amt range (diverge)':<22} {'Frequent amts':>24}")
    print("-" * 70)
    for s in solvers + reference:
        ad = amount_divergences[s]
        if not ad:
            print(f"{s:<22} {'(none)':<22}")
            continue
        amts = sorted(ad.keys())
        amt_str = f"{min(amts)}-{max(amts)}" if len(amts) > 1 else str(amts[0])
        freq = sorted(ad.items(), key=lambda x: -x[1])[:3]
        freq_str = ", ".join(f"amt={a}({c})" for a, c in freq)
        print(f"{s:<22} {amt_str:<22} {freq_str:>24}")

    print(f"\n{'Solver':<22} {'|coins| range (diverge)':<24}")
    print("-" * 48)
    for s in solvers + reference:
        cd = coin_count_divergences[s]
        if not cd:
            print(f"{s:<22} {'(none)':<24}")
            continue
        keys = sorted(cd.keys())
        r = f"{min(keys)}-{max(keys)}" if len(keys) > 1 else str(keys[0])
        print(f"{s:<22} {r:<24}")

    print("\nDone.")


if __name__ == "__main__":
    run_diversity_analysis()

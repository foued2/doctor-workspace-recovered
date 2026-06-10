"""LC322 Bimaristan — failure geometry for Coin Change (LC322).

RECONSTRUCTED — original unrecoverable from PhotoRec.
Provides the LC322 class with invariant_families for run_lc322.py.

Family-to-manifold mapping (from A11 P3 perturbations):
  - greedy_dp_threshold: greedy_trap_no_subdivision
  - reachability_counterfactual: unreachable_greedy_confusion
  - large_amount_stress: large_coin_dominance_decoy
  - non_canonical_coin_order: (no reconstructed manifold)
  - forward_dp_overwrite: (no reconstructed manifold)
  - memo_cache_aliasing: (no reconstructed manifold)

All predicates use symbols from LC322_SYMBOL_REGISTRY only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Predicate:
    left: str
    operator: str
    right: str


@dataclass(frozen=True)
class Generator:
    generator_id: str
    generation_constraints: tuple[Predicate, ...]
    validation_predicates: tuple[Predicate, ...]


@dataclass(frozen=True)
class Manifold:
    manifold_id: str
    geometry_generators: tuple[Generator, ...]


@dataclass(frozen=True)
class InvariantFamily:
    family_id: str
    failure_manifolds: tuple[Manifold, ...]


# ── Predicates (LC322_SYMBOL_REGISTRY symbols only) ──────────────────

# Generation constraints — filter candidate space to LC322 domain
_GEN_AMOUNT_MIN = Predicate("amount", ">=", "6")
_GEN_AMOUNT_MAX = Predicate("amount", "<=", "20")
_GEN_COINS_MIN = Predicate("len(coins)", ">=", "3")
_GEN_COINS_MAX = Predicate("len(coins)", "<=", "5")

# Validation: greedy_trap_no_subdivision
# Identity: greedy overcounts on coin sets with no subdivision relationships
_VAL_GREEDY_OVERCOUNTS = Predicate("greedy_overcounts", "==", "True")
_VAL_NO_SUBDIVISION = Predicate("coin_set_no_subdivision", "==", "True")
_VAL_REACHABLE = Predicate("is_reachable", "==", "True")

# Validation: unreachable_greedy_confusion
# Identity: greedy diverges on instances where reachability is confused
_VAL_GREEDY_DIVERGES = Predicate("greedy_diverges", "==", "True")
_VAL_REACHABILITY_LOOKAHEAD_OVERCOUNTS = Predicate(
    "reachability_lookahead_overcounts", "==", "True"
)

# Validation: large_coin_dominance_decoy
# Identity: large coin dominates, amount stress reveals greedy failure
_VAL_OPTIMAL_EXCEEDS = Predicate(
    "optimal_coin_count_exceeds_coin_type_count", "==", "True"
)
_VAL_MODULO_ALIAS = Predicate("modulo_remainder_alias_present", "==", "True")

# ── Generators ────────────────────────────────────────────────────────

_GENERATION_CONSTRAINTS = (
    _GEN_AMOUNT_MIN,
    _GEN_AMOUNT_MAX,
    _GEN_COINS_MIN,
    _GEN_COINS_MAX,
)

_gen_greedy_trap = Generator(
    generator_id="greedy_trap_no_subdivision_gen",
    generation_constraints=_GENERATION_CONSTRAINTS,
    validation_predicates=(
        _VAL_REACHABLE,
        _VAL_NO_SUBDIVISION,
        _VAL_GREEDY_OVERCOUNTS,
    ),
)

_gen_unreachable = Generator(
    generator_id="unreachable_greedy_confusion_gen",
    generation_constraints=_GENERATION_CONSTRAINTS,
    validation_predicates=(
        _VAL_REACHABLE,
        _VAL_GREEDY_DIVERGES,
        _VAL_REACHABILITY_LOOKAHEAD_OVERCOUNTS,
    ),
)

_gen_large_coin = Generator(
    generator_id="large_coin_dominance_decoy_gen",
    generation_constraints=_GENERATION_CONSTRAINTS,
    validation_predicates=(
        _VAL_REACHABLE,
        _VAL_OPTIMAL_EXCEEDS,
        _VAL_MODULO_ALIAS,
    ),
)

# ── Manifolds ─────────────────────────────────────────────────────────

_manifold_greedy_trap = Manifold(
    manifold_id="greedy_trap_no_subdivision",
    geometry_generators=(_gen_greedy_trap,),
)

_manifold_unreachable = Manifold(
    manifold_id="unreachable_greedy_confusion",
    geometry_generators=(_gen_unreachable,),
)

_manifold_large_coin = Manifold(
    manifold_id="large_coin_dominance_decoy",
    geometry_generators=(_gen_large_coin,),
)

# ── Families (6 from P3 perturbations; 3 with reconstructed manifolds) ─

_family_greedy_dp = InvariantFamily(
    family_id="greedy_dp_threshold",
    failure_manifolds=(_manifold_greedy_trap,),
)

_family_reachability = InvariantFamily(
    family_id="reachability_counterfactual",
    failure_manifolds=(_manifold_unreachable,),
)

_family_large_amount = InvariantFamily(
    family_id="large_amount_stress",
    failure_manifolds=(_manifold_large_coin,),
)

_family_non_canonical = InvariantFamily(
    family_id="non_canonical_coin_order",
    failure_manifolds=(),
)

_family_forward_dp = InvariantFamily(
    family_id="forward_dp_overwrite",
    failure_manifolds=(),
)

_family_memo_cache = InvariantFamily(
    family_id="memo_cache_aliasing",
    failure_manifolds=(),
)


class LC322:
    invariant_families = (
        _family_greedy_dp,
        _family_reachability,
        _family_large_amount,
        _family_non_canonical,
        _family_forward_dp,
        _family_memo_cache,
    )

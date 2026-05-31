"""Validate provisional quarantine manifest and compute eligible queue."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from doctor.adversarial.structural_comparator import COMPARATOR_REGISTRY


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "quarantine_manifest.json"


VALID_COMPARATORS: set[str] = set(COMPARATOR_REGISTRY)


def _is_eligible(entry: dict[str, Any]) -> bool:
    comparator = entry.get("comparator")
    return (
        entry.get("source_confidence") == "confirmed"
        and entry.get("perturbation_family") == "multiset_invariant"
        and isinstance(comparator, str)
        and comparator in VALID_COMPARATORS
    )


def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    entries = data.get("entries")
    total_claimed = data.get("total_claimed")
    if not isinstance(entries, list):
        return ["entries must be a list"]
    if not isinstance(total_claimed, int):
        return ["total_claimed must be an int"]
    if len(entries) != total_claimed:
        errors.append(
            f"entries length mismatch: {len(entries)} != total_claimed ({total_claimed})"
        )

    allowed_conf = {"confirmed", "inferred", "unknown"}
    allowed_reason = {"memorization", "instability", "false_consensus", "unknown"}
    allowed_oracle = {
        "exact_numeric",
        "boolean_decision",
        "optimization_min",
        "optimization_max",
        "structural_equivalence",
        "unknown",
    }
    allowed_family = {
        "multiset_invariant",
        "ordering_invariant",
        "graph_label_invariant",
        "interval_equivalent",
        "reachability_preserving",
        "paired_conservation",
        "plateaumorphic_invariant",
        "minimum_margin_feasibility",
        "syntax_only",
        "none",
        "unknown",
    }

    allowed_invariant_class = {
        "scalar",
        "multiset",
        "nested_multiset",
        "order_sign_local",
        "paired_conservation",
        "reachability_boolean",
        "unknown",
    }
    allowed_risk_level = {"low", "medium", "high", "unknown"}
    allowed_confidence = {"high", "medium", "low", "unknown"}
    allowed_source = {"empirical", "exclusion_analysis", "heuristic_preclassification", "manual_design", "unknown"}
    allowed_evaluation_mode = {"perturbation_gate", "boundary_probe", "unknown"}

    seen_ids: set[int] = set()
    unknown_slots = 0
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{idx}] must be an object")
            continue

        pid = entry.get("id")
        if pid is None:
            unknown_slots += 1
        elif not isinstance(pid, int):
            errors.append(f"entries[{idx}].id must be int or null")
        elif pid in seen_ids:
            errors.append(f"duplicate id detected: {pid}")
        else:
            seen_ids.add(pid)

        if entry.get("source_confidence") not in allowed_conf:
            errors.append(f"entries[{idx}].source_confidence invalid")
        if entry.get("quarantine_reason") not in allowed_reason:
            errors.append(f"entries[{idx}].quarantine_reason invalid")
        if entry.get("oracle_shape") not in allowed_oracle:
            errors.append(f"entries[{idx}].oracle_shape invalid")
        if entry.get("perturbation_family") not in allowed_family:
            errors.append(f"entries[{idx}].perturbation_family invalid")
        if entry.get("lc_compatible") not in (True, False, None):
            errors.append(f"entries[{idx}].lc_compatible must be true/false/null")

        ic = entry.get("invariant_class")
        if ic is not None and ic not in allowed_invariant_class:
            errors.append(f"entries[{idx}].invariant_class invalid: {ic!r}")
        ir = entry.get("invariant_risk_level")
        if ir is not None and ir not in allowed_risk_level:
            errors.append(f"entries[{idx}].invariant_risk_level invalid: {ir!r}")
        conf = entry.get("confidence")
        if conf is not None and conf not in allowed_confidence:
            errors.append(f"entries[{idx}].confidence invalid: {conf!r}")
        src = entry.get("source")
        if src is not None and src not in allowed_source:
            errors.append(f"entries[{idx}].source invalid: {src!r}")
        ev = entry.get("evaluation_mode")
        if ev is not None and ev not in allowed_evaluation_mode:
            errors.append(f"entries[{idx}].evaluation_mode invalid: {ev!r}")

        comparator = entry.get("comparator")
        if comparator is not None and comparator not in VALID_COMPARATORS:
            errors.append(
                f"entries[{idx}].comparator invalid: {comparator!r}. "
                f"must be one of {sorted(VALID_COMPARATORS)}"
            )

    if unknown_slots != (total_claimed - len(seen_ids)):
        errors.append(
            "unknown slot count mismatch: expected "
            f"{total_claimed - len(seen_ids)}, found {unknown_slots}"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate quarantine manifest and print processing queue."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to quarantine manifest JSON.",
    )
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate_manifest(data)

    entries = data.get("entries", [])
    eligible = sorted(
        entry["id"] for entry in entries if isinstance(entry.get("id"), int) and _is_eligible(entry)
    )

    print(f"manifest: {args.manifest}")
    print(f"total_claimed: {data.get('total_claimed')}")
    print(f"entries: {len(entries)}")
    print(f"eligible_queue: {eligible}")

    if errors:
        print("status: invalid")
        for err in errors:
            print(f"- {err}")
        return 1

    print("status: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

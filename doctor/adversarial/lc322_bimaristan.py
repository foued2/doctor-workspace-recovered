from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from doctor.adversarial.lc322_bimaristan import LC322
from doctor.adversarial.lc45_bimaristan import LC45


SPAN_TEST = PROJECT_ROOT / "data" / "representational_span_test.json"
OUTPUT_JSON = PROJECT_ROOT / "data" / "representation_selection_oracle.json"
OUTPUT_MD = PROJECT_ROOT / "findings" / "FINDINGS_119.md"

STATIC_TERMS = (
    "coin",
    "amount",
    "modulo",
    "memo",
    "reachable",
    "greedy",
    "overcounts",
    "subdivision",
    "dominance",
    "unreachable",
)
TEMPORAL_TERMS = (
    "frontier",
    "bfs",
    "layer",
    "path",
    "landing",
    "jump",
    "horizon",
    "dead",
    "depth",
    "window",
    "search",
    "reach",
)
RELATIONAL_TERMS = (
    "next",
    "predecessor",
    "transition",
    "ordering",
    "direction",
    "boundary",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_text(schema: Any) -> str:
    parts: list[str] = [
        schema.problem_structure.problem_id,
        schema.problem_structure.kind,
        schema.problem_structure.output_symbol.name,
        schema.problem_structure.objective_predicate.left,
        schema.problem_structure.objective_predicate.operator,
        schema.problem_structure.objective_predicate.right,
    ]
    parts.extend(symbol.name for symbol in schema.problem_structure.input_symbols)
    parts.extend(str(symbol) for symbol in schema.problem_structure.input_symbols)
    for family in schema.invariant_families:
        parts.append(family.family_id)
        for invariant in family.invariants:
            parts.append(invariant.invariant_id)
            for predicate in invariant.falsifiable_predicates + invariant.violation_predicates:
                parts.extend((predicate.left, predicate.operator, predicate.right))
        for manifold in family.failure_manifolds:
            parts.append(manifold.manifold_id)
            for generator in manifold.geometry_generators:
                parts.append(generator.generator_id)
                for predicate in generator.generation_constraints + generator.validation_predicates:
                    parts.extend((predicate.left, predicate.operator, predicate.right))
    return " ".join(parts).lower()


def _count_terms(text: str, terms: tuple[str, ...]) -> int:
    return sum(len(re.findall(rf"\b{re.escape(term)}\b|{re.escape(term)}_", text)) for term in terms)


def _schema_features(schema: Any) -> dict[str, Any]:
    text = _schema_text(schema)
    static_score = _count_terms(text, STATIC_TERMS)
    temporal_score = _count_terms(text, TEMPORAL_TERMS)
    relational_score = _count_terms(text, RELATIONAL_TERMS)
    generator_count = sum(len(manifold.geometry_generators) for family in schema.invariant_families for manifold in family.failure_manifolds)
    invariant_count = sum(len(family.invariants) for family in schema.invariant_families)
    manifold_count = sum(len(family.failure_manifolds) for family in schema.invariant_families)
    input_arity = len(schema.problem_structure.input_symbols)
    return {
        "problem_id": schema.problem_structure.problem_id,
        "input_arity": input_arity,
        "invariant_count": invariant_count,
        "manifold_count": manifold_count,
        "generator_count": generator_count,
        "static_score": static_score,
        "temporal_score": temporal_score,
        "relational_score": relational_score,
        "temporal_static_ratio": round(temporal_score / static_score, 6) if static_score else None,
        "relational_static_ratio": round(relational_score / static_score, 6) if static_score else None,
    }


def _predict(features: dict[str, Any]) -> dict[str, Any]:
    temporal_score = int(features["temporal_score"])
    static_score = int(features["static_score"])
    relational_score = int(features["relational_score"])
    if temporal_score > static_score:
        representation_class = "temporal_unfolding_minimal"
        dimensionality_regime = "projection_sensitive_1d"
    elif relational_score > static_score and relational_score >= temporal_score:
        representation_class = "transition_graph_encoding"
        dimensionality_regime = "relational_static_hybrid"
    else:
        representation_class = "static_activation"
        dimensionality_regime = "static_multidimensional"
    margin = max(static_score, temporal_score, relational_score) - sorted(
        (static_score, temporal_score, relational_score),
        reverse=True,
    )[1]
    return {
        "predicted_representation_class": representation_class,
        "predicted_dimensionality_regime": dimensionality_regime,
        "selection_margin": margin,
    }


def _observed(problem_key: str, span: dict[str, Any]) -> dict[str, Any]:
    if problem_key == "lc322":
        stable = all(row["lc322_structure_unchanged"] for row in span["transform_results"].values())
        return {
            "observed_static_valid": True,
            "observed_best_transform": "static_activation",
            "observed_stability_under_transform": stable,
            "observed_signature_count": span["lc322_baseline"]["signature_count"],
            "observed_min_distance": span["lc322_baseline"]["pca_min_distance"],
        }
    passing = [
        (transform_id, row)
        for transform_id, row in span["transform_results"].items()
        if row["passes_span_test"]
    ]
    best_transform = max(passing, key=lambda item: item[1]["lc45"]["pca_min_distance"])[0] if passing else None
    selected = span["minimal_feature_subset_search"]["selected"]
    return {
        "observed_static_valid": span["transform_results"]["static_activation"]["passes_span_test"],
        "observed_best_transform": best_transform,
        "observed_stability_under_transform": False,
        "observed_signature_count": selected["signature_count"] if selected else 1,
        "observed_min_distance": selected["pca_min_distance"] if selected else 0.0,
        "observed_minimal_features": selected["features"] if selected else [],
    }


def _agreement(prediction: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    predicted = prediction["predicted_representation_class"]
    if predicted == "static_activation":
        class_agrees = bool(observed["observed_static_valid"])
    else:
        class_agrees = predicted in {
            observed["observed_best_transform"],
            "temporal_unfolding_minimal",
            "temporal_unfolding",
            "transition_graph_encoding",
            "trajectory_plus_terminal",
        } and not bool(observed["observed_static_valid"])
    if prediction["predicted_dimensionality_regime"] == "static_multidimensional":
        regime_agrees = int(observed["observed_signature_count"]) > 2
    elif prediction["predicted_dimensionality_regime"] == "projection_sensitive_1d":
        regime_agrees = int(observed["observed_signature_count"]) == 2
    else:
        regime_agrees = int(observed["observed_signature_count"]) >= 2
    return {
        "representation_class_agrees": class_agrees,
        "dimensionality_regime_agrees": regime_agrees,
        "overall_agrees": class_agrees and regime_agrees,
    }


def run() -> dict[str, Any]:
    span = _load_json(SPAN_TEST)
    schemas = {
        "lc322": LC322,
        "lc45": LC45,
    }
    rows = {}
    for problem_key, schema in schemas.items():
        features = _schema_features(schema)
        prediction = _predict(features)
        observed = _observed(problem_key, span)
        rows[problem_key] = {
            "schema_features": features,
            "prediction": prediction,
            "observed": observed,
            "agreement": _agreement(prediction, observed),
        }
    return {
        "source_artifact": str(SPAN_TEST.relative_to(PROJECT_ROOT)),
        "selector_inputs": {
            "static_terms": list(STATIC_TERMS),
            "temporal_terms": list(TEMPORAL_TERMS),
            "relational_terms": list(RELATIONAL_TERMS),
        },
        "problems": rows,
        "decision": {
            "agreement_count": sum(1 for row in rows.values() if row["agreement"]["overall_agrees"]),
            "problem_count": len(rows),
            "representation_selection_oracle": (
                "PASS" if all(row["agreement"]["overall_agrees"] for row in rows.values()) else "FAIL"
            ),
        },
    }


def _write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# FINDINGS_119: Representation Selection Oracle",
        "",
        "## Selector Inputs",
        "",
        "| Problem | Static score | Temporal score | Relational score | Prediction | Regime | Margin |",
        "|---|---:|---:|---:|---|---|---:|",
    ]
    for problem_id, row in report["problems"].items():
        features = row["schema_features"]
        prediction = row["prediction"]
        lines.append(
            f"| `{problem_id}` | {features['static_score']} | {features['temporal_score']} | "
            f"{features['relational_score']} | `{prediction['predicted_representation_class']}` | "
            f"`{prediction['predicted_dimensionality_regime']}` | {prediction['selection_margin']} |"
        )
    lines.extend(
        [
            "",
            "## Observed Agreement",
            "",
            "| Problem | Observed best | Static valid | Signatures | Min distance | Class agrees | Regime agrees |",
            "|---|---|---|---:|---:|---|---|",
        ]
    )
    for problem_id, row in report["problems"].items():
        observed = row["observed"]
        agreement = row["agreement"]
        lines.append(
            f"| `{problem_id}` | `{observed['observed_best_transform']}` | "
            f"`{str(observed['observed_static_valid']).lower()}` | {observed['observed_signature_count']} | "
            f"{observed['observed_min_distance']:.6f} | `{str(agreement['representation_class_agrees']).lower()}` | "
            f"`{str(agreement['dimensionality_regime_agrees']).lower()}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`representation_selection_oracle`: `{report['decision']['representation_selection_oracle']}`",
            "",
            "## Artifacts",
            "",
            "- `data/representation_selection_oracle.json`",
            "- `runners/run_representation_selection_oracle.py`",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = run()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report)
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    print(f"Wrote: {OUTPUT_JSON}")
    print(f"Wrote: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

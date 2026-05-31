"""
Validation harness for doctor/schema_classifier.py::classify_schema(statement).

Measures statement -> topic accuracy using the in-distribution few-shot dataset
extracted from the classifier's own prompt.

Does NOT connect to Doctor evaluator claims.
Does NOT reuse LC322 taxonomy accuracy.
Does NOT use static manifest tags as predictions.
Does NOT count keyword heuristics.
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from doctor.schema_classifier import classify_schema

DATASET_PATH = ROOT / "data" / "schema_classifier_few_shot_dataset.json"
OUTPUT_PATH = ROOT / "data" / "schema_classifier_eval.json"


def load_dataset(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["examples"], data["meta"]


def run_evaluation(examples: list[dict]) -> dict:
    results = []
    parse_failures = 0

    for ex in examples:
        sid = ex["id"]
        statement = ex["statement"]
        try:
            prediction = classify_schema(statement)
        except Exception as e:
            results.append({
                "id": sid,
                "statement": statement,
                "ground_truth": {
                    "domain": ex["domain"],
                    "paradigm": ex["paradigm"],
                    "dp_type": ex["dp_type"],
                    "confidence": ex["confidence"],
                },
                "prediction": None,
                "error": str(e),
                "parse_failure": True,
            })
            parse_failures += 1
            continue

        has_error = "error" in prediction and prediction["error"]
        results.append({
            "id": sid,
            "statement": statement,
            "ground_truth": {
                "domain": ex["domain"],
                "paradigm": ex["paradigm"],
                "dp_type": ex["dp_type"],
                "confidence": ex["confidence"],
            },
            "prediction": {
                "domain": prediction.get("domain", ""),
                "paradigm": prediction.get("paradigm", ""),
                "dp_type": prediction.get("dp_type", ""),
                "confidence": prediction.get("confidence", ""),
            },
            "error": prediction.get("error", ""),
            "parse_failure": has_error,
        })
        if has_error:
            parse_failures += 1

    total = len(examples)
    evaluated = total - parse_failures

    domain_correct = 0
    paradigm_correct = 0
    joint_correct = 0
    y_true_domain = []
    y_pred_domain = []
    y_true_paradigm = []
    y_pred_paradigm = []

    for r in results:
        if r["parse_failure"]:
            continue
        gt = r["ground_truth"]
        pred = r["prediction"]

        if pred["domain"] == gt["domain"]:
            domain_correct += 1
        y_true_domain.append(gt["domain"])
        y_pred_domain.append(pred["domain"] if pred["domain"] else "(empty)")

        if pred["paradigm"] == gt["paradigm"]:
            paradigm_correct += 1
        y_true_paradigm.append(gt["paradigm"])
        y_pred_paradigm.append(pred["paradigm"] if pred["paradigm"] else "(empty)")

        if pred["domain"] == gt["domain"] and pred["paradigm"] == gt["paradigm"]:
            joint_correct += 1

    domain_acc = domain_correct / evaluated if evaluated > 0 else 0.0
    paradigm_acc = paradigm_correct / evaluated if evaluated > 0 else 0.0
    joint_acc = joint_correct / evaluated if evaluated > 0 else 0.0

    # Manually compute macro F1 and confusion matrix
    def _macro_f1(true, pred, labels):
        f1_scores = []
        for label in labels:
            tp = sum(1 for i in range(len(true)) if true[i] == label and pred[i] == label)
            fp = sum(1 for i in range(len(true)) if true[i] != label and pred[i] == label)
            fn = sum(1 for i in range(len(true)) if true[i] == label and pred[i] != label)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_scores.append(f1)
        return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0

    def _confusion_matrix(true, pred, labels):
        n = len(labels)
        cm = [[0] * n for _ in range(n)]
        label_index = {l: i for i, l in enumerate(labels)}
        for t, p in zip(true, pred):
            i = label_index.get(t, -1)
            j = label_index.get(p, -1)
            if i >= 0 and j >= 0:
                cm[i][j] += 1
        return cm

    domain_labels = sorted(set(y_true_domain))
    domain_f1 = _macro_f1(y_true_domain, y_pred_domain, domain_labels)

    paradigm_labels = sorted(set(y_true_paradigm))
    paradigm_f1 = _macro_f1(y_true_paradigm, y_pred_paradigm, paradigm_labels)

    domain_cm = _confusion_matrix(y_true_domain, y_pred_domain, domain_labels) if evaluated > 0 else []
    paradigm_cm = _confusion_matrix(y_true_paradigm, y_pred_paradigm, paradigm_labels) if evaluated > 0 else []

    # Confidence analysis
    confidence_results = []
    for r in results:
        if r["parse_failure"]:
            continue
        gt = r["ground_truth"]
        pred = r["prediction"]
        correct = pred["domain"] == gt["domain"] and pred["paradigm"] == gt["paradigm"]
        confidence_results.append({
            "id": r["id"],
            "reported_confidence": pred.get("confidence", ""),
            "joint_correct": correct,
            "domain_correct": pred["domain"] == gt["domain"],
            "paradigm_correct": pred["paradigm"] == gt["paradigm"],
        })

    # Confidence vs correctness table
    conf_table = {}
    for cr in confidence_results:
        conf = cr["reported_confidence"]
        if conf not in conf_table:
            conf_table[conf] = {"total": 0, "joint_correct": 0}
        conf_table[conf]["total"] += 1
        if cr["joint_correct"]:
            conf_table[conf]["joint_correct"] += 1
    confidence_vs_correctness = {}
    for conf, counts in sorted(conf_table.items()):
        confidence_vs_correctness[conf] = {
            "total": counts["total"],
            "joint_correct": counts["joint_correct"],
            "joint_accuracy": round(counts["joint_correct"] / counts["total"], 4) if counts["total"] > 0 else 0.0,
        }

    # Average reported confidence (high=1.0, low=0.0)
    conf_scores = []
    for cr in confidence_results:
        if cr["reported_confidence"] == "high":
            conf_scores.append(1.0)
        elif cr["reported_confidence"] == "low":
            conf_scores.append(0.0)
    avg_reported_confidence = round(sum(conf_scores) / len(conf_scores), 4) if conf_scores else None

    # Per-domain accuracy breakdown
    domain_breakdown = {}
    for label in domain_labels:
        correct_count = sum(1 for i in range(len(y_true_domain)) if y_true_domain[i] == label and y_pred_domain[i] == label)
        total_count = y_true_domain.count(label)
        domain_breakdown[label] = {
            "total": total_count,
            "correct": correct_count,
            "accuracy": round(correct_count / total_count, 4) if total_count > 0 else 0.0,
        }

    # Per-paradigm accuracy breakdown
    paradigm_breakdown = {}
    for label in paradigm_labels:
        correct_count = sum(1 for i in range(len(y_true_paradigm)) if y_true_paradigm[i] == label and y_pred_paradigm[i] == label)
        total_count = y_true_paradigm.count(label)
        paradigm_breakdown[label] = {
            "total": total_count,
            "correct": correct_count,
            "accuracy": round(correct_count / total_count, 4) if total_count > 0 else 0.0,
        }

    def _nullify_if_zero(val):
        return None if evaluated == 0 else val

    return {
        "total_evaluated": total,
        "parse_failures": parse_failures,
        "successfully_evaluated": evaluated,
        "top_1_domain_accuracy": _nullify_if_zero(round(domain_acc, 4)),
        "top_1_paradigm_accuracy": _nullify_if_zero(round(paradigm_acc, 4)),
        "joint_domain_paradigm_accuracy": _nullify_if_zero(round(joint_acc, 4)),
        "domain_macro_f1": _nullify_if_zero(round(domain_f1, 4)),
        "paradigm_macro_f1": _nullify_if_zero(round(paradigm_f1, 4)),
        "average_reported_confidence": avg_reported_confidence,
        "domain_breakdown": _nullify_if_zero(domain_breakdown),
        "paradigm_breakdown": _nullify_if_zero(paradigm_breakdown),
        "confidence_vs_correctness": confidence_vs_correctness,
        "confusion_matrix_domain": {
            "labels": domain_labels,
            "matrix": domain_cm,
        },
        "confusion_matrix_paradigm": {
            "labels": paradigm_labels,
            "matrix": paradigm_cm,
        },
        "per_example_results": results,
        "confidence_analysis": confidence_results,
    }


def check_llm_available() -> bool:
    """Check if any LLM API key is configured."""
    has_groq = bool(os.environ.get("GROQ_API_KEY", ""))
    has_google = bool(os.environ.get("GOOGLE_API_KEY", ""))
    has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY", ""))
    return has_groq or has_google or has_openrouter


def main():
    examples, meta = load_dataset(DATASET_PATH)

    if not check_llm_available():
        report = {
            "status": "SKIPPED",
            "reason": "No LLM API key configured (GROQ_API_KEY, GOOGLE_API_KEY, or OPENROUTER_API_KEY). Cannot call classify_schema which requires an LLM.",
            "dataset": meta,
            "total_evaluated": 0,
            "parse_failures": 0,
            "successfully_evaluated": 0,
            "top_1_domain_accuracy": None,
            "top_1_paradigm_accuracy": None,
            "joint_domain_paradigm_accuracy": None,
            "domain_macro_f1": None,
            "paradigm_macro_f1": None,
            "average_reported_confidence": None,
            "domain_breakdown": {},
            "paradigm_breakdown": {},
            "confidence_vs_correctness": {},
            "confusion_matrix_domain": None,
            "confusion_matrix_paradigm": None,
            "per_example_results": [],
            "confidence_analysis": [],
            "api_auth_failure": False,
        }
    else:
        report = run_evaluation(examples)
        n_attempted = report["total_evaluated"]
        n_ok = report["successfully_evaluated"]
        if n_attempted > 0 and n_ok == 0:
            # All attempts failed — likely API auth or connectivity issue
            report["status"] = "API_UNAVAILABLE"
            report["reason"] = "LLM API key was set but all calls failed (auth/rate-limit/connectivity). Check API credentials."
        elif n_ok > 0 and n_ok < n_attempted:
            report["status"] = "PARTIAL"
            report["reason"] = ""
        else:
            report["status"] = "COMPLETE"
            report["reason"] = ""
        report["dataset"] = meta

    output = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "harness": "scratch/_run_schema_eval.py",
        "classifier_under_test": "doctor/schema_classifier.py::classify_schema",
        **report,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Written {OUTPUT_PATH}")
    print(json.dumps({k: v for k, v in output.items() if k in (
        "status", "total_evaluated", "parse_failures", "successfully_evaluated",
        "top_1_domain_accuracy", "top_1_paradigm_accuracy", "joint_domain_paradigm_accuracy",
        "domain_macro_f1", "paradigm_macro_f1", "average_reported_confidence",
    )}, indent=2))


if __name__ == "__main__":
    main()

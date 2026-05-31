"""
Enhanced Evaluator
==================
Extends the strict evaluator with stress-testing specific metrics:

1. Robustness score: accuracy(noisy) / accuracy(clean)
2. Degradation curve: accuracy at each noise level
3. Failure diversity: How varied the failures are (not all same pattern)
4. Recovery ability: Success rate after initial failure
5. Stress kind breakdown: Performance by stress type
6. Failure pattern analysis: What kinds of failures occur
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

from external_stress_layer import StressMetrics, StressKind


# ===========================================================================
# PHASE 2 — Rule Violation Detection (Step 2.1)
# Three executable rule checks that detect integrity violations in Doctor reasoning.
# ===========================================================================


def detect_rule_violations(
    case: Any,  # StressCase
    prediction: Dict[str, Any],
) -> List[str]:
    """Detect rule violations in a Doctor prediction.

    Three rules are checked:

    R1 — Contradiction blindness:
         Case contains contradiction signal AND doctor verdict is correct/partial
         AND doctor reasoning does not mention contradiction.

    R2 — Corruption trust:
         Case has corrupted label flag AND doctor verdict used sample evidence.

    R3 — False confidence:
         Ground truth is undefined AND doctor returned correct or partial.

    Args:
        case: StressCase object with ground_truth and metadata
        prediction: Dict from doctor.predict() with label, confidence, etc.

    Returns:
        List of violated rule strings: ["R1"], ["R2", "R3"], [], etc.
    """
    violations = []

    truth = case.ground_truth
    label = prediction["label"]
    raw_conf = prediction.get("confidence", 0.0)
    confidence = float(raw_conf) if raw_conf is not None else 0.0
    decision_path = prediction.get("decision_path", [])
    prompt = case.prompt.lower()

    # ── R1: Contradiction blindness ──────────────────────────────────────────
    # Case contains contradiction signal (explicit contradiction patterns in prompt)
    # AND doctor verdict is correct or partial
    # AND doctor reasoning does not mention contradiction
    contradiction_patterns = [
        "contradict", "conflict", "inconsistent", "incompatible",
        "mutually exclusive", "cannot both", "disagree"
    ]
    has_contradiction_signal = any(pat in prompt for pat in contradiction_patterns)

    # Also check case metadata for contradiction flag (supports both old and new flag names)
    has_contradiction_meta = (
        case.metadata.get("contradiction", False) or
        case.metadata.get("has_contradiction", False)
    )

    if has_contradiction_signal or has_contradiction_meta:
        if label in ("correct", "partial"):
            # Check if doctor reasoning mentions contradiction
            decision_path_str = " ".join(decision_path).lower()
            mentions_contradiction = any(
                keyword in decision_path_str
                for keyword in ["contradict", "conflict", "R2", "conflicting_examples"]
            )

            if not mentions_contradiction:
                violations.append("R1")

    # ── R2: Corruption trust ─────────────────────────────────────────────────
    # Case has corrupted label flag AND doctor verdict used sample evidence
    # FIX: Also detect when Doctor classifies corrupted cases as "correct" without
    # flagging the corruption — this is the core R2 violation
    has_corrupted_label = (
        case.metadata.get("corrupted_label", False) or
        case.metadata.get("has_corrupted_label", False)
    )
    used_sample_evidence = prediction.get("used_sample_output", False)

    # Also check if decision path mentions using examples/samples
    decision_path_str = " ".join(decision_path).lower()
    mentions_sample = any(
        keyword in decision_path_str
        for keyword in ["sample", "example", "expected_output"]
    )

    # FIX: R2 also fires when corrupted label case has conflicting_examples evidence
    # and Doctor resolves it (R2 rule fires) — this means Doctor is using corrupted evidence
    has_corrupted_label_and_conflict = (
        has_corrupted_label and
        "r2:conflicting_examples_resolved" in decision_path_str
    )

    # FIX: R2 also fires when corrupted label case is classified as "correct"
    # without the Doctor flagging the corruption
    corrupted_but_not_flagged = (
        has_corrupted_label and
        label == "correct" and
        not prediction.get("conflict_detected", False)
    )

    if has_corrupted_label and (used_sample_evidence or mentions_sample or has_corrupted_label_and_conflict or corrupted_but_not_flagged):
        violations.append("R2")

    # ── R3: False confidence ─────────────────────────────────────────────────
    # Ground truth is undefined AND doctor returned correct or partial
    if truth == "undefined" and label in ("correct", "partial"):
        violations.append("R3")

    return violations


# ===========================================================================
# PHASE 5 — Second-Pass Evaluation: Correct-by-Luck Detection
# ===========================================================================

def second_pass_eval(case: Any, prediction: Dict[str, Any]) -> Dict[str, Any]:
    """Second-pass evaluation independent of verdict correctness.
    
    Checks whether the Doctor got the right answer for the right reason.
    A Doctor can return the correct verdict but for broken reasoning.
    
    Returns dict with:
        - verdict_correct: bool
        - reasoning_sound: bool
        - rule_violations: list of rule strings
        - failure_mode: "sound" | "correct_by_luck" | "wrong_with_violation"
    """
    truth = case.ground_truth
    label = prediction["label"]
    raw_conf = prediction.get("confidence", 0.0)
    confidence = float(raw_conf) if raw_conf is not None else 0.0

    verdict_correct = (label == truth)
    violations = detect_rule_violations(case, prediction)
    
    # Check if reasoning is sound
    # Reasoning is unsound if rule violations exist even when verdict is correct
    reasoning_sound = len(violations) == 0
    
    # Determine failure mode
    if verdict_correct and reasoning_sound:
        failure_mode = "sound"
    elif verdict_correct and not reasoning_sound:
        failure_mode = "correct_by_luck"
    elif not verdict_correct and reasoning_sound:
        failure_mode = "honest_error"
    else:
        failure_mode = "wrong_with_violation"
    
    return {
        "verdict_correct": verdict_correct,
        "reasoning_sound": reasoning_sound,
        "rule_violations": violations,
        "failure_mode": failure_mode,
    }


# ===========================================================================
# PHASE 5 — Calibration Tracking
# ===========================================================================

def compute_calibration(cases: List[Any], predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute calibration breakdown per verdict class.
    
    Tracks:
        - correct_verdicts_high_confidence: confidence >= 0.7 AND verdict correct
        - correct_verdicts_low_confidence: confidence < 0.7 AND verdict correct
        - wrong_verdicts_high_confidence: confidence >= 0.7 AND verdict wrong  ← most dangerous
        - wrong_verdicts_low_confidence: confidence < 0.7 AND verdict wrong
    
    Flags runs where wrong_verdicts_high_confidence > 20% of total wrong verdicts.
    """
    cal = {
        "correct_verdicts_high_confidence": 0,
        "correct_verdicts_low_confidence": 0,
        "wrong_verdicts_high_confidence": 0,
        "wrong_verdicts_low_confidence": 0,
    }
    
    # Per-verdict-class breakdown
    by_verdict = defaultdict(lambda: {"correct_high": 0, "correct_low": 0, "wrong_high": 0, "wrong_low": 0})
    
    for case, pred in zip(cases, predictions):
        truth = case.ground_truth
        label = pred["label"]
        raw_conf = pred.get("confidence", 0.0)
        confidence = float(raw_conf) if raw_conf is not None else 0.0
        matched = (label == truth)
        high_conf = confidence >= 0.7
        
        if matched and high_conf:
            cal["correct_verdicts_high_confidence"] += 1
            by_verdict[label]["correct_high"] += 1
        elif matched and not high_conf:
            cal["correct_verdicts_low_confidence"] += 1
            by_verdict[label]["correct_low"] += 1
        elif not matched and high_conf:
            cal["wrong_verdicts_high_confidence"] += 1
            by_verdict[label]["wrong_high"] += 1
        else:
            cal["wrong_verdicts_low_confidence"] += 1
            by_verdict[label]["wrong_low"] += 1
    
    # Flag dangerous overconfidence
    total_wrong = cal["wrong_verdicts_high_confidence"] + cal["wrong_verdicts_low_confidence"]
    wrong_high_conf_pct = (
        cal["wrong_verdicts_high_confidence"] / total_wrong if total_wrong > 0 else 0.0
    )
    cal["wrong_high_confidence_pct"] = round(wrong_high_conf_pct, 4)
    cal["flag_dangerous_overconfidence"] = wrong_high_conf_pct > 0.20
    
    # Per-verdict breakdown
    cal["by_verdict"] = dict(by_verdict)
    
    return cal


# ===========================================================================
# PHASE 5 — Distribution Shift Detection
# ===========================================================================

def compute_distribution_shift(
    cases: List[Any],
    predictions: List[Dict[str, Any]],
    stress_kind_field: str = "stress_kind",
) -> Dict[str, Any]:
    """Compute distribution shift between ESL and internal generator accuracy.
    
    ESL cases are the real-world anchor. If internal accuracy diverges
    significantly from ESL accuracy, the generator is producing cases
    that don't reflect real-world difficulty.
    
    shift_score = |ESL_accuracy - internal_accuracy| / ESL_accuracy
    
    If shift_score > 0.4, flag for novelty injection.
    """
    from enum import Enum
    
    # Group by stress kind
    esl_correct = 0
    esl_total = 0
    internal_correct = 0
    internal_total = 0
    
    for case, pred in zip(cases, predictions):
        truth = case.ground_truth
        label = pred["label"]
        matched = (label == truth)
        
        # Get stress kind — handle both enum and string forms
        kind = case.stress_kind
        if isinstance(kind, Enum):
            kind_name = kind.name
        else:
            kind_name = str(kind)
        
        if kind_name in ("REAL_WORLD", "CROSS_DOMAIN", "HUMAN_CRAFTED"):
            # ESL cases
            esl_total += 1
            if matched:
                esl_correct += 1
        else:
            # Internal generator cases
            internal_total += 1
            if matched:
                internal_correct += 1
    
    esl_accuracy = esl_correct / esl_total if esl_total > 0 else None
    internal_accuracy = internal_correct / internal_total if internal_total > 0 else None
    
    # Compute shift score
    if esl_accuracy is not None and internal_accuracy is not None and esl_accuracy > 0:
        shift_score = abs(esl_accuracy - internal_accuracy) / esl_accuracy
    else:
        shift_score = None
    
    # Flag for novelty injection
    needs_novelty_injection = shift_score is not None and shift_score > 0.4
    
    return {
        "esl_accuracy": round(esl_accuracy, 4) if esl_accuracy is not None else None,
        "esl_total": esl_total,
        "internal_accuracy": round(internal_accuracy, 4) if internal_accuracy is not None else None,
        "internal_total": internal_total,
        "shift_score": round(shift_score, 4) if shift_score is not None else None,
        "needs_novelty_injection": needs_novelty_injection,
    }


def _entropy(values: List[float], bins: int = 4) -> float:
    """Calculate normalized entropy of a distribution."""
    if not values:
        return 0.0
    counts = [0] * bins
    for value in values:
        index = min(int(value * bins), bins - 1)
        counts[index] += 1
    total = sum(counts)
    entropy = 0.0
    for count in counts:
        if count == 0:
            continue
        probability = count / total
        entropy -= probability * math.log(probability, 2)
    return round(entropy / math.log(bins, 2), 4) if bins > 1 else 0.0


def _jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


class EnhancedEvaluator:
    """Evaluates Doctor performance under stress with extended metrics.
    
    Provides all standard evaluator metrics plus:
    - Robustness score
    - Degradation curves
    - Failure diversity
    - Recovery rate
    - Stress kind breakdown
    - Failure pattern analysis
    """
    
    def evaluate_batch(
        self,
        cases: List[Any],  # StressCase objects
        predictions: List[Dict[str, Any]],
    ) -> StressMetrics:
        """Evaluate a batch of predictions with stress-testing metrics.
        
        Args:
            cases: List of StressCase objects
            predictions: List of prediction dicts from Doctor
            
        Returns:
            StressMetrics with comprehensive evaluation
        """
        metrics = StressMetrics()
        metrics.total_cases = len(cases)
        
        if not cases or not predictions:
            return metrics
        
        # Basic metrics
        exact_matches = []
        overconfident = 0
        underconfident = 0
        
        # Stress-specific tracking
        by_stress_kind = defaultdict(lambda: {"correct": 0, "total": 0})
        by_noise_level = defaultdict(lambda: {"correct": 0, "total": 0})
        failure_patterns = Counter()
        by_source_domain = defaultdict(lambda: {"correct": 0, "total": 0})
        
        # PHASE 2: Rule violation tracking
        rule_violation_counts = Counter()  # Count each rule violation
        rule_violation_cases = []  # Store cases with rule violations for analysis
        
        for case, prediction in zip(cases, predictions):
            truth = case.ground_truth
            label = prediction["label"]
            raw_conf = prediction.get("confidence", 0.0)
            confidence = float(raw_conf) if raw_conf is not None else 0.0
            matched = label == truth
            
            exact_matches.append(1.0 if matched else 0.0)
            
            # Over/under confidence
            if not matched and confidence >= 0.8:
                overconfident += 1
            if matched and confidence <= 0.4:
                underconfident += 1
            
            # Track by stress kind
            kind_name = case.stress_kind.name
            by_stress_kind[kind_name]["total"] += 1
            if matched:
                by_stress_kind[kind_name]["correct"] += 1
            
            # Track by noise level
            noise_level = case.noise_level
            by_noise_level[noise_level]["total"] += 1
            if matched:
                by_noise_level[noise_level]["correct"] += 1
            
            # Track failure patterns
            if not matched:
                pattern = self._classify_failure(case, prediction)
                failure_patterns[pattern] += 1
                case.failure_pattern = pattern

            # PHASE 2: Detect rule violations for ALL cases (not just failures)
            # Rule violations are about reasoning integrity, not just verdict accuracy
            violations = detect_rule_violations(case, prediction)
            if violations:
                for v in violations:
                    rule_violation_counts[v] += 1
                rule_violation_cases.append({
                    "case_id": case.case_id,
                    "violations": violations,
                    "ground_truth": truth,
                    "doctor_label": label,
                    "confidence": confidence,
                })
            
            # Track by source domain (if available)
            source_domain = case.metadata.get("source_domain", case.metadata.get("source_type", "unknown"))
            by_source_domain[source_domain]["total"] += 1
            if matched:
                by_source_domain[source_domain]["correct"] += 1
        
        # Calculate standard metrics
        metrics.accuracy = round(sum(exact_matches) / len(exact_matches), 4) if exact_matches else 0.0
        metrics.overconfidence_rate = round(overconfident / len(predictions), 4) if predictions else 0.0
        metrics.underconfidence_rate = round(underconfident / len(predictions), 4) if predictions else 0.0
        metrics.correct_cases = sum(exact_matches)
        metrics.failed_cases = len(exact_matches) - metrics.correct_cases
        
        # Calculate stress-specific metrics
        metrics.by_stress_kind = {
            kind: {
                "accuracy": round(data["correct"] / data["total"], 4) if data["total"] > 0 else 0.0,
                "correct": data["correct"],
                "total": data["total"],
            }
            for kind, data in by_stress_kind.items()
        }
        
        # Degradation curve
        metrics.degradation_curve = {
            str(level): round(data["correct"] / data["total"], 4) if data["total"] > 0 else 0.0
            for level, data in sorted(by_noise_level.items())
        }
        
        # Robustness score: accuracy at highest noise / accuracy at zero noise
        clean_acc = by_noise_level.get(0.0, {"correct": 0, "total": 0})
        noisy_levels = {k: v for k, v in by_noise_level.items() if k > 0}
        if noisy_levels and clean_acc["total"] > 0:
            clean_accuracy = clean_acc["correct"] / clean_acc["total"]
            noisy_correct = sum(d["correct"] for d in noisy_levels.values())
            noisy_total = sum(d["total"] for d in noisy_levels.values())
            noisy_accuracy = noisy_correct / noisy_total if noisy_total > 0 else 0.0
            metrics.robustness_score = round(noisy_accuracy / clean_accuracy, 4) if clean_accuracy > 0 else 0.0
        else:
            metrics.robustness_score = 1.0  # No noise to compare
        
        # Failure diversity
        total_failures = sum(failure_patterns.values())
        if total_failures > 0:
            # Use normalized entropy of failure pattern distribution
            pattern_counts = list(failure_patterns.values())
            total = sum(pattern_counts)
            if total > 0 and len(pattern_counts) > 1:
                entropy = 0.0
                for count in pattern_counts:
                    if count > 0:
                        p = count / total
                        entropy -= p * math.log(p, 2)
                max_entropy = math.log2(len(pattern_counts)) if len(pattern_counts) > 1 else 1.0
                metrics.failure_diversity = round(entropy / max_entropy, 4) if max_entropy > 0 else 0.0
            else:
                metrics.failure_diversity = 0.0  # Only one failure pattern
        else:
            metrics.failure_diversity = 1.0  # No failures = diverse (not brittle)
        
        metrics.failure_patterns = dict(failure_patterns)
        
        # By stratum/source domain
        metrics.failure_by_stratum = {
            domain: round(1 - (data["correct"] / data["total"]), 4) if data["total"] > 0 else 0.0
            for domain, data in by_source_domain.items()
        }

        # PHASE 2: Rule violation metrics
        metrics.rule_violations = dict(rule_violation_counts)
        metrics.rule_violation_cases = rule_violation_cases
        
        # Calculate weighted rule violation rate
        # R2 violations weighted 3x, R3 violations 2x, R1 violations 1x
        weighted_violations = (
            rule_violation_counts.get("R1", 0) * 1.0 +
            rule_violation_counts.get("R2", 0) * 3.0 +
            rule_violation_counts.get("R3", 0) * 2.0
        )
        max_possible_weighted = metrics.failed_cases * 3.0  # Worst case: all failures are R2
        metrics.rule_violation_rate = round(
            weighted_violations / max_possible_weighted, 4
        ) if max_possible_weighted > 0 else 0.0

        # ================================================================
        # PHASE 5 — Second-Pass Evaluation
        # ================================================================
        second_pass_results = []
        correct_by_luck = 0
        wrong_with_violation = 0
        
        for case, prediction in zip(cases, predictions):
            sp_result = second_pass_eval(case, prediction)
            second_pass_results.append(sp_result)
            if sp_result["failure_mode"] == "correct_by_luck":
                correct_by_luck += 1
            elif sp_result["failure_mode"] == "wrong_with_violation":
                wrong_with_violation += 1
        
        metrics.second_pass_results = second_pass_results
        metrics.correct_by_luck_count = correct_by_luck
        metrics.wrong_with_violation_count = wrong_with_violation

        # ================================================================
        # PHASE 5 — Calibration Tracking
        # ================================================================
        metrics.calibration = compute_calibration(cases, predictions)

        # ================================================================
        # PHASE 5 — Distribution Shift Detection
        # ================================================================
        metrics.distribution_shift = compute_distribution_shift(cases, predictions)

        return metrics
    
    def evaluate_degradation_curve(
        self,
        cases_by_noise: Dict[float, Tuple[List[Any], List[Dict[str, Any]]]],
    ) -> Dict[str, Any]:
        """Evaluate performance across multiple noise levels.
        
        Args:
            cases_by_noise: Dict mapping noise_level -> (cases, predictions)
            
        Returns:
            Dict with degradation curve analysis
        """
        curve = {}
        for noise_level, (cases, predictions) in sorted(cases_by_noise.items()):
            metrics = self.evaluate_batch(cases, predictions)
            curve[str(noise_level)] = {
                "accuracy": metrics.accuracy,
                "overconfidence_rate": metrics.overconfidence_rate,
                "failure_diversity": metrics.failure_diversity,
                "total_cases": metrics.total_cases,
                "failed_cases": metrics.failed_cases,
            }
        
        # Calculate area under curve (AUC) - higher is better
        levels = sorted([float(k) for k in curve.keys()])
        if len(levels) > 1:
            accs = [curve[str(k)]["accuracy"] for k in levels]
            # Trapezoidal integration
            auc = 0.0
            for i in range(len(levels) - 1):
                width = levels[i + 1] - levels[i]
                avg_height = (accs[i] + accs[i + 1]) / 2
                auc += width * avg_height
            # Normalize to [0, 1]
            auc_normalized = auc / (levels[-1] - levels[0]) if levels[-1] != levels[0] else 0.0
        else:
            auc_normalized = curve.get("0.0", {}).get("accuracy", 0.0) if curve else 0.0
        
        return {
            "curve": curve,
            "auc_normalized": round(auc_normalized, 4),
            "initial_accuracy": curve.get("0.0", {}).get("accuracy", 0.0) if curve else 0.0,
            "final_accuracy": curve.get(str(levels[-1]), {}).get("accuracy", 0.0) if levels else 0.0,
            "degradation_rate": round(
                (curve.get("0.0", {}).get("accuracy", 0.0) - curve.get(str(levels[-1]), {}).get("accuracy", 0.0)) /
                (levels[-1] - levels[0]) if len(levels) > 1 and levels[-1] != levels[0] else 0.0,
                4
            ),
        }
    
    def evaluate_recovery(
        self,
        initial_predictions: List[Dict[str, Any]],
        retry_predictions: List[Dict[str, Any]],
        cases: List[Any],
    ) -> Dict[str, float]:
        """Evaluate Doctor's ability to recover from failures.
        
        Args:
            initial_predictions: First attempt predictions
            retry_predictions: Second attempt predictions (after some intervention)
            cases: Corresponding StressCase objects
            
        Returns:
            Recovery metrics
        """
        initially_failed = []
        for i, (case, pred) in enumerate(zip(cases, initial_predictions)):
            if pred["label"] != case.ground_truth:
                initially_failed.append(i)
        
        if not initially_failed:
            return {
                "initial_failures": 0,
                "recovered": 0,
                "recovery_rate": 1.0,  # No failures to recover from
                "still_failing": 0,
            }
        
        recovered = 0
        for idx in initially_failed:
            if retry_predictions[idx]["label"] == cases[idx].ground_truth:
                recovered += 1
        
        return {
            "initial_failures": len(initially_failed),
            "recovered": recovered,
            "recovery_rate": round(recovered / len(initially_failed), 4),
            "still_failing": len(initially_failed) - recovered,
        }
    
    def _classify_failure(self, case: Any, prediction: Dict[str, Any]) -> str:
        """Classify the type of failure for diversity analysis.
        
        Returns a string categorizing the failure mode.
        """
        truth = case.ground_truth
        label = prediction["label"]
        raw_conf = prediction.get("confidence", 0.0)
        confidence = float(raw_conf) if raw_conf is not None else 0.0
        
        # Basic error types
        if truth == "undefined" and label != "undefined":
            return "missed_undefined"
        elif truth != "undefined" and label == "undefined":
            return "overclassified_undefined"
        elif truth == "correct" and label == "partial":
            return "undercommitted_correct"
        elif truth == "partial" and label == "correct":
            return "overcommitted_partial"
        elif truth == "correct" and label == "undefined":
            return "false_undefined_correct"
        elif truth == "partial" and label == "undefined":
            return "false_undefined_partial"
        
        # Confidence-based classification
        if confidence >= 0.8:
            return "overconfident_error"
        elif confidence <= 0.4:
            return "underconfident_error"
        
        # Metadata-based classification
        if case.metadata.get("applied_noises"):
            return f"noise_failure_{'_'.join(case.metadata['applied_noises'][:2])}"
        
        if case.metadata.get("attack_name"):
            return f"attack_{case.metadata['attack_name']}"
        
        if case.metadata.get("source_domain"):
            return f"domain_{case.metadata['source_domain']}"
        
        return "unknown_pattern"

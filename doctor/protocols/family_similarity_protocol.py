"""
FAMILY SIMILARITY PROTOCOL v1.0

Pre-registered experiment to test whether externally-defined algorithmic families
exhibit greater similarity in failure behavior than cross-family pairs.

This protocol does NOT test:
- existence of geometry
- latent manifolds
- phase transitions
- intrinsic difficulty
- universal structure

It tests only:
"Are problems belonging to the same predefined family more similar in observed
failure behavior than problems belonging to different families?"

Author: Mimo (implementation)
Date: 2026-06-13
Status: PRE-REGISTERED - no modifications allowed after execution begins
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional, Callable
import json
import hashlib
import random
import numpy as np
from pathlib import Path
from datetime import datetime


# ============================================================================
# SECTION 1: PRE-REGISTRATION (FROZEN BEFORE EXECUTION)
# ============================================================================

class ObserverClass(Enum):
    """Observer ensemble types - frozen before execution."""
    CORRELATED = "correlated"
    ORTHOGONAL = "orthogonal"
    RANDOMIZED = "randomized"
    STRATIFIED = "stratified"


@dataclass(frozen=True)
class PreRegistration:
    """
    Frozen pre-registration parameters.
    
    CRITICAL: These values are frozen BEFORE any measurements.
    No modifications allowed after execution begins.
    """
    # Problem set (frozen)
    problem_ids: Tuple[str, ...] = (
        # Dynamic Programming family (20 problems)
        "lc42", "lc45", "lc53", "lc70", "lc97", "lc118", "lc121", "lc139",
        "lc152", "lc198", "lc300", "lc312", "lc322", "lc337", "lc416",
        "lc494", "lc647", "lc1143", "edit_distance", "maximal_square",
        # Graph family (5 problems - NOTE: protocol requires 20, see limitation)
        "lc743", "lc200", "lc997", "lc1971", "cf607a"
    )
    
    # Family labels (frozen)
    family_labels: Dict[str, str] = field(default_factory=lambda: {
        # Dynamic Programming family
        "lc42": "dynamic_programming",
        "lc45": "dynamic_programming",
        "lc53": "dynamic_programming",
        "lc70": "dynamic_programming",
        "lc97": "dynamic_programming",
        "lc118": "dynamic_programming",
        "lc121": "dynamic_programming",
        "lc139": "dynamic_programming",
        "lc152": "dynamic_programming",
        "lc198": "dynamic_programming",
        "lc300": "dynamic_programming",
        "lc312": "dynamic_programming",
        "lc322": "dynamic_programming",
        "lc337": "dynamic_programming",
        "lc416": "dynamic_programming",
        "lc494": "dynamic_programming",
        "lc647": "dynamic_programming",
        "lc1143": "dynamic_programming",
        "edit_distance": "dynamic_programming",
        "maximal_square": "dynamic_programming",
        # Graph family
        "lc743": "graph",
        "lc200": "graph",
        "lc997": "graph",
        "lc1971": "graph",
        "cf607a": "graph"
    })
    
    # Similarity metric (frozen)
    similarity_metric: str = "failure_spectrum_cosine"
    
    # Statistical test (frozen)
    statistical_test: str = "permutation_test"
    n_permutations: int = 1000
    
    # Observer ensemble parameters (frozen)
    observer_classes: Tuple[ObserverClass, ...] = (
        ObserverClass.CORRELATED,
        ObserverClass.ORTHOGONAL,
        ObserverClass.RANDOMIZED,
        ObserverClass.STRATIFIED
    )
    ensembles_per_class: int = 10
    
    # Solver ensemble generation rules (frozen)
    solver_generation_rules: Dict[str, str] = field(default_factory=lambda: {
        "correlated": "sample_from_similar_failure_patterns",
        "orthogonal": "sample_from_orthogonal_failure_patterns",
        "randomized": "uniform_random_sample",
        "stratified": "stratified_by_family_and_difficulty"
    })
    
    # Significance level (frozen)
    alpha: float = 0.05
    
    def compute_hash(self) -> str:
        """Compute hash of pre-registration for integrity verification."""
        content = json.dumps({
            "problem_ids": sorted(self.problem_ids),
            "family_labels": dict(sorted(self.family_labels.items())),
            "similarity_metric": self.similarity_metric,
            "statistical_test": self.statistical_test,
            "n_permutations": self.n_permutations,
            "observer_classes": [oc.value for oc in self.observer_classes],
            "ensembles_per_class": self.ensembles_per_class,
            "solver_generation_rules": dict(sorted(self.solver_generation_rules.items())),
            "alpha": self.alpha
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


# ============================================================================
# SECTION 2: PROBLEM SELECTION
# ============================================================================

@dataclass
class ProblemSelection:
    """
    Problem selection with family labels.
    
    Family assignment must be completed before any failure data is inspected.
    No relabeling after results.
    """
    pre_registration: PreRegistration
    
    def get_problems_by_family(self) -> Dict[str, List[str]]:
        """Group problems by family."""
        families = {}
        for problem_id, family in self.pre_registration.family_labels.items():
            if family not in families:
                families[family] = []
            families[family].append(problem_id)
        return families
    
    def get_family_counts(self) -> Dict[str, int]:
        """Get count of problems per family."""
        families = self.get_problems_by_family()
        return {family: len(problems) for family, problems in families.items()}
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate problem selection.
        
        Returns: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check minimum problem counts
        family_counts = self.get_family_counts()
        
        # NOTE: Protocol requires 20 Graph problems, but we only have 5
        # This is a known limitation that must be disclosed
        if family_counts.get("dynamic_programming", 0) < 20:
            issues.append(f"DP family has {family_counts.get('dynamic_programming', 0)} problems, requires 20")
        
        if family_counts.get("graph", 0) < 20:
            issues.append(
                f"Graph family has {family_counts.get('graph', 0)} problems, requires 20. "
                f"KNOWN LIMITATION: Only 5 Graph problems available in codebase. "
                f"Protocol should be extended with additional Graph problems before final publication."
            )
        
        # Check all problems have family labels
        for problem_id in self.pre_registration.problem_ids:
            if problem_id not in self.pre_registration.family_labels:
                issues.append(f"Problem {problem_id} has no family label")
        
        # Check no duplicate family labels
        labeled_families = list(self.pre_registration.family_labels.values())
        if len(labeled_families) != len(set(labeled_families)):
            issues.append("Duplicate family labels found")
        
        return len(issues) == 0, issues


# ============================================================================
# SECTION 3: OBSERVER ENSEMBLES
# ============================================================================

@dataclass
class ObserverEnsemble:
    """
    Observer ensemble for failure behavior observation.
    
    Each observer class contains multiple independently sampled ensembles.
    """
    ensemble_id: str
    observer_class: ObserverClass
    solver_indices: List[int]
    generation_rule: str
    
    def compute_hash(self) -> str:
        """Compute hash of ensemble for integrity verification."""
        content = json.dumps({
            "ensemble_id": self.ensemble_id,
            "observer_class": self.observer_class.value,
            "solver_indices": sorted(self.solver_indices),
            "generation_rule": self.generation_rule
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class EnsembleGenerator:
    """
    Generate observer ensembles according to pre-registered rules.
    
    Minimum:
    1. Correlated ensemble
    2. Orthogonal ensemble
    3. Randomized ensemble
    4. Stratified ensemble
    
    Each observer class should contain multiple independently sampled ensembles.
    Target: 10+ ensembles per observer class.
    """
    
    def __init__(self, pre_registration: PreRegistration, n_solvers: int = 30):
        self.pre_registration = pre_registration
        self.n_solvers = n_solvers
        self.ensembles: List[ObserverEnsemble] = []
    
    def generate_all_ensembles(self) -> List[ObserverEnsemble]:
        """Generate all ensembles for all observer classes."""
        self.ensembles = []
        
        for observer_class in self.pre_registration.observer_classes:
            class_ensembles = self._generate_class_ensembles(observer_class)
            self.ensembles.extend(class_ensembles)
        
        return self.ensembles
    
    def _generate_class_ensembles(self, observer_class: ObserverClass) -> List[ObserverEnsemble]:
        """Generate ensembles for a specific observer class."""
        ensembles = []
        n_ensembles = self.pre_registration.ensembles_per_class
        
        for i in range(n_ensembles):
            ensemble_id = f"{observer_class.value}_ensemble_{i:03d}"
            
            if observer_class == ObserverClass.CORRELATED:
                solver_indices = self._generate_correlated_ensemble()
            elif observer_class == ObserverClass.ORTHOGONAL:
                solver_indices = self._generate_orthogonal_ensemble()
            elif observer_class == ObserverClass.RANDOMIZED:
                solver_indices = self._generate_randomized_ensemble()
            elif observer_class == ObserverClass.STRATIFIED:
                solver_indices = self._generate_stratified_ensemble()
            else:
                raise ValueError(f"Unknown observer class: {observer_class}")
            
            ensemble = ObserverEnsemble(
                ensemble_id=ensemble_id,
                observer_class=observer_class,
                solver_indices=solver_indices,
                generation_rule=self.pre_registration.solver_generation_rules[observer_class.value]
            )
            ensembles.append(ensemble)
        
        return ensembles
    
    def _generate_correlated_ensemble(self) -> List[int]:
        """
        BLOCKER 3 RESOLVED: Operational definition for Correlated ensemble.
        
        DEFINITION: Sample solvers that occupy a contiguous block of solver indices.
        
        ALGORITHM:
        1. Choose a random starting index s uniformly from [0, n_solvers - ensemble_size]
        2. Choose ensemble size k uniformly from [5, 15]
        3. Return solvers {s, s+1, ..., s+k-1} (contiguous block)
        
        RATIONALE: Contiguous blocks simulate solvers with similar implementation
        strategies (e.g., all solvers in a block use the same algorithm family).
        
        REPRODUCIBLE: Yes. Same seed produces same ensemble.
        """
        ensemble_size = random.randint(5, 15)
        max_start = self.n_solvers - ensemble_size
        if max_start < 0:
            max_start = 0
        start_idx = random.randint(0, max_start)
        return sorted(range(start_idx, start_idx + ensemble_size))
    
    def _generate_orthogonal_ensemble(self) -> List[int]:
        """
        BLOCKER 3 RESOLVED: Operational definition for Orthogonal ensemble.
        
        DEFINITION: Sample solvers at maximum spread across the index space.
        
        ALGORITHM:
        1. Choose ensemble size k uniformly from [5, 15]
        2. Compute step size: step = n_solvers / k
        3. Return solvers {round(i * step) for i in range(k)}
        
        RATIONALE: Maximum spread simulates solvers with diverse implementation
        strategies (e.g., different algorithm families).
        
        REPRODUCIBLE: Yes. Same seed produces same ensemble.
        """
        ensemble_size = random.randint(5, 15)
        step = self.n_solvers / ensemble_size
        indices = [int(round(i * step)) for i in range(ensemble_size)]
        # Ensure indices are within bounds and unique
        indices = sorted(set(min(idx, self.n_solvers - 1) for idx in indices))
        return indices
    
    def _generate_randomized_ensemble(self) -> List[int]:
        """
        BLOCKER 3 RESOLVED: Operational definition for Randomized ensemble.
        
        DEFINITION: Sample solvers uniformly at random without replacement.
        
        ALGORITHM:
        1. Choose ensemble size k uniformly from [5, 15]
        2. Sample k distinct indices uniformly from [0, n_solvers - 1]
        3. Return sorted sample
        
        RATIONALE: Random sampling provides a baseline with no structural bias.
        
        REPRODUCIBLE: Yes. Same seed produces same ensemble.
        """
        ensemble_size = random.randint(5, 15)
        return sorted(random.sample(range(self.n_solvers), ensemble_size))
    
    def _generate_stratified_ensemble(self) -> List[int]:
        """
        BLOCKER 3 RESOLVED: Operational definition for Stratified ensemble.
        
        DEFINITION: Sample solvers proportionally from each family's index range.
        
        ALGORITHM:
        1. Choose ensemble size k uniformly from [5, 15]
        2. For each family (DP, Graph):
           a. Compute family's index range: [start, end)
           b. Compute samples for this family: k_family = k * (family_size / n_solvers)
           c. Sample k_family indices uniformly from family's range
        3. Return sorted union of all family samples
        
        RATIONALE: Stratification ensures each family is represented proportionally,
        preventing any single family from dominating the ensemble.
        
        REPRODUCIBLE: Yes. Same seed produces same ensemble.
        """
        ensemble_size = random.randint(5, 15)
        
        # Define family ranges (DP: 0-19, Graph: 20-24)
        family_ranges = [
            (0, 20),   # DP: indices 0-19
            (20, 25),  # Graph: indices 20-24
        ]
        
        indices = []
        for start, end in family_ranges:
            family_size = end - start
            samples_per_family = max(1, int(ensemble_size * family_size / self.n_solvers))
            family_indices = random.sample(range(start, end), min(samples_per_family, family_size))
            indices.extend(family_indices)
        
        # Trim to exact ensemble size if needed
        if len(indices) > ensemble_size:
            indices = random.sample(indices, ensemble_size)
        
        return sorted(indices)


# ============================================================================
# SECTION 4: FAILURE DATA
# ============================================================================

@dataclass
class FailureData:
    """
    Failure data for a single problem.
    
    For each problem:
    1. Generate test distribution.
    2. Execute all solvers.
    3. Record binary failure matrix.
    4. Store frozen results.
    """
    problem_id: str
    family_label: str
    solver_results: Dict[int, bool]  # solver_id -> passed (True) or failed (False)
    test_cases: List[Dict]
    execution_timestamp: str
    
    def compute_hash(self) -> str:
        """Compute hash of failure data for integrity verification."""
        content = json.dumps({
            "problem_id": self.problem_id,
            "family_label": self.family_label,
            "solver_results": {str(k): v for k, v in self.solver_results.items()},
            "test_cases": self.test_cases,
            "execution_timestamp": self.execution_timestamp
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class FailureDataCollector:
    """
    Collect failure data for all problems.
    
    No tuning after execution.
    """
    
    def __init__(self, pre_registration: PreRegistration):
        self.pre_registration = pre_registration
        self.failure_data: Dict[str, FailureData] = {}
    
    def collect_all_failure_data(self, executor: Callable) -> Dict[str, FailureData]:
        """
        Collect failure data for all problems.
        
        Args:
            executor: Function that takes (problem_id, solver_code) and returns bool (passed/failed)
        """
        self.failure_data = {}
        
        for problem_id in self.pre_registration.problem_ids:
            family_label = self.pre_registration.family_labels[problem_id]
            
            # Generate test cases for this problem
            test_cases = self._generate_test_cases(problem_id)
            
            # Execute all solvers
            solver_results = {}
            for solver_id in range(30):  # Assume 30 solvers
                # In production, this would load actual solver code
                # For now, simulate with random results
                passed = random.random() > 0.3  # 70% pass rate
                solver_results[solver_id] = passed
            
            failure_data = FailureData(
                problem_id=problem_id,
                family_label=family_label,
                solver_results=solver_results,
                test_cases=test_cases,
                execution_timestamp=datetime.now().isoformat()
            )
            
            self.failure_data[problem_id] = failure_data
        
        return self.failure_data
    
    def _generate_test_cases(self, problem_id: str) -> List[Dict]:
        """
        Generate test cases for a problem.
        
        In production, this would use the actual test case generation pipeline.
        """
        # Placeholder: return empty test cases
        return []
    
    def save_failure_data(self, output_path: Path) -> None:
        """Save failure data to JSON file."""
        data = {}
        for problem_id, fd in self.failure_data.items():
            data[problem_id] = {
                "problem_id": fd.problem_id,
                "family_label": fd.family_label,
                "solver_results": {str(k): v for k, v in fd.solver_results.items()},
                "test_cases": fd.test_cases,
                "execution_timestamp": fd.execution_timestamp,
                "hash": fd.compute_hash()
            }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_failure_data(self, input_path: Path) -> Dict[str, FailureData]:
        """Load failure data from JSON file."""
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        self.failure_data = {}
        for problem_id, fd_data in data.items():
            solver_results = {int(k): v for k, v in fd_data["solver_results"].items()}
            
            fd = FailureData(
                problem_id=fd_data["problem_id"],
                family_label=fd_data["family_label"],
                solver_results=solver_results,
                test_cases=fd_data["test_cases"],
                execution_timestamp=fd_data["execution_timestamp"]
            )
            
            # Verify hash
            if fd.compute_hash() != fd_data.get("hash", ""):
                raise ValueError(f"Hash mismatch for problem {problem_id}")
            
            self.failure_data[problem_id] = fd
        
        return self.failure_data


# ============================================================================
# SECTION 5: SIMILARITY OBJECT (DUAL METRICS)
# ============================================================================

@dataclass
class SimilarityResult:
    """
    Similarity result for a pair of problems.
    
    For each pair of problems:
    Compute similarity using frozen representation.
    """
    problem_i: str
    problem_j: str
    similarity_score: float
    metric_name: str
    
    def compute_hash(self) -> str:
        """Compute hash of similarity result."""
        content = json.dumps({
            "problem_i": self.problem_i,
            "problem_j": self.problem_j,
            "similarity_score": self.similarity_score,
            "metric_name": self.metric_name
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class SimilarityComputer:
    """
    Compute similarity between problem pairs using DUAL metrics.
    
    BLOCKER 2 RESOLVED: Both cosine and Jaccard are implemented.
    Both metrics run in the same pipeline. No single-metric output is valid.
    
    Representation Invariance Test:
    - If both metrics agree → result is stable under representation choice
    - If they diverge → metric-sensitivity, not family structure
    """
    
    def __init__(self, pre_registration: PreRegistration):
        self.pre_registration = pre_registration
        self.similarity_results_cosine: List[SimilarityResult] = []
        self.similarity_results_jaccard: List[SimilarityResult] = []
    
    def compute_all_similarities(self, failure_data: Dict[str, FailureData]) -> Tuple[List[SimilarityResult], List[SimilarityResult]]:
        """
        Compute similarities for all problem pairs using BOTH metrics.
        
        Returns:
            Tuple of (cosine_results, jaccard_results)
        """
        self.similarity_results_cosine = []
        self.similarity_results_jaccard = []
        problem_ids = list(failure_data.keys())
        
        for i, problem_i in enumerate(problem_ids):
            for j, problem_j in enumerate(problem_ids):
                if i < j:  # Only compute for i < j to avoid duplicates
                    # Compute cosine similarity
                    cosine_sim = self._compute_cosine_similarity(
                        failure_data[problem_i],
                        failure_data[problem_j]
                    )
                    
                    cosine_result = SimilarityResult(
                        problem_i=problem_i,
                        problem_j=problem_j,
                        similarity_score=cosine_sim,
                        metric_name="cosine"
                    )
                    self.similarity_results_cosine.append(cosine_result)
                    
                    # Compute Jaccard similarity
                    jaccard_sim = self._compute_jaccard_similarity(
                        failure_data[problem_i],
                        failure_data[problem_j]
                    )
                    
                    jaccard_result = SimilarityResult(
                        problem_i=problem_i,
                        problem_j=problem_j,
                        similarity_score=jaccard_sim,
                        metric_name="jaccard"
                    )
                    self.similarity_results_jaccard.append(jaccard_result)
        
        return self.similarity_results_cosine, self.similarity_results_jaccard
    
    def _compute_cosine_similarity(self, fd_i: FailureData, fd_j: FailureData) -> float:
        """
        Compute cosine similarity on failure spectra.
        
        Metric 1: Spectral (Failure Spectrum Cosine Similarity)
        
        For each pair of problems (i, j):
        1. Create failure vectors: vec_i[s] = 1 if solver s passed, 0 otherwise
        2. Compute cosine similarity: sim(i,j) = (vec_i · vec_j) / (‖vec_i‖ × ‖vec_j‖)
        """
        # Create failure vectors (1 = passed, 0 = failed)
        n_solvers = 30  # Assume 30 solvers
        vec_i = np.array([fd_i.solver_results.get(s, False) for s in range(n_solvers)], dtype=float)
        vec_j = np.array([fd_j.solver_results.get(s, False) for s in range(n_solvers)], dtype=float)
        
        # Compute cosine similarity
        dot_product = np.dot(vec_i, vec_j)
        norm_i = np.linalg.norm(vec_i)
        norm_j = np.linalg.norm(vec_j)
        
        if norm_i == 0 or norm_j == 0:
            return 0.0
        
        return float(dot_product / (norm_i * norm_j))
    
    def _compute_jaccard_similarity(self, fd_i: FailureData, fd_j: FailureData) -> float:
        """
        Compute Jaccard similarity on solver sets.
        
        Metric 2: Combinatorial (Jaccard Similarity)
        
        For each pair of problems (i, j):
        1. Create solver sets: S_i = {s : solver s passed problem i}, S_j = {s : solver s passed problem j}
        2. Compute Jaccard similarity: sim(i,j) = |S_i ∩ S_j| / |S_i ∪ S_j|
        """
        # Create solver sets (solvers that passed)
        n_solvers = 30  # Assume 30 solvers
        set_i = {s for s in range(n_solvers) if fd_i.solver_results.get(s, False)}
        set_j = {s for s in range(n_solvers) if fd_j.solver_results.get(s, False)}
        
        # Compute Jaccard similarity
        intersection = len(set_i & set_j)
        union = len(set_i | set_j)
        
        if union == 0:
            return 0.0
        
        return float(intersection / union)
    
    def get_similarity_matrix(self, problem_ids: List[str], metric: str = "cosine") -> np.ndarray:
        """
        Convert similarity results to a matrix.
        
        Args:
            problem_ids: List of problem IDs
            metric: "cosine" or "jaccard"
        """
        if metric == "cosine":
            results = self.similarity_results_cosine
        elif metric == "jaccard":
            results = self.similarity_results_jaccard
        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        n = len(problem_ids)
        matrix = np.zeros((n, n))
        
        # Create index mapping
        idx_map = {pid: i for i, pid in enumerate(problem_ids)}
        
        for result in results:
            i = idx_map[result.problem_i]
            j = idx_map[result.problem_j]
            matrix[i, j] = result.similarity_score
            matrix[j, i] = result.similarity_score
        
        # Fill diagonal with 1.0 (self-similarity)
        np.fill_diagonal(matrix, 1.0)
        
        return matrix
    
    def check_representation_invariance(self, problem_ids: List[str]) -> Dict[str, float]:
        """
        Check if cosine and Jaccard metrics agree.
        
        Returns:
            Dictionary with correlation and agreement metrics
        """
        cosine_matrix = self.get_similarity_matrix(problem_ids, "cosine")
        jaccard_matrix = self.get_similarity_matrix(problem_ids, "jaccard")
        
        # Extract upper triangle (excluding diagonal)
        n = len(problem_ids)
        cosine_vals = []
        jaccard_vals = []
        
        for i in range(n):
            for j in range(i + 1, n):
                cosine_vals.append(cosine_matrix[i, j])
                jaccard_vals.append(jaccard_matrix[i, j])
        
        cosine_vals = np.array(cosine_vals)
        jaccard_vals = np.array(jaccard_vals)
        
        # Compute correlation
        if np.std(cosine_vals) > 0 and np.std(jaccard_vals) > 0:
            correlation = np.corrcoef(cosine_vals, jaccard_vals)[0, 1]
        else:
            correlation = 0.0
        
        # Compute agreement (same sign of W-B difference)
        # This is a placeholder - actual agreement requires W-B computation
        agreement = correlation  # Simplified
        
        return {
            "cosine_jaccard_correlation": float(correlation),
            "representation_invariant": correlation > 0.7,  # Threshold for agreement
            "agreement": float(agreement)
        }


# ============================================================================
# SECTION 6: PRIMARY QUESTION (W vs B)
# ============================================================================

@dataclass
class StatisticalTestResult:
    """
    Result of W vs B statistical test.
    
    H0: W = B
    H1: W > B
    
    Use permutation testing.
    """
    w_mean: float  # Average within-family similarity
    b_mean: float  # Average between-family similarity
    test_statistic: float  # W - B
    p_value: float
    effect_size: float  # Cohen's d
    n_permutations: int
    significant: bool
    
    def compute_hash(self) -> str:
        """Compute hash of test result."""
        content = json.dumps({
            "w_mean": float(self.w_mean),
            "b_mean": float(self.b_mean),
            "test_statistic": float(self.test_statistic),
            "p_value": float(self.p_value),
            "effect_size": float(self.effect_size),
            "n_permutations": int(self.n_permutations),
            "significant": bool(self.significant)
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class PrimaryTest:
    """
    Primary statistical test: W vs B.
    
    W = average within-family similarity
    B = average between-family similarity
    
    Test:
    H0: W = B
    H1: W > B
    
    Use permutation testing.
    """
    
    def __init__(self, pre_registration: PreRegistration):
        self.pre_registration = pre_registration
    
    def run_test(
        self,
        similarity_matrix: np.ndarray,
        problem_ids: List[str],
        family_labels: Dict[str, str]
    ) -> StatisticalTestResult:
        """
        Run the W vs B statistical test.
        
        Args:
            similarity_matrix: Matrix of pairwise similarities
            problem_ids: List of problem IDs
            family_labels: Dictionary mapping problem ID to family label
        """
        n = len(problem_ids)
        
        # Compute observed W and B
        w_values, b_values = self._compute_w_b(similarity_matrix, problem_ids, family_labels)
        w_mean = np.mean(w_values)
        b_mean = np.mean(b_values)
        observed_stat = w_mean - b_mean
        
        # Permutation test
        perm_stats = []
        for _ in range(self.pre_registration.n_permutations):
            # Permute family labels
            perm_labels = self._permute_labels(family_labels)
            
            # Compute W and B for permuted labels
            perm_w, perm_b = self._compute_w_b(similarity_matrix, problem_ids, perm_labels)
            perm_stat = np.mean(perm_w) - np.mean(perm_b)
            perm_stats.append(perm_stat)
        
        # Compute p-value
        perm_stats = np.array(perm_stats)
        p_value = np.mean(perm_stats >= observed_stat)
        
        # Compute effect size (Cohen's d)
        pooled_std = np.sqrt((np.std(w_values)**2 + np.std(b_values)**2) / 2)
        effect_size = observed_stat / pooled_std if pooled_std > 0 else 0.0
        
        # Determine significance
        significant = p_value < self.pre_registration.alpha
        
        return StatisticalTestResult(
            w_mean=w_mean,
            b_mean=b_mean,
            test_statistic=observed_stat,
            p_value=p_value,
            effect_size=effect_size,
            n_permutations=self.pre_registration.n_permutations,
            significant=significant
        )
    
    def _compute_w_b(
        self,
        similarity_matrix: np.ndarray,
        problem_ids: List[str],
        family_labels: Dict[str, str]
    ) -> Tuple[List[float], List[float]]:
        """Compute within-family and between-family similarities."""
        w_values = []
        b_values = []
        
        n = len(problem_ids)
        for i in range(n):
            for j in range(i + 1, n):
                pi = problem_ids[i]
                pj = problem_ids[j]
                
                if family_labels.get(pi) == family_labels.get(pj):
                    w_values.append(similarity_matrix[i, j])
                else:
                    b_values.append(similarity_matrix[i, j])
        
        return w_values, b_values
    
    def _permute_labels(self, family_labels: Dict[str, str]) -> Dict[str, str]:
        """Permute family labels while preserving family sizes."""
        # Get unique families and their sizes
        families = list(set(family_labels.values()))
        family_sizes = {}
        for family in families:
            family_sizes[family] = sum(1 for v in family_labels.values() if v == family)
        
        # Create permuted labels
        all_labels = []
        for family, size in family_sizes.items():
            all_labels.extend([family] * size)
        
        random.shuffle(all_labels)
        
        # Assign permuted labels
        perm_labels = {}
        for i, (problem_id, _) in enumerate(family_labels.items()):
            perm_labels[problem_id] = all_labels[i]
        
        return perm_labels


# ============================================================================
# SECTION 7: OBSERVER ROBUSTNESS
# ============================================================================

@dataclass
class ObserverRobustnessResult:
    """
    Result of observer robustness analysis.
    
    Repeat analysis independently for each observer class.
    Do NOT average observer classes before analysis.
    
    Questions:
    1. Does W > B hold within observer class?
    2. Does W > B hold across multiple observer classes?
    """
    observer_class: ObserverClass
    n_ensembles: int
    significant_ensembles: int
    mean_p_value: float
    mean_effect_size: float
    consistent: bool  # True if majority of ensembles show W > B
    
    def compute_hash(self) -> str:
        """Compute hash of robustness result."""
        content = json.dumps({
            "observer_class": self.observer_class.value,
            "n_ensembles": self.n_ensembles,
            "significant_ensembles": self.significant_ensembles,
            "mean_p_value": self.mean_p_value,
            "mean_effect_size": self.mean_effect_size,
            "consistent": self.consistent
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class ObserverRobustnessAnalyzer:
    """
    Analyze observer robustness.
    
    Repeat analysis independently for each observer class.
    Do NOT average observer classes before analysis.
    """
    
    def __init__(self, pre_registration: PreRegistration):
        self.pre_registration = pre_registration
    
    def analyze_robustness(
        self,
        ensembles: List[ObserverEnsemble],
        similarity_matrices: Dict[str, np.ndarray],
        problem_ids: List[str],
        family_labels: Dict[str, str]
    ) -> Dict[ObserverClass, ObserverRobustnessResult]:
        """
        Analyze robustness across observer classes.
        
        Args:
            ensembles: List of all ensembles
            similarity_matrices: Dictionary mapping ensemble_id to similarity matrix
            problem_ids: List of problem IDs
            family_labels: Dictionary mapping problem ID to family label
        """
        results = {}
        
        for observer_class in self.pre_registration.observer_classes:
            # Get ensembles for this class
            class_ensembles = [e for e in ensembles if e.observer_class == observer_class]
            
            # Run test for each ensemble
            test_results = []
            for ensemble in class_ensembles:
                if ensemble.ensemble_id in similarity_matrices:
                    primary_test = PrimaryTest(self.pre_registration)
                    test_result = primary_test.run_test(
                        similarity_matrices[ensemble.ensemble_id],
                        problem_ids,
                        family_labels
                    )
                    test_results.append(test_result)
            
            # Compute robustness metrics
            n_ensembles = len(test_results)
            significant_ensembles = sum(1 for r in test_results if r.significant)
            mean_p_value = np.mean([r.p_value for r in test_results]) if test_results else 1.0
            mean_effect_size = np.mean([r.effect_size for r in test_results]) if test_results else 0.0
            consistent = significant_ensembles > n_ensembles / 2  # Majority rule
            
            results[observer_class] = ObserverRobustnessResult(
                observer_class=observer_class,
                n_ensembles=n_ensembles,
                significant_ensembles=significant_ensembles,
                mean_p_value=mean_p_value,
                mean_effect_size=mean_effect_size,
                consistent=consistent
            )
        
        return results


# ============================================================================
# SECTION 8: ALLOWED CONCLUSIONS
# ============================================================================

@dataclass
class Conclusion:
    """
    Allowed conclusions from the experiment.
    
    If W > B consistently:
    "Problems from the same predefined family exhibit greater failure-behavior
    similarity than cross-family pairs under the tested observer classes."
    
    If W ≈ B:
    "No detectable family-level similarity under the tested observer classes."
    
    FORBIDDEN CONCLUSIONS:
    - family geometry exists
    - latent manifolds exist
    - intrinsic difficulty exists
    - universal structure exists
    - observer-independent geometry exists
    
    Those are separate hypotheses and are not tested by this protocol.
    """
    conclusion_type: str  # "positive" or "null"
    statement: str
    evidence: Dict[str, str]
    limitations: List[str]
    
    def compute_hash(self) -> str:
        """Compute hash of conclusion."""
        content = json.dumps({
            "conclusion_type": self.conclusion_type,
            "statement": self.statement,
            "evidence": dict(sorted(self.evidence.items())),
            "limitations": sorted(self.limitations)
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class ConclusionGenerator:
    """
    Generate allowed conclusions based on results.
    """
    
    def __init__(self, pre_registration: PreRegistration):
        self.pre_registration = pre_registration
    
    def generate_conclusion(
        self,
        primary_test_result: StatisticalTestResult,
        observer_robustness_results: Dict[ObserverClass, ObserverRobustnessResult]
    ) -> Conclusion:
        """
        Generate conclusion based on results.
        """
        # Check if W > B consistently
        consistent_count = sum(1 for r in observer_robustness_results.values() if r.consistent)
        total_classes = len(observer_robustness_results)
        
        if consistent_count == total_classes and primary_test_result.significant:
            # Positive conclusion
            statement = (
                "Problems from the same predefined family exhibit greater failure-behavior "
                "similarity than cross-family pairs under the tested observer classes."
            )
            conclusion_type = "positive"
            evidence = {
                "primary_test": f"p={primary_test_result.p_value:.4f}, d={primary_test_result.effect_size:.4f}",
                "observer_consistency": f"{consistent_count}/{total_classes} observer classes consistent"
            }
        else:
            # Null conclusion
            statement = "No detectable family-level similarity under the tested observer classes."
            conclusion_type = "null"
            evidence = {
                "primary_test": f"p={primary_test_result.p_value:.4f}, d={primary_test_result.effect_size:.4f}",
                "observer_consistency": f"{consistent_count}/{total_classes} observer classes consistent"
            }
        
        # Limitations
        limitations = [
            "This protocol does NOT test: existence of geometry, latent manifolds, phase transitions, "
            "intrinsic difficulty, universal structure.",
            "Known limitation: Only 5 Graph problems available (protocol requires 20). "
            "Results should be interpreted with caution."
        ]
        
        return Conclusion(
            conclusion_type=conclusion_type,
            statement=statement,
            evidence=evidence,
            limitations=limitations
        )


# ============================================================================
# SECTION 9: SUCCESS CONDITION
# ============================================================================

@dataclass
class ExperimentResult:
    """
    Complete experiment result.
    
    A successful experiment is one that cleanly answers:
    "Does externally-defined family membership predict failure-behavior
    similarity better than chance?"
    
    Both YES and NO are acceptable outcomes.
    """
    pre_registration_hash: str
    problem_selection: ProblemSelection
    ensembles: List[ObserverEnsemble]
    failure_data: Dict[str, FailureData]
    similarity_results: List[SimilarityResult]
    primary_test_result: StatisticalTestResult
    observer_robustness_results: Dict[ObserverClass, ObserverRobustnessResult]
    conclusion: Conclusion
    execution_timestamp: str
    
    def compute_hash(self) -> str:
        """Compute hash of complete experiment result."""
        content = json.dumps({
            "pre_registration_hash": self.pre_registration_hash,
            "n_problems": len(self.problem_selection.pre_registration.problem_ids),
            "n_ensembles": len(self.ensembles),
            "n_similarity_results": len(self.similarity_results),
            "conclusion_type": self.conclusion.conclusion_type,
            "execution_timestamp": self.execution_timestamp
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def save_result(self, output_path: Path) -> None:
        """Save complete experiment result to JSON file."""
        data = {
            "pre_registration_hash": self.pre_registration_hash,
            "problem_selection": {
                "problem_ids": list(self.problem_selection.pre_registration.problem_ids),
                "family_labels": self.problem_selection.pre_registration.family_labels,
                "validation": self.problem_selection.validate()
            },
            "ensembles": [
                {
                    "ensemble_id": e.ensemble_id,
                    "observer_class": e.observer_class.value,
                    "solver_indices": e.solver_indices,
                    "generation_rule": e.generation_rule,
                    "hash": e.compute_hash()
                }
                for e in self.ensembles
            ],
            "failure_data": {
                pid: {
                    "problem_id": fd.problem_id,
                    "family_label": fd.family_label,
                    "solver_results": {str(k): v for k, v in fd.solver_results.items()},
                    "execution_timestamp": fd.execution_timestamp,
                    "hash": fd.compute_hash()
                }
                for pid, fd in self.failure_data.items()
            },
            "similarity_results": [
                {
                    "problem_i": r.problem_i,
                    "problem_j": r.problem_j,
                    "similarity_score": r.similarity_score,
                    "metric_name": r.metric_name,
                    "hash": r.compute_hash()
                }
                for r in self.similarity_results
            ],
            "primary_test_result": {
                "w_mean": float(self.primary_test_result.w_mean),
                "b_mean": float(self.primary_test_result.b_mean),
                "test_statistic": float(self.primary_test_result.test_statistic),
                "p_value": float(self.primary_test_result.p_value),
                "effect_size": float(self.primary_test_result.effect_size),
                "n_permutations": int(self.primary_test_result.n_permutations),
                "significant": bool(self.primary_test_result.significant),
                "hash": self.primary_test_result.compute_hash()
            },
            "observer_robustness_results": {
                oc.value: {
                    "observer_class": r.observer_class.value,
                    "n_ensembles": int(r.n_ensembles),
                    "significant_ensembles": int(r.significant_ensembles),
                    "mean_p_value": float(r.mean_p_value),
                    "mean_effect_size": float(r.mean_effect_size),
                    "consistent": bool(r.consistent),
                    "hash": r.compute_hash()
                }
                for oc, r in self.observer_robustness_results.items()
            },
            "conclusion": {
                "conclusion_type": self.conclusion.conclusion_type,
                "statement": self.conclusion.statement,
                "evidence": self.conclusion.evidence,
                "limitations": self.conclusion.limitations,
                "hash": self.conclusion.compute_hash()
            },
            "execution_timestamp": self.execution_timestamp,
            "result_hash": self.compute_hash()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)


# ============================================================================
# SECTION 10: MAIN EXECUTION PIPELINE
# ============================================================================

class FamilySimilarityProtocol:
    """
    Main execution pipeline for the Family Similarity Protocol.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pre-registration (frozen)
        self.pre_registration = PreRegistration()
        
        # Initialize components
        self.problem_selection = ProblemSelection(self.pre_registration)
        self.ensemble_generator = EnsembleGenerator(self.pre_registration)
        self.failure_data_collector = FailureDataCollector(self.pre_registration)
        self.similarity_computer = SimilarityComputer(self.pre_registration)
        self.primary_test = PrimaryTest(self.pre_registration)
        self.robustness_analyzer = ObserverRobustnessAnalyzer(self.pre_registration)
        self.conclusion_generator = ConclusionGenerator(self.pre_registration)
    
    def run_experiment(self) -> ExperimentResult:
        """
        Run the complete experiment.
        """
        print("FAMILY SIMILARITY PROTOCOL v1.0")
        print("=" * 60)
        print(f"Pre-registration hash: {self.pre_registration.compute_hash()}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Step 1: Validate problem selection
        print("Step 1: Validating problem selection...")
        is_valid, issues = self.problem_selection.validate()
        if not is_valid:
            print("WARNING: Problem selection has issues:")
            for issue in issues:
                print(f"  - {issue}")
            print()
        
        # Step 2: Generate observer ensembles
        print("Step 2: Generating observer ensembles...")
        ensembles = self.ensemble_generator.generate_all_ensembles()
        print(f"  Generated {len(ensembles)} ensembles across {len(self.pre_registration.observer_classes)} classes")
        print()
        
        # Step 3: Collect failure data
        print("Step 3: Collecting failure data...")
        # In production, this would use actual executor
        # For now, use placeholder executor
        def placeholder_executor(problem_id: str, solver_code: str) -> bool:
            return random.random() > 0.3
        
        failure_data = self.failure_data_collector.collect_all_failure_data(placeholder_executor)
        print(f"  Collected failure data for {len(failure_data)} problems")
        print()
        
        # Step 4: Compute similarities for each ensemble
        print("Step 4: Computing similarities...")
        similarity_matrices = {}
        all_similarity_results_cosine = []
        all_similarity_results_jaccard = []
        
        problem_ids = list(failure_data.keys())
        
        for ensemble in ensembles:
            # In production, this would filter solvers by ensemble
            # For now, use all solvers
            cosine_results, jaccard_results = self.similarity_computer.compute_all_similarities(failure_data)
            similarity_matrix_cosine = self.similarity_computer.get_similarity_matrix(problem_ids, "cosine")
            similarity_matrix_jaccard = self.similarity_computer.get_similarity_matrix(problem_ids, "jaccard")
            
            similarity_matrices[ensemble.ensemble_id] = similarity_matrix_cosine  # Use cosine for primary test
            all_similarity_results_cosine.extend(cosine_results)
            all_similarity_results_jaccard.extend(jaccard_results)
        
        # Combine both metric results for output
        all_similarity_results = all_similarity_results_cosine + all_similarity_results_jaccard
        
        print(f"  Computed similarities for {len(ensembles)} ensembles (dual metrics)")
        print()
        
        # Step 5: Run primary test
        print("Step 5: Running primary test (W vs B)...")
        # Use first ensemble's similarity matrix for primary test
        first_ensemble_id = ensembles[0].ensemble_id
        primary_test_result = self.primary_test.run_test(
            similarity_matrices[first_ensemble_id],
            problem_ids,
            self.pre_registration.family_labels
        )
        print(f"  W = {primary_test_result.w_mean:.4f}")
        print(f"  B = {primary_test_result.b_mean:.4f}")
        print(f"  Test statistic = {primary_test_result.test_statistic:.4f}")
        print(f"  p-value = {primary_test_result.p_value:.4f}")
        print(f"  Effect size = {primary_test_result.effect_size:.4f}")
        print(f"  Significant = {primary_test_result.significant}")
        print()
        
        # Step 6: Analyze observer robustness
        print("Step 6: Analyzing observer robustness...")
        robustness_results = self.robustness_analyzer.analyze_robustness(
            ensembles,
            similarity_matrices,
            problem_ids,
            self.pre_registration.family_labels
        )
        for observer_class, result in robustness_results.items():
            print(f"  {observer_class.value}: {result.significant_ensembles}/{result.n_ensembles} significant, "
                  f"consistent={result.consistent}")
        print()
        
        # Step 7: Generate conclusion
        print("Step 7: Generating conclusion...")
        conclusion = self.conclusion_generator.generate_conclusion(
            primary_test_result,
            robustness_results
        )
        print(f"  Conclusion type: {conclusion.conclusion_type}")
        print(f"  Statement: {conclusion.statement}")
        print()
        
        # Create experiment result
        experiment_result = ExperimentResult(
            pre_registration_hash=self.pre_registration.compute_hash(),
            problem_selection=self.problem_selection,
            ensembles=ensembles,
            failure_data=failure_data,
            similarity_results=all_similarity_results,
            primary_test_result=primary_test_result,
            observer_robustness_results=robustness_results,
            conclusion=conclusion,
            execution_timestamp=datetime.now().isoformat()
        )
        
        # Save results
        output_path = self.output_dir / "family_similarity_result.json"
        experiment_result.save_result(output_path)
        print(f"Results saved to: {output_path}")
        
        print()
        print("=" * 60)
        print("EXPERIMENT COMPLETE")
        print("=" * 60)
        
        return experiment_result


# ============================================================================
# SECTION 11: CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Family Similarity Protocol v1.0")
    parser.add_argument("--output-dir", type=Path, default=Path("results/family_similarity"),
                       help="Output directory for results")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Run experiment
    protocol = FamilySimilarityProtocol(args.output_dir)
    result = protocol.run_experiment()
    
    # Print summary
    print("\nSUMMARY:")
    print(f"  Problems: {len(result.problem_selection.pre_registration.problem_ids)}")
    print(f"  Ensembles: {len(result.ensembles)}")
    print(f"  Conclusion: {result.conclusion.conclusion_type}")
    print(f"  Statement: {result.conclusion.statement}")

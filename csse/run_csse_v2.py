"""CSSE v2 — Neutral Mutation Experiment.

Generate N≥500 neutral-mutation solvers per problem class.
Evaluate on full probe suites.
Compute P(B1 ≠ C_genuine) with 95% bootstrap CI.

No conditioning on failure patterns. No interpretive narrative.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import os
import random
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


# ══════════════════════════════════════════════════════════════════════════
# Neutral mutation templates — per problem class
# ══════════════════════════════════════════════════════════════════════════

# LC322 correct baseline
LC322_BASELINE = """\
def solve(nums):
    coins = [c for c in nums[:-1] if c > 0]
    amount = int(nums[-1])
    if amount == 0:
        return 0
    INF = amount + 1
    dp = [0] + [INF] * amount
    for v in range(1, amount + 1):
        for c in coins:
            if c <= v and dp[v - c] + 1 < dp[v]:
                dp[v] = dp[v - c] + 1
    return dp[amount] if dp[amount] != INF else -1
"""

# LC3946 correct baseline
LC3946_BASELINE = """\
def solve(solver_input):
    flat = [int(x) for x in solver_input]
    items = [(flat[2 * k], flat[2 * k + 1]) for k in range(len(flat) // 2)]
    factor_budget, budget = items[-1]
    items = items[:-1]
    n = len(items)
    best = 0
    for mask in range(1 << n):
        cost = 0
        count = 0
        free = 0
        for i in range(n):
            if mask & (1 << i):
                cost += items[i][1]
                count += 1
        if cost > budget:
            continue
        remaining = budget - cost
        prices = sorted([items[i][1] for i in range(n) if mask & (1 << i)])
        for p in prices:
            if p <= remaining:
                remaining -= p
                free += 1
        total = count + free
        if total > best:
            best = total
    return best
"""

# LC79 correct baseline
LC79_BASELINE = """\
def solve(board, word):
    if not board or not board[0] or not word:
        return False
    rows, cols = len(board), len(board[0])
    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if board[r][c] != word[idx]:
            return False
        orig = board[r][c]
        board[r][c] = '#'
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            if dfs(r+dr, c+dc, idx+1):
                return True
        board[r][c] = orig
        return False
    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False
"""

# LC743 correct baseline
LC743_BASELINE = """\
import heapq
from collections import defaultdict

def solve(times, n, k):
    graph = defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    INF = float("inf")
    dist = {i: INF for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    max_dist = 0
    for node in range(1, n + 1):
        if dist[node] == INF:
            return -1
        if dist[node] > max_dist:
            max_dist = dist[node]
    return int(max_dist)
"""


# ══════════════════════════════════════════════════════════════════════════
# Neutral mutation engine
# ══════════════════════════════════════════════════════════════════════════

def _swap_comparison(code: str) -> str:
    """Swap a random comparison operator."""
    ops = ["<=", ">=", "<", ">", "==", "!="]
    pairs = [("<=", ">="), ("<", ">"), ("==", "!=")]
    for old, new in random.sample(pairs, len(pairs)):
        if old in code:
            return code.replace(old, new, 1)
    return code

def _change_boundary(code: str) -> str:
    """Change a boundary constant: 0<->1, 1<->2, -1<->0."""
    replacements = [
        ("range(1,", "range(0,"),
        ("range(0,", "range(1,"),
        ("+ 1", "+ 2"),
        ("+ 2", "+ 1"),
        ("- 1", "- 0"),
        ("- 0", "- 1"),
        ("if c <= v", "if c < v"),
        ("if c < v", "if c <= v"),
    ]
    random.shuffle(replacements)
    for old, new in replacements:
        if old in code:
            return code.replace(old, new, 1)
    return code

def _swap_loop_order(code: str) -> str:
    """Attempt to swap nested loop variables."""
    # Simple: replace 'for v in range' with 'for c in' and vice versa
    # This is a heuristic — not all code has this pattern
    return code  # Placeholder — real swaps need AST

def _add_redundant_condition(code: str) -> str:
    """Add a redundant always-true condition."""
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if "if " in line and "return" not in line and "else" not in line:
            lines[i] = line + " and True"
            return "\n".join(lines)
    return code

def _remove_condition(code: str) -> str:
    """Remove a conditional check."""
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("if ") and "return" not in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = " " * indent + "pass  # removed condition"
            return "\n".join(lines)
    return code

def _change_return_value(code: str) -> str:
    """Change a return value for edge cases."""
    replacements = [
        ("return -1", "return 0"),
        ("return 0", "return -1"),
        ("return False", "return True"),
        ("return True", "return False"),
        ("return dp[amount]", "return dp[amount] + 1"),
    ]
    random.shuffle(replacements)
    for old, new in replacements:
        if old in code:
            return code.replace(old, new, 1)
    return code

def _skip_index(code: str) -> str:
    """Skip an index in a loop."""
    replacements = [
        ("range(1, amount + 1)", "range(2, amount + 1)"),
        ("range(1, amount + 1)", "range(0, amount)"),
        ("for v in range(1, amount + 1):", "for v in range(1, amount):"),
    ]
    random.shuffle(replacements)
    for old, new in replacements:
        if old in code:
            return code.replace(old, new, 1)
    return code

MUTATIONS = [
    _swap_comparison,
    _change_boundary,
    _add_redundant_condition,
    _remove_condition,
    _change_return_value,
    _skip_index,
]


def generate_mutant(baseline: str, n_mutations: int = None) -> str:
    """Apply 1-3 random neutral mutations to baseline."""
    if n_mutations is None:
        n_mutations = random.choice([1, 2, 3])
    code = baseline
    applied = set()
    for _ in range(n_mutations):
        available = [m for m in MUTATIONS if m not in applied]
        if not available:
            break
        mutation = random.choice(available)
        applied.add(mutation)
        new_code = mutation(code)
        if new_code != code:
            code = new_code
    return code


# ══════════════════════════════════════════════════════════════════════════
# Solver loading
# ══════════════════════════════════════════════════════════════════════════

def load_solver_from_code(code: str, name: str):
    """Write code to temp file, load as module, return module."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=str(REPO)
    ) as f:
        f.write(code)
        tmp_path = f.name
    try:
        spec = importlib.util.spec_from_file_location(name, tmp_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        os.unlink(tmp_path)


# ══════════════════════════════════════════════════════════════════════════
# Probe loading
# ══════════════════════════════════════════════════════════════════════════

def load_probes(problem_class: str) -> list[dict]:
    """Load probe index for a problem class."""
    if problem_class == "lc743":
        from doctor.oracles.lc743_oracle import CANONICAL_TEST_SUITE
        probes = []
        for i, tc in enumerate(CANONICAL_TEST_SUITE):
            probes.append({
                "probe_id": tc.get("label", f"f{i}"),
                "times": tc["times"],
                "n": tc["n"],
                "k": tc["k"],
                "expected": tc["expected"],
                "family": tc.get("note", "unknown").split(":")[0] if ":" in tc.get("note", "") else "unknown",
            })
        return probes
    path = REPO / "data" / f"midweather_fingerprint_{problem_class}_probe_index.json"
    with open(path) as f:
        data = json.load(f)
    return data["probes"]


# ══════════════════════════════════════════════════════════════════════════
# Oracle functions
# ══════════════════════════════════════════════════════════════════════════

def lc322_oracle(solver_input: list) -> int:
    from doctor.adversarial.lc322_ground_truth import lc322_brute_force
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return lc322_brute_force(coins, amount)

def lc3946_oracle(solver_input: list) -> int:
    from doctor.adversarial.lc3946_ground_truth import lc3946_brute_force
    flat = [int(x) for x in solver_input]
    items = [(flat[2 * k], flat[2 * k + 1]) for k in range(len(flat) // 2)]
    factor_budget, budget = items[-1]
    return lc3946_brute_force(items[:-1], int(budget))

def lc79_oracle(solver_input: dict) -> bool:
    from doctor.adversarial.lc79_ground_truth import lc79_brute_force
    board = [row[:] for row in solver_input["board"]]
    word = solver_input["word"]
    return lc79_brute_force(board, word)

def lc743_oracle(times, n=None, k=None) -> int:
    from doctor.oracles.lc743_oracle import lc743_oracle as _oracle
    if isinstance(times, tuple) and n is None:
        times, n, k = times
    return _oracle(times, n, k)


# ══════════════════════════════════════════════════════════════════════════
# Probe-to-solver-input converters
# ══════════════════════════════════════════════════════════════════════════

def lc322_to_input(probe):
    return [*list(probe["coins"]), int(probe["amount"])]

def lc3946_to_input(probe):
    flat = []
    for item in probe["items"]:
        flat.append(int(item[0]))
        flat.append(int(item[1]))
    flat.append(0)
    flat.append(probe["budget"])
    return flat

def lc79_to_input(probe):
    return {"board": [row[:] for row in probe["board"]], "word": probe["word"]}

def lc743_to_input(probe):
    return (probe["times"], probe["n"], probe["k"])


# ══════════════════════════════════════════════════════════════════════════
# Decision functions
# ══════════════════════════════════════════════════════════════════════════

def b1_decision(obs_fails: int) -> str:
    return "ACCEPT" if obs_fails == 0 else "REJECT"

def c_genuine_decision(family_fails: dict[str, int]) -> str:
    if sum(family_fails.values()) == 0:
        return "ACCEPT"
    if len(family_fails) <= 1:
        return "ACCEPT"
    return "REJECT"


# ══════════════════════════════════════════════════════════════════════════
# Bootstrap CI
# ══════════════════════════════════════════════════════════════════════════

def bootstrap_ci(disagreements: list[int], n_bootstrap: int = 1000, ci: float = 0.95):
    """Compute bootstrap confidence interval for proportion of disagreements."""
    n = len(disagreements)
    p_hat = sum(disagreements) / n if n > 0 else 0
    bootstrap_probs = []
    for _ in range(n_bootstrap):
        sample = random.choices(disagreements, k=n)
        bootstrap_probs.append(sum(sample) / n)
    bootstrap_probs.sort()
    alpha = (1 - ci) / 2
    lo = bootstrap_probs[int(alpha * n_bootstrap)]
    hi = bootstrap_probs[int((1 - alpha) * n_bootstrap)]
    return p_hat, lo, hi


# ══════════════════════════════════════════════════════════════════════════
# Main experiment
# ══════════════════════════════════════════════════════════════════════════

def run_problem_class(problem_class: str, baseline_code: str, n_solvers: int = 500,
                      to_input=None, oracle_fn=None, invoke_style="single"):
    """Run the full experiment for one problem class."""
    print(f"\n{'='*70}")
    print(f"  {problem_class} — generating {n_solvers} neutral mutants")
    print(f"{'='*70}")

    probes = load_probes(problem_class)
    probe_family = {p["probe_id"]: p.get("family", p.get("probe_family", "unknown")) for p in probes}

    # Generate solvers
    solvers = []
    for i in range(n_solvers):
        code = generate_mutant(baseline_code)
        solvers.append((f"m{i:04d}", code))

    # Evaluate each solver
    results = []
    for sid, code in solvers:
        try:
            mod = load_solver_from_code(code, sid)
            solver_fn = mod.solve
        except Exception:
            # Compilation error — record as all-fail
            results.append({
                "sid": sid,
                "obs_fails": len(probes),
                "family_fails": {f: len(probes) for f in set(probe_family.values())},
                "b1": "REJECT",
                "c_gen": "REJECT",
                "disagree": 0,
                "compile_error": True,
            })
            continue

        # Evaluate on all probes
        probe_results = {}
        for probe in probes:
            solver_input = to_input(probe)
            try:
                truth = oracle_fn(solver_input)
                if invoke_style == "single":
                    observed = solver_fn(copy.deepcopy(solver_input))
                elif invoke_style == "lc79":
                    observed = solver_fn(copy.deepcopy(solver_input["board"]), solver_input["word"])
                elif invoke_style == "lc743":
                    observed = solver_fn(*solver_input)
                else:
                    observed = solver_fn(copy.deepcopy(solver_input))
            except Exception:
                observed = "EXC"
            probe_results[probe["probe_id"]] = (observed == truth)

        # Compute observed failures (all probes for this experiment)
        obs_fails = sum(1 for v in probe_results.values() if not v)

        # Compute family failures
        family_fails = defaultdict(int)
        for pid, passed in probe_results.items():
            if not passed:
                fam = probe_family.get(pid, "unknown")
                family_fails[fam] += 1

        # Decisions
        b1 = b1_decision(obs_fails)
        c_gen = c_genuine_decision(dict(family_fails))
        disagree = 1 if b1 != c_gen else 0

        results.append({
            "sid": sid,
            "obs_fails": obs_fails,
            "family_fails": dict(family_fails),
            "b1": b1,
            "c_gen": c_gen,
            "disagree": disagree,
            "compile_error": False,
        })

    # Compute metrics
    n_total = len(results)
    n_compile_error = sum(1 for r in results if r["compile_error"])
    n_valid = n_total - n_compile_error
    disagreements = [r["disagree"] for r in results if not r["compile_error"]]
    n_disagree = sum(disagreements)

    if n_valid > 0:
        p_hat, lo, hi = bootstrap_ci(disagreements)
    else:
        p_hat, lo, hi = 0, 0, 0

    # Failure rate distribution
    fail_rates = defaultdict(int)
    for r in results:
        if not r["compile_error"]:
            fail_rates[r["obs_fails"]] += 1

    # Family failure distribution for disagreeing solvers
    disagree_family_dist = defaultdict(int)
    for r in results:
        if r["disagree"] and not r["compile_error"]:
            for fam in r["family_fails"]:
                disagree_family_dist[fam] += 1

    return {
        "problem_class": problem_class,
        "n_total": n_total,
        "n_valid": n_valid,
        "n_compile_error": n_compile_error,
        "n_disagree": n_disagree,
        "p_hat": p_hat,
        "ci_lo": lo,
        "ci_hi": hi,
        "fail_rate_dist": dict(sorted(fail_rates.items())),
        "disagree_family_dist": dict(disagree_family_dist),
        "per_solver": results,
    }


def main():
    random.seed(20260611)  # Reproducible

    N_SOLVERS = 500

    # Problem class configs
    configs = [
        ("lc322", LC322_BASELINE, lc322_to_input, lc322_oracle, "single"),
        ("lc3946", LC3946_BASELINE, lc3946_to_input, lc3946_oracle, "single"),
        ("lc79", LC79_BASELINE, lc79_to_input, lc79_oracle, "lc79"),
        ("lc743", LC743_BASELINE, lc743_to_input, lc743_oracle, "lc743"),
    ]

    all_results = []
    for pc, baseline, to_input, oracle_fn, style in configs:
        try:
            r = run_problem_class(pc, baseline, N_SOLVERS, to_input, oracle_fn, style)
            all_results.append(r)
        except Exception as e:
            print(f"ERROR on {pc}: {e}")
            import traceback; traceback.print_exc()

    # ── Output tables ──────────────────────────────────────────────────────
    print("\n" + "=" * 90)
    print("  GLOBAL SUMMARY")
    print("=" * 90)
    print(f"{'Problem':<10} {'N':<6} {'Valid':<6} {'CE':<5} {'D':<6} {'P(D)':<8} {'95% CI':<16}")
    print("-" * 90)
    for r in all_results:
        ci_str = f"[{r['ci_lo']:.4f}, {r['ci_hi']:.4f}]"
        print(f"{r['problem_class']:<10} {r['n_total']:<6} {r['n_valid']:<6} "
              f"{r['n_compile_error']:<5} {r['n_disagree']:<6} {r['p_hat']:<8.4f} {ci_str:<16}")
    print()

    # Per-problem detail
    for r in all_results:
        print(f"\n{'-'*90}")
        print(f"  {r['problem_class']} -- FAIL RATE DISTRIBUTION (obs_fails: count)")
        print(f"{'-'*90}")
        for k in sorted(r["fail_rate_dist"].keys()):
            print(f"  {k}: {r['fail_rate_dist'][k]}")

        print(f"\n  {r['problem_class']} -- DISAGREEMENT FAMILY DISTRIBUTION")
        print(f"{'-'*90}")
        for fam, count in sorted(r["disagree_family_dist"].items()):
            print(f"  {fam}: {count}")

        # P(disagree | obs_fails = k)
        print(f"\n  {r['problem_class']} -- P(disagree | obs_fails = k)")
        print(f"{'-'*90}")
        obs_fails_disagree = defaultdict(lambda: [0, 0])
        for s in r["per_solver"]:
            if not s["compile_error"]:
                k = s["obs_fails"]
                obs_fails_disagree[k][0] += 1
                obs_fails_disagree[k][1] += s["disagree"]
        print(f"  {'k':<6} {'N':<6} {'D':<6} {'P(D|k)'}")
        for k in sorted(obs_fails_disagree.keys()):
            n_k, d_k = obs_fails_disagree[k]
            p = d_k / n_k if n_k > 0 else 0
            print(f"  {k:<6} {n_k:<6} {d_k:<6} {p:.4f}")

    # Cross-problem comparison
    print(f"\n{'='*90}")
    print("  CROSS-PROBLEM: Is P(D) invariant?")
    print(f"{'='*90}")
    p_hats = [r["p_hat"] for r in all_results if r["n_valid"] > 0]
    if len(p_hats) >= 2:
        max_diff = max(p_hats) - min(p_hats)
        print(f"  Range of P(D): [{min(p_hats):.4f}, {max(p_hats):.4f}]")
        print(f"  Max pairwise difference: {max_diff:.4f}")
        print(f"  All CIs overlap: ", end="")
        cis = [(r["ci_lo"], r["ci_hi"]) for r in all_results if r["n_valid"] > 0]
        all_overlap = all(
            cis[i][0] <= cis[j][1] and cis[j][0] <= cis[i][1]
            for i in range(len(cis)) for j in range(i+1, len(cis))
        )
        print("YES" if all_overlap else "NO")
    print("=" * 90)

    # Write raw results
    output = {
        "seed": 20260611,
        "n_solvers_per_class": N_SOLVERS,
        "summary": [{
            "problem_class": r["problem_class"],
            "n_valid": r["n_valid"],
            "n_disagree": r["n_disagree"],
            "p_hat": r["p_hat"],
            "ci_lo": r["ci_lo"],
            "ci_hi": r["ci_hi"],
        } for r in all_results],
    }
    out_path = REPO / "results" / "csse_v2_result.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()

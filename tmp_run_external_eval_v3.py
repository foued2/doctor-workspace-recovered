"""Evaluate external corpus with file-based adapter layer."""
import json
import os
import sys
import copy
import importlib.util
import threading
from collections import defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

from solver_adapter import detect_interface, write_adapter, cleanup_adapter, ADAPTER_DIR

def load_external_corpus():
    path = os.path.join(REPO, "data", "external_solver_corpus.json")
    with open(path) as f:
        return json.load(f)

def load_probes(problem_class):
    if problem_class == "LC322":
        path = os.path.join(REPO, "data", "midweather_fingerprint_lc322_probe_index.json")
        with open(path) as f:
            data = json.load(f)
        return data["probes"]
    elif problem_class == "LC79":
        path = os.path.join(REPO, "data", "midweather_fingerprint_lc79_probe_index.json")
        with open(path) as f:
            data = json.load(f)
        return data["probes"]
    elif problem_class == "LC743":
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
    return []

def load_solver_from_adapter(wrap_path, sid):
    """Load solver from adapter wrapper module."""
    try:
        # Ensure ADAPTER_DIR is in sys.path for raw module imports
        if ADAPTER_DIR not in sys.path:
            sys.path.insert(0, ADAPTER_DIR)
        mod_name = f"adapted_{sid}"
        spec = importlib.util.spec_from_file_location(mod_name, wrap_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        raise e

def oracle_fn(problem_class, solver_input):
    if problem_class == "LC322":
        from doctor.adversarial.lc322_ground_truth import lc322_brute_force
        coins = list(solver_input[:-1])
        amount = int(solver_input[-1])
        return lc322_brute_force(coins, amount)
    elif problem_class == "LC79":
        from doctor.adversarial.lc79_ground_truth import lc79_brute_force
        board = [row[:] for row in solver_input["board"]]
        word = solver_input["word"]
        return lc79_brute_force(board, word)
    elif problem_class == "LC743":
        from doctor.oracles.lc743_oracle import lc743_oracle as _oracle
        times, n, k = solver_input
        return _oracle(times, n, k)

def to_input(problem_class, probe):
    if problem_class == "LC322":
        return [*list(probe["coins"]), int(probe["amount"])]
    elif problem_class == "LC79":
        return {"board": [row[:] for row in probe["board"]], "word": probe["word"]}
    elif problem_class == "LC743":
        return (probe["times"], probe["n"], probe["k"])

def invoke_solver(solver_fn, solver_input, problem_class, timeout=5):
    """Invoke solver with timeout."""
    import signal
    import ctypes

    def timeout_handler(signum, frame):
        raise TimeoutError("Solver timed out")

    if problem_class == "LC322":
        result = [None]
        def run():
            try:
                result[0] = solver_fn(copy.deepcopy(solver_input))
            except Exception as e:
                result[0] = f"EXC:{e}"
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()
        t.join(timeout)
        if t.is_alive():
            return "TIMEOUT"
        return result[0]
    elif problem_class == "LC79":
        result = [None]
        def run():
            try:
                result[0] = solver_fn(copy.deepcopy(solver_input["board"]), solver_input["word"])
            except Exception as e:
                result[0] = f"EXC:{e}"
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()
        t.join(timeout)
        if t.is_alive():
            return "TIMEOUT"
        return result[0]
    elif problem_class == "LC743":
        result = [None]
        def run():
            try:
                result[0] = solver_fn(*solver_input)
            except Exception as e:
                result[0] = f"EXC:{e}"
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()
        t.join(timeout)
        if t.is_alive():
            return "TIMEOUT"
        return result[0]

def b1_decision(obs_fails):
    return "ACCEPT" if obs_fails == 0 else "REJECT"

def c_genuine_decision(family_fails):
    if sum(family_fails.values()) == 0:
        return "ACCEPT"
    if len(family_fails) <= 1:
        return "ACCEPT"
    return "REJECT"

def main():
    corpus = load_external_corpus()

    by_problem = defaultdict(list)
    for s in corpus:
        by_problem[s["problem_id"]].append(s)

    results_all = []

    for problem_class in ["LC322", "LC79", "LC743"]:
        solvers = by_problem.get(problem_class, [])
        if not solvers:
            print(f"\n{problem_class}: no solvers, skipping")
            continue

        probes = load_probes(problem_class)
        probe_family = {}
        for p in probes:
            fam = p.get("family", "unknown")
            if ":" in str(fam):
                fam = str(fam).split(":")[0]
            probe_family[p["probe_id"]] = fam

        print(f"\n{'='*70}")
        print(f"  {problem_class}: {len(solvers)} external solvers, {len(probes)} probes")
        print(f"{'='*70}")

        results = []
        adapted_count = 0
        for solver in solvers:
            sid_label = solver["source_origin"][:50]
            code = solver["raw_code"]

            # Detect and adapt
            iface = detect_interface(code, problem_class)
            needs_adapt = not (iface["has_solve"] and not iface["has_class"])
            if needs_adapt:
                adapted_count += 1

            try:
                wrap_path, sid = write_adapter(code, problem_class, iface)
                mod = load_solver_from_adapter(wrap_path, sid)
                solver_fn = mod.solve
            except Exception as e:
                results.append({
                    "sid": sid_label,
                    "obs_fails": len(probes),
                    "family_fails": {f: len(probes) for f in set(probe_family.values())},
                    "b1": "REJECT",
                    "c_gen": "REJECT",
                    "disagree": 0,
                    "compile_error": True,
                    "known_outcome": solver["known_outcome"],
                    "error": str(e)[:100],
                })
                continue

            probe_results = {}
            for probe in probes:
                solver_input = to_input(problem_class, probe)
                try:
                    truth = oracle_fn(problem_class, solver_input)
                    observed = invoke_solver(solver_fn, solver_input, problem_class)
                except Exception:
                    observed = "EXC"
                probe_results[probe["probe_id"]] = (observed == truth)

            obs_fails = sum(1 for v in probe_results.values() if not v)

            family_fails = defaultdict(int)
            for pid, passed in probe_results.items():
                if not passed:
                    fam = probe_family.get(pid, "unknown")
                    family_fails[fam] += 1

            b1 = b1_decision(obs_fails)
            c_gen = c_genuine_decision(dict(family_fails))
            disagree = 1 if b1 != c_gen else 0

            results.append({
                "sid": sid_label,
                "obs_fails": obs_fails,
                "family_fails": dict(family_fails),
                "b1": b1,
                "c_gen": c_gen,
                "disagree": disagree,
                "compile_error": False,
                "known_outcome": solver["known_outcome"],
            })

        # Summary
        n_total = len(results)
        n_ce = sum(1 for r in results if r["compile_error"])
        n_valid = n_total - n_ce
        n_disagree = sum(1 for r in results if r["disagree"])
        p_d = n_disagree / n_valid if n_valid > 0 else 0

        print(f"  Adapted: {adapted_count}/{len(solvers)}")
        print(f"  Total: {n_total}, Valid: {n_valid}, CE: {n_ce}, D: {n_disagree}, P(D): {p_d:.4f}")

        # CE details
        if n_ce > 0:
            ce_reasons = [r.get("error", "?")[:60] for r in results if r["compile_error"]]
            print(f"  CE reasons (first 5): {ce_reasons[:5]}")

        # Failure rate distribution
        fail_dist = defaultdict(int)
        for r in results:
            if not r["compile_error"]:
                fail_dist[r["obs_fails"]] += 1
        print(f"  Fail rate distribution: {dict(sorted(fail_dist.items()))}")

        # P(D | k)
        obs_fails_disagree = defaultdict(lambda: [0, 0])
        for r in results:
            if not r["compile_error"]:
                k = r["obs_fails"]
                obs_fails_disagree[k][0] += 1
                obs_fails_disagree[k][1] += r["disagree"]

        print(f"  P(D | k):")
        for k in sorted(obs_fails_disagree.keys()):
            n_k, d_k = obs_fails_disagree[k]
            p = d_k / n_k if n_k > 0 else 0
            print(f"    k={k}: N={n_k}, D={d_k}, P(D|k)={p:.4f}")

        # Disagreement details
        disagrees = [r for r in results if r["disagree"]]
        if disagrees:
            print(f"  Disagreements:")
            for r in disagrees:
                print(f"    obs_fails={r['obs_fails']}, families={r['family_fails']}")

        results_all.append({
            "problem_class": problem_class,
            "n_total": n_total,
            "n_valid": n_valid,
            "n_ce": n_ce,
            "n_disagree": n_disagree,
            "p_hat": p_d,
            "results": results,
        })

    # Save
    out_path = os.path.join(REPO, "data", "external_corpus_eval_v3_result.json")
    with open(out_path, "w") as f:
        json.dump(results_all, f, indent=2)
    print(f"\nResults saved to {out_path}")

if __name__ == "__main__":
    main()

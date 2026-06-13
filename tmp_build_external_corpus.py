"""Build external solver corpus for LC322, LC79, LC743.

Sources:
- human_solvers/ (LC322 only, 37 solutions)
- ChatGPT-CodeGenAnalysis (LC322, LC79, LC743, passing only)

Each solver tagged with:
- problem_id
- source_origin
- raw_code
- known_outcome (if externally verified)
"""
import json
import os
import glob

REPO = os.path.dirname(os.path.abspath(__file__))

def load_chatgpt_solutions():
    """Load ChatGPT-CodeGenAnalysis solutions for target problems."""
    path = os.path.join(REPO, "data", "chatgpt_codegen_python.json")
    with open(path) as f:
        data = json.load(f)
    
    targets = {
        "322-coin-change": "LC322",
        "079-word-search": "LC79",
        "743-network-delay-time": "LC743",
    }
    
    solvers = []
    for entry in data:
        name = entry.get("name", "")
        if name in targets:
            solvers.append({
                "problem_id": targets[name],
                "source_origin": "ChatGPT-CodeGenAnalysis",
                "raw_code": entry.get("generated_code", ""),
                "known_outcome": "pass" if entry.get("is_pass") == 1 else "fail",
                "error_info": entry.get("error_info", ""),
            })
    return solvers

def load_human_solvers():
    """Load human_solvers/ for LC322."""
    solvers = []
    hs_dir = os.path.join(REPO, "human_solvers")
    
    for py_file in glob.glob(os.path.join(hs_dir, "**", "*.py"), recursive=True):
        if "__pycache__" in py_file:
            continue
        if "debug_page" in py_file or "debug_leetcode" in py_file:
            continue
        if "source_urls" in py_file:
            continue
            
        rel_path = os.path.relpath(py_file, hs_dir)
        
        # Determine if correct or incorrect based on filename
        basename = os.path.basename(py_file)
        is_wrong = basename.startswith("wrong_")
        
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                code = f.read()
        except:
            continue
        
        if len(code.strip()) < 20:
            continue
            
        solvers.append({
            "problem_id": "LC322",
            "source_origin": f"human_solvers/{rel_path}",
            "raw_code": code,
            "known_outcome": "fail" if is_wrong else "unknown",
        })
    
    return solvers

def main():
    corpus = []
    
    # Load ChatGPT solutions
    cgpt = load_chatgpt_solutions()
    corpus.extend(cgpt)
    print(f"ChatGPT-CodeGenAnalysis: {len(cgpt)} solvers")
    
    # Load human solvers
    human = load_human_solvers()
    corpus.extend(human)
    print(f"human_solvers: {len(human)} solvers")
    
    # Summary
    by_problem = {}
    for s in corpus:
        pid = s["problem_id"]
        if pid not in by_problem:
            by_problem[pid] = {"total": 0, "pass": 0, "fail": 0, "unknown": 0}
        by_problem[pid]["total"] += 1
        by_problem[pid][s["known_outcome"]] += 1
    
    print(f"\nTotal corpus: {len(corpus)} solvers")
    for pid, counts in sorted(by_problem.items()):
        print(f"  {pid}: {counts}")
    
    # Save corpus
    out_path = os.path.join(REPO, "data", "external_solver_corpus.json")
    with open(out_path, "w") as f:
        json.dump(corpus, f, indent=2)
    print(f"\nCorpus saved to {out_path}")

if __name__ == "__main__":
    main()

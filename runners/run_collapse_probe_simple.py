"""Simplified LC756 collapse probe."""
import sys, ast, re, math, json, random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\pakla\PycharmProjects\doctor-workspace-recovered")
sys.path.insert(0, str(ROOT))

# Extract solver source
def extract_solvers(filepath):
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    solvers = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("s") and node.name[1:].isdigit():
            start = node.lineno - 1
            end = node.end_lineno
            lines = source.splitlines()[start:end]
            solvers[node.name] = "\n".join(lines)
    return solvers

# Tokenize
def tokenize(code):
    code = re.sub(r"#.*$", "", code, flags=re.MULTILINE)
    code = re.sub(r'""".*?"""', "", code, flags=re.DOTALL)
    tokens = re.findall(r"\b\w+\b|[^\s\w]", code)
    return tokens

# Token overlap
def token_overlap(a, b):
    set_a, set_b = set(a), set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

# Paths
lc743_path = ROOT / "doctor" / "solvers" / "lc_743_solvers.py"
lc756_path = ROOT / "doctor" / "solvers" / "lc756" / "lc_756_solvers.py"

lc743 = extract_solvers(lc743_path)
lc756 = extract_solvers(lc756_path)

print(f"LC743: {len(lc743)} solvers")
print(f"LC756: {len(lc756)} solvers")

# Tokenize all
lc743_tok = {n: tokenize(c) for n, c in lc743.items()}
lc756_tok = {n: tokenize(c) for n, c in lc756.items()}

# Pairwise within LC756
sims = []
names = sorted(lc756_tok.keys())
for i in range(len(names)):
    for j in range(i+1, len(names)):
        s = token_overlap(lc756_tok[names[i]], lc756_tok[names[j]])
        sims.append(s)

avg_sim = sum(sims) / len(sims)
max_sim = max(sims)
min_sim = min(sims)

print(f"\nLC756 pairwise token overlap:")
print(f"  Average: {avg_sim:.4f}")
print(f"  Max: {max_sim:.4f}")
print(f"  Min: {min_sim:.4f}")

# Cross-population
cross = []
for n1 in lc743_tok:
    for n2 in lc756_tok:
        s = token_overlap(lc743_tok[n1], lc756_tok[n2])
        cross.append(s)
avg_cross = sum(cross) / len(cross)
print(f"\nCross-population similarity: {avg_cross:.4f}")

# Output divergence test
from doctor.oracles.lc743_oracle import lc743_oracle

rng = random.Random(42)
instances = []
for i in range(10):
    n = rng.randint(2, 4)
    k = 1
    edges = []
    for _ in range(rng.randint(1, 5)):
        u = rng.randint(1, n)
        v = rng.randint(1, n)
        if u != v:
            w = rng.randint(1, 5)
            edges.append([u, v, w])
    if edges:
        try:
            exp = lc743_oracle(edges, n, k)
            instances.append((edges, n, k, exp))
        except Exception:
            pass

print(f"\nGenerated {len(instances)} test instances")

# Import solvers
import importlib.util
spec = importlib.util.spec_from_file_location("lc743", str(lc743_path))
m43 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m43)

spec = importlib.util.spec_from_file_location("lc756", str(lc756_path))
m56 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m56)

# Run solvers with timeout (using threading)
import threading

class TimeoutError(Exception):
    pass

def run_with_timeout(fn, args, timeout=2):
    result = [None]
    def worker():
        try:
            result[0] = fn(*args)
        except Exception:
            pass
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None
    return result[0]

outputs_43 = {}
outputs_56 = {}

for name in [n for n in dir(m43) if n.startswith("s") and n[1:].isdigit()]:
    fn = getattr(m43, name)
    results = []
    for e, n, k, _ in instances:
        result = run_with_timeout(fn, (e, n, k), timeout=2)
        results.append(result)
    outputs_43[name] = results

for name in [n for n in dir(m56) if n.startswith("s") and n[1:].isdigit()]:
    fn = getattr(m56, name)
    results = []
    for e, n, k, _ in instances:
        result = run_with_timeout(fn, (e, n, k), timeout=2)
        results.append(result)
    outputs_56[name] = results

# Compute entropy per instance
def entropy(values):
    c = Counter(values)
    total = len(values)
    ent = 0
    for count in c.values():
        p = count / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent

entropy_43 = [entropy([outputs_43[n][i] for n in outputs_43]) for i in range(len(instances))]
entropy_56 = [entropy([outputs_56[n][i] for n in outputs_56]) for i in range(len(instances))]

avg_ent_43 = sum(entropy_43) / len(entropy_43)
avg_ent_56 = sum(entropy_56) / len(entropy_56)

print(f"\nOutput entropy (bits):")
print(f"  LC743: {avg_ent_43:.4f}")
print(f"  LC756: {avg_ent_56:.4f}")

# Output clustering
def clustering(outputs):
    names = sorted(outputs.keys())
    n_inst = len(next(iter(outputs.values())))
    ags = []
    for i in range(n_inst):
        vals = [outputs[n][i] for n in names]
        c = Counter(vals)
        ags.append(max(c.values()) / len(names))
    return sum(ags) / len(ags)

clust_43 = clustering(outputs_43)
clust_56 = clustering(outputs_56)

print(f"\nOutput clustering:")
print(f"  LC743: {clust_43:.4f}")
print(f"  LC756: {clust_56:.4f}")

# Collapse score
max_ent = math.log2(30)
out_conv = 1 - (avg_ent_56 / max_ent)
collapse = avg_sim * out_conv

print(f"\nCollapse metrics:")
print(f"  Structural similarity: {avg_sim:.4f}")
print(f"  Output convergence: {out_conv:.4f}")
print(f"  Collapse score: {collapse:.4f}")

if collapse > 0.5:
    print(f"  Regime: HIGH COLLAPSE")
elif avg_sim > 0.7 and out_conv < 0.3:
    print(f"  Regime: ORACLE-DRIVEN CHAOS")
elif avg_sim < 0.3 and out_conv < 0.3:
    print(f"  Regime: NOISE")
else:
    print(f"  Regime: MEANINGFUL DIVERSITY")

print(f"\nVerdict: {'COLLAPSED' if collapse > 0.5 else 'DISTINCT'}")

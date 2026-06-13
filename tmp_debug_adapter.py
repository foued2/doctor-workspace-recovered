"""Debug: test adapter on specific solvers."""
import os, sys, tempfile, importlib.util
from solver_adapter import detect_interface, wrap_solver

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

# Test on a few LC322 solvers
test_files = [
    "human_solvers/lc_bottomup_dp_v2.py",
    "human_solvers/lc_bfs_v1.py",
    "human_solvers/so_sources/correct.py",
    "human_solvers/so_sources/wrong_1_off_by_one.py",
]

for tf in test_files:
    path = os.path.join(REPO, tf)
    if not os.path.exists(path):
        print(f"SKIP {tf}: not found")
        continue
    with open(path) as f:
        code = f.read()

    iface = detect_interface(code, "LC322")
    adapted = wrap_solver(code, "LC322", iface)
    print(f"\n--- {tf} ---")
    print(f"  Interface: {iface}")

    # Try to compile
    try:
        compile(adapted, f"{tf}_adapted", "exec")
        print(f"  Compile: OK")
    except SyntaxError as e:
        print(f"  Compile: SYNTAX ERROR: {e}")
        # Show the wrapper part
        lines = adapted.split("\n")
        for i, line in enumerate(lines[-10:], len(lines)-9):
            print(f"    {i}: {line}")
        continue

    # Try to load
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=os.path.join(REPO, "tmp_solvers"))
    tmp.write(adapted)
    tmp.close()
    try:
        spec = importlib.util.spec_from_file_location("test_solver", tmp.name)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = mod.solve
        # Test call
        result = fn([[2,5,10], 26])
        print(f"  Load: OK, solve([2,5,10], 26) = {result}")
    except Exception as e:
        print(f"  Load: ERROR: {e}")
    finally:
        os.unlink(tmp.name)

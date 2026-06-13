"""Debug adapter v3."""
import os, sys
REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)

from solver_adapter import detect_interface, write_adapter, ADAPTER_DIR

# Test on a specific solver
path = os.path.join(REPO, "human_solvers", "lc_bottomup_dp_v2.py")
with open(path) as f:
    code = f.read()

iface = detect_interface(code, "LC322")
print(f"Interface: {iface}")

wrap_path, sid = write_adapter(code, "LC322", iface)
print(f"wrap_path: {wrap_path}")

# Read the wrapper
with open(wrap_path) as f:
    wrapper = f.read()
print(f"\nWrapper content:\n{wrapper}")

# Read the raw
raw_path = os.path.join(ADAPTER_DIR, f"{sid}_raw.py")
with open(raw_path) as f:
    raw = f.read()
print(f"\nRaw content (first 500 chars):\n{raw[:500]}")

# Try adding ADAPTER_DIR to sys.path and importing
sys.path.insert(0, ADAPTER_DIR)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"test_{sid}", wrap_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print(f"\nImport OK, solve exists: {hasattr(mod, 'solve')}")
except Exception as e:
    print(f"\nImport ERROR: {e}")

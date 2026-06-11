"""Solver adapter layer v3.

Uses file-based import to avoid indentation issues.
Writes original solver to temp file, creates wrapper that imports from it.
"""
import re
import os
import hashlib
import tempfile

REPO = os.path.dirname(os.path.abspath(__file__))
ADAPTER_DIR = os.path.join(REPO, "tmp_adapter_solvers")
os.makedirs(ADAPTER_DIR, exist_ok=True)


def detect_interface(code, problem_class):
    """Detect the solver interface pattern."""
    has_class = bool(re.search(r'class\s+\w+', code))

    if problem_class == "LC322":
        has_solve = bool(re.search(r'def\s+solve\s*\(', code))
        has_coinChange = bool(re.search(r'def\s+coinChange\s*\(', code))
        solve_single = bool(re.search(r'def\s+solve\s*\(\s*self\s*\)', code))
        solve_two = bool(re.search(r'def\s+solve\s*\(\s*\w+\s*,\s*\w+\s*\)', code))
        return {
            "has_class": has_class,
            "has_solve": has_solve,
            "has_target": has_coinChange,
            "target_name": "coinChange",
            "solve_arity": 1 if solve_single else (2 if solve_two else 0),
        }
    elif problem_class == "LC79":
        has_solve = bool(re.search(r'def\s+solve\s*\(', code))
        has_exist = bool(re.search(r'def\s+exist\s*\(', code))
        return {
            "has_class": has_class,
            "has_solve": has_solve,
            "has_target": has_exist,
            "target_name": "exist",
        }
    elif problem_class == "LC743":
        has_solve = bool(re.search(r'def\s+solve\s*\(', code))
        has_ndt = bool(re.search(r'def\s+networkDelayTime\s*\(', code))
        return {
            "has_class": has_class,
            "has_solve": has_solve,
            "has_target": has_ndt,
            "target_name": "networkDelayTime",
        }
    return {"has_class": has_class, "has_solve": False, "has_target": False, "target_name": ""}


def _stable_id(code):
    return "a" + hashlib.md5(code.encode()).hexdigest()[:12]


def write_adapter(code, problem_class, iface):
    """Write adapter files and return path to wrapper module."""
    sid = _stable_id(code)
    raw_path = os.path.join(ADAPTER_DIR, f"{sid}_raw.py")
    wrap_path = os.path.join(ADAPTER_DIR, f"{sid}_wrap.py")

    # Write raw solver code
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(code)

    # Write wrapper
    target = iface.get("target_name", "")

    if problem_class == "LC322":
        if iface["has_solve"] and not iface["has_class"]:
            if iface.get("solve_arity", 0) == 2:
                # solve(coins, amount) -> solve(solver_input)
                wrapper = f"""
from {sid}_raw import solve as _raw_solve

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return _raw_solve(coins, amount)
"""
            else:
                # Already correct
                wrapper = f"""
from {sid}_raw import solve
"""
        elif iface["has_class"]:
            wrapper = f"""
from {sid}_raw import Solution

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return Solution().{target}(coins, amount)
"""
        else:
            wrapper = f"""
from {sid}_raw import {target} as _fn

def solve(solver_input):
    coins = list(solver_input[:-1])
    amount = int(solver_input[-1])
    return _fn(coins, amount)
"""

    elif problem_class == "LC79":
        if iface["has_class"]:
            wrapper = f"""
from {sid}_raw import Solution

def solve(board, word):
    return Solution().{target}(board, word)
"""
        else:
            wrapper = f"""
from {sid}_raw import {target} as _fn

def solve(board, word):
    return _fn(board, word)
"""

    elif problem_class == "LC743":
        if iface["has_class"]:
            wrapper = f"""
from {sid}_raw import Solution

def solve(times, n, k):
    return Solution().{target}(times, n, k)
"""
        else:
            wrapper = f"""
from {sid}_raw import {target} as _fn

def solve(times, n, k):
    return _fn(times, n, k)
"""
    else:
        wrapper = f"from {sid}_raw import solve\n"

    with open(wrap_path, "w", encoding="utf-8") as f:
        f.write(wrapper)

    return wrap_path, sid


def cleanup_adapter(sid):
    """Remove adapter files."""
    for suffix in ["_raw.py", "_wrap.py", "_raw.pyc"]:
        path = os.path.join(ADAPTER_DIR, f"{sid}{suffix}")
        if os.path.exists(path):
            os.unlink(path)

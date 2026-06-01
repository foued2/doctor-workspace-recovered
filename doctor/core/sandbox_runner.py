from __future__ import annotations

from typing import Any, Optional


def run_solution_in_sandbox(code: str, input_args: Any = None, timeout: int = 5) -> Any:
    import subprocess
    import sys
    import tempfile
    import os

    sandbox_code = f"""\
{code}

import sys
args = {input_args!r} if {input_args is not None} else ()

_func = None
for _name in ["solution", "solve", "twoSum", "maxArea", "trap", "lengthOfLongestSubstring", "isValid", "exist", "coinChange", "arrange_numbers_divisible"]:
    if _name in dir() and callable(eval(_name)):
        _func = eval(_name)
        break
if _func is None:
    for _name in dir():
        if not _name.startswith("_") and callable(eval(_name)):
            _func = eval(_name)
            break

try:
    result = _func(*args) if _func else None
    print(repr(result))
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
    sys.exit(1)
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sandbox_code)
        temp_file = f.name

    try:
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        if output.startswith("ERROR:"):
            return None
        try:
            return eval(output)
        except:
            return output
    except (subprocess.TimeoutExpired, Exception):
        return None
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

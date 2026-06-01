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
try:
    result = solution(*args) if hasattr(solution, '__call__') else solve(*args)
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

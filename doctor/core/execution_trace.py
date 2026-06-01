"""Execution trace — runs a test case and captures output/error."""
from __future__ import annotations

import traceback
from time import perf_counter
from typing import Any, Callable, Optional


def run_test_with_trace(
    func: Callable,
    input_args: tuple,
    expected: Any,
    timeout_ms: float = 5000.0,
) -> dict:
    """
    Run a single test case and return a trace dict.

    Returns:
        {
            "input": input_args,
            "expected": expected,
            "output": actual_output or None,
            "error": error_message or None,
            "runtime_ms": float,
        }
    """
    started = perf_counter()
    try:
        result = func(*input_args)
        runtime_ms = round((perf_counter() - started) * 1000, 3)
        return {
            "input": input_args,
            "expected": expected,
            "output": result,
            "error": None,
            "runtime_ms": runtime_ms,
        }
    except Exception as e:
        runtime_ms = round((perf_counter() - started) * 1000, 3)
        return {
            "input": input_args,
            "expected": expected,
            "output": None,
            "error": f"{type(e).__name__}: {e}",
            "runtime_ms": runtime_ms,
        }

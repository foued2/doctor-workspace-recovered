"""Execution policy — controls untrusted code execution safety."""
from __future__ import annotations

import os


class UnsafeExecutionBlocked(Exception):
    """Raised when untrusted execution is blocked by policy."""
    pass


def _is_untrusted_execution_allowed() -> bool:
    """Check if untrusted execution is permitted via environment variable."""
    return os.environ.get("DOCTOR_ALLOW_UNTRUSTED_EXECUTION", "0") == "1"


def assert_untrusted_execution_allowed(context: str = "") -> None:
    """Assert that untrusted execution is allowed. Raises UnsafeExecutionBlocked if not."""
    if not _is_untrusted_execution_allowed():
        raise UnsafeExecutionBlocked(
            f"Untrusted execution blocked{f' in {context}' if context else ''}. "
            f"Set DOCTOR_ALLOW_UNTRUSTED_EXECUTION=1 to allow."
        )


def candidate_writes_allowed() -> bool:
    """Check if candidate artifact writes are permitted."""
    return os.environ.get("DOCTOR_ALLOW_CANDIDATE_WRITES", "0") == "1"

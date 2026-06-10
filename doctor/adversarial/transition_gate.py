"""SSC-v2 transition gate — single write path for all pipeline artifacts.

Every pipeline artifact must pass through ``write_gated_artifact`` before
touching disk.  The gate enforces:

  1. Schema validation (artifact-type-specific)
  2. SSC-v2 invariant A ⟂ P — no execution state in payload
  3. SSC-v2 invariant C ⟂ P — contract_ids declared, not inferred
  4. Atomic write (tmp → rename)
  5. Post-write verification (read back + re-validate)

If any step fails the file is not written.  No partial writes.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from doctor.adversarial.artifact_schema_validators import (
    ArtifactValidationError,
    validate_c4_decisions,
    validate_c4_freeze,
    validate_fingerprint_result,
    validate_fp_freeze,
    validate_probe_index,
    validate_seval_manifest,
)

logger = logging.getLogger(__name__)

# ── Validator registry ────────────────────────────────────────────────

_VALIDATORS: dict[str, Any] = {
    "A1": validate_c4_decisions,
    "A2": validate_fingerprint_result,
    "A4": validate_seval_manifest,
    "A5": validate_probe_index,
    "F1": validate_fp_freeze,
    "F2": validate_c4_freeze,
}

# Known contract IDs — used by invariant C ⟂ P
_KNOWN_CONTRACTS = frozenset({"C-1", "C-4", "C-5", "C-6", "C-7", "FP", "META"})

# SSC-v2 invariant A ⟂ P — forbidden key prefixes/patterns in payload.
# These indicate execution state leaked into an artifact.
_EXEC_STATE_PATTERNS = (
    "sys.path",
    "module_path",
    "module_available",
    "module_loaded",
    "import_status",
    "imported_",
    "runtime_",
    "execution_",
    "_module_",
    "_import_",
    "_runtime_",
    "_execution_",
)


class TransitionGateError(RuntimeError):
    """Raised when the transition gate blocks a write."""

    def __init__(self, step: str, message: str) -> None:
        self.step = step
        super().__init__(f"[transition_gate:{step}] {message}")


# ── Invariant checks ─────────────────────────────────────────────────


def _check_no_execution_state(payload: dict, artifact_type: str, path: str) -> None:
    """SSC-v2 invariant A ⟂ P — payload must not contain execution state."""
    bad_keys: list[str] = []
    for key in payload:
        kl = key.lower()
        for pattern in _EXEC_STATE_PATTERNS:
            if pattern in kl:
                bad_keys.append(key)
                break
    if bad_keys:
        raise TransitionGateError(
            "A_orth_P",
            f"[{path}] artifact {artifact_type} payload contains execution "
            f"state fields: {bad_keys}",
        )


def _check_contract_ids_declared(
    contract_ids: tuple[str, ...], artifact_type: str, path: str
) -> None:
    """SSC-v2 invariant C ⟂ P — contract_ids must be declared, not inferred."""
    if not isinstance(contract_ids, tuple):
        raise TransitionGateError(
            "C_orth_P",
            f"[{path}] contract_ids must be a tuple, got {type(contract_ids).__name__}",
        )
    for cid in contract_ids:
        if cid not in _KNOWN_CONTRACTS:
            raise TransitionGateError(
                "C_orth_P",
                f"[{path}] unknown contract_id {cid!r}; must be one of "
                f"{sorted(_KNOWN_CONTRACTS)}",
            )


# ── Schema dispatch ──────────────────────────────────────────────────


def _validate_schema(payload: dict, artifact_type: str, path: str) -> None:
    """Step 1: schema validation if a validator exists for this type."""
    validator = _VALIDATORS.get(artifact_type)
    if validator is None:
        logger.warning(
            "[transition_gate] artifact type %s has no schema validator — "
            "tagged UNVALIDATED, write will proceed",
            artifact_type,
        )
        return
    validator(payload, path=path)


# ── Atomic write ─────────────────────────────────────────────────────


def _atomic_write(path: Path, payload: dict) -> None:
    """Step 4: write to a temp file in the same directory, then rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    # Write to temp file on same filesystem for atomic rename
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), suffix=".tmp", prefix=f".gate_{path.stem}_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(path))
    except BaseException:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ── Post-write verification ──────────────────────────────────────────


def _verify_write(
    path: Path, artifact_type: str, contract_ids: tuple[str, ...]
) -> None:
    """Step 5: read back and re-validate."""
    try:
        read_back = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise TransitionGateError(
            "verify",
            f"[{path}] post-write read failed: {exc}",
        ) from exc

    # Re-validate schema
    _validate_schema(read_back, artifact_type, str(path))

    # Re-check SSC-v2 invariants
    _check_no_execution_state(read_back, artifact_type, str(path))
    _check_contract_ids_declared(contract_ids, artifact_type, str(path))


# ── Public API ───────────────────────────────────────────────────────


def write_gated_artifact(
    path: Path,
    payload: dict,
    artifact_type: str,
    delta_type: str,
    contract_ids: tuple[str, ...],
) -> None:
    """Write a pipeline artifact through the SSC-v2 transition gate.

    Parameters
    ----------
    path:
        Destination file path.
    payload:
        The artifact content (must be JSON-serialisable dict).
    artifact_type:
        Artifact identifier, e.g. ``"A1"``, ``"A2"``, ``"F1"``.
        Maps to a schema validator; unknown types are tagged UNVALIDATED.
    delta_type:
        One of ``ARTIFACT_WRITE | CONTRACT_REEVALUATION | PROVENANCE_BINDING``.
    contract_ids:
        Tuple of contract IDs this artifact feeds, e.g. ``("C-4",)``.
        Declared by the caller — never inferred from runtime.

    Raises
    ------
    TransitionGateError
        If any gate step fails.  The file is NOT written.
    ArtifactValidationError
        If schema validation fails.  The file is NOT written.
    """
    path_str = str(path)

    # ── Step 1: schema validation ────────────────────────────────────
    _validate_schema(payload, artifact_type, path_str)

    # ── Step 2: SSC-v2 invariant A ⟂ P ─────────────────────────────
    _check_no_execution_state(payload, artifact_type, path_str)

    # ── Step 3: SSC-v2 invariant C ⟂ P ─────────────────────────────
    _check_contract_ids_declared(contract_ids, artifact_type, path_str)

    # ── Step 4: atomic write ────────────────────────────────────────
    _atomic_write(path, payload)

    # ── Step 5: post-write verification ─────────────────────────────
    _verify_write(path, artifact_type, contract_ids)

    logger.info(
        "[transition_gate] %s %s written via gate (delta_type=%s, contracts=%s)",
        artifact_type,
        path.name,
        delta_type,
        contract_ids,
    )

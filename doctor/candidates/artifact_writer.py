"""Artifact writer — writes candidate artifacts to disk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from doctor.adversarial.transition_gate import write_gated_artifact


_ARTIFACT_DIR = Path("scratch/candidates")


def write_candidate(artifact: dict[str, Any]) -> Path:
    """
    Write a candidate artifact to disk through SSC-v2 transition gate.

    Returns the path to the written file.
    """
    problem_hash = artifact.get("problem_hash", "unknown")
    candidate_type = artifact.get("candidate_type", "unknown")
    filename = f"{problem_hash[:12]}_{candidate_type}.json"

    path = _ARTIFACT_DIR / filename
    write_gated_artifact(path, artifact, "META", "ARTIFACT_WRITE", ("META",))

    return path

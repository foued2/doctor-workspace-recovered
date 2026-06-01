"""Artifact writer — writes candidate artifacts to disk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_ARTIFACT_DIR = Path("scratch/candidates")


def write_candidate(artifact: dict[str, Any]) -> Path:
    """
    Write a candidate artifact to disk.

    Returns the path to the written file.
    """
    _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    problem_hash = artifact.get("problem_hash", "unknown")
    candidate_type = artifact.get("candidate_type", "unknown")
    filename = f"{problem_hash[:12]}_{candidate_type}.json"

    path = _ARTIFACT_DIR / filename
    path.write_text(json.dumps(artifact, indent=2, default=str), encoding="utf-8")

    return path

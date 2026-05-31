"""Versioned immutable registry for adversarial probe sets."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doctor.adversarial.experiment_contract import canonical_json, execution_hash


DEFAULT_PROBE_REGISTRY_DIR = Path("doctor/adversarial/probe_sets")
REQUIRED_PROBE_SET_FIELDS = {
    "probe_set_id",
    "problem_id",
    "manifold_set_id",
    "version",
    "semantic_intent",
    "probes",
    "version_hash",
}


class ProbeRegistryError(ValueError):
    pass


@dataclass(frozen=True)
class ProbeSet:
    probe_set_id: str
    problem_id: str
    manifold_set_id: str
    version: str
    semantic_intent: str
    probes: tuple[dict[str, Any], ...]
    version_hash: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProbeSet":
        missing = sorted(REQUIRED_PROBE_SET_FIELDS - set(data))
        if missing:
            raise ProbeRegistryError(f"probe set missing required fields: {missing}")
        probes = data["probes"]
        if not isinstance(probes, list) or not probes:
            raise ProbeRegistryError("probe set must contain a non-empty probes list")
        computed_hash = compute_probe_set_hash(data)
        if data["version_hash"] != computed_hash:
            raise ProbeRegistryError(
                f"probe set version_hash mismatch for {data['probe_set_id']}: "
                f"{data['version_hash']} != {computed_hash}"
            )
        probe_ids = [str(row.get("probe_id")) for row in probes]
        if len(probe_ids) != len(set(probe_ids)):
            raise ProbeRegistryError(f"duplicate probe_id in {data['probe_set_id']}")
        return cls(
            probe_set_id=str(data["probe_set_id"]),
            problem_id=str(data["problem_id"]),
            manifold_set_id=str(data["manifold_set_id"]),
            version=str(data["version"]),
            semantic_intent=str(data["semantic_intent"]),
            probes=tuple(dict(row) for row in probes),
            version_hash=str(data["version_hash"]),
        )


class ProbeRegistry:
    def __init__(self, probe_sets: list[ProbeSet]) -> None:
        self._probe_sets = {probe_set.probe_set_id: probe_set for probe_set in probe_sets}
        if len(self._probe_sets) != len(probe_sets):
            raise ProbeRegistryError("duplicate probe_set_id in registry")

    @classmethod
    def from_directory(cls, directory: str | Path = DEFAULT_PROBE_REGISTRY_DIR) -> "ProbeRegistry":
        root = Path(directory)
        probe_sets = [
            ProbeSet.from_dict(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(root.glob("*.json"))
        ]
        return cls(probe_sets)

    def get(self, probe_set_id: str) -> ProbeSet:
        if probe_set_id not in self._probe_sets:
            raise ProbeRegistryError(f"unknown probe_set_id: {probe_set_id}")
        return self._probe_sets[probe_set_id]

    def validate_binding(self, descriptor: dict[str, Any]) -> None:
        probe_set_id = descriptor.get("probe_set_id")
        if not probe_set_id:
            raise ProbeRegistryError("descriptor missing probe_set_id")
        probe_set = self.get(str(probe_set_id))
        if probe_set.problem_id != descriptor.get("problem_id"):
            raise ProbeRegistryError("probe_set problem_id does not match descriptor")
        if probe_set.manifold_set_id != descriptor.get("manifold_set_id"):
            raise ProbeRegistryError("probe_set manifold_set_id does not match descriptor")

    def probe_set_ids(self) -> list[str]:
        return sorted(self._probe_sets)


def compute_probe_set_hash(data: dict[str, Any]) -> str:
    stable = {
        key: value
        for key, value in data.items()
        if key != "version_hash"
    }
    return execution_hash(stable)


def load_probe_registry(directory: str | Path = DEFAULT_PROBE_REGISTRY_DIR) -> ProbeRegistry:
    return ProbeRegistry.from_directory(directory)

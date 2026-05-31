from __future__ import annotations

import json
from pathlib import Path

import pytest

from doctor.adversarial.probe_registry import (
    ProbeRegistryError,
    compute_probe_set_hash,
    load_probe_registry,
)


def test_probe_registry_loads_checked_in_probe_sets():
    registry = load_probe_registry()
    assert registry.probe_set_ids() == [
        "lc322-closed-six-family-basis-v1",
        "lc322-expanded-eight-family-basis-v1",
        "lc322-search-resource-truncation-v1",
        "lc45-six-manifold-probe-set-v1",
    ]


def test_probe_set_hashes_are_content_bound():
    for path in Path("doctor/adversarial/probe_sets").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["version_hash"] == compute_probe_set_hash(data)


def test_probe_registry_validates_descriptor_binding():
    registry = load_probe_registry()
    registry.validate_binding(
        {
            "problem_id": "lc45",
            "manifold_set_id": "lc45-six-manifold-probe-set-v1",
            "probe_set_id": "lc45-six-manifold-probe-set-v1",
        }
    )
    with pytest.raises(ProbeRegistryError, match="manifold_set_id"):
        registry.validate_binding(
            {
                "problem_id": "lc45",
                "manifold_set_id": "wrong",
                "probe_set_id": "lc45-six-manifold-probe-set-v1",
            }
        )

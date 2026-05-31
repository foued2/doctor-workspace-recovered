"""Skeleton manifest writer for v0.3 protocol.

This module provides generic functions for constructing and writing v0.3 manifest
JSON files from already-supplied validated metadata.

It contains:
- no real benchmark content
- no hidden-set generation
- no visible-set generation
- no expected-output generation
- no validation run approval

Real v0.3 content remains blocked pending separate explicit approval.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from doctor.v03.hash_utils import hash_json_object


class V03ManifestWriterError(RuntimeError):
    pass


class V03ManifestKindError(V03ManifestWriterError):
    pass


class V03ManifestContentError(V03ManifestWriterError):
    pass


class V03RealContentBlockedError(V03ManifestWriterError):
    pass


ALLOWED_MANIFEST_KINDS = frozenset({
    "benchmark_pool",
    "split",
    "oracle",
    "solver",
    "perturbation",
    "validation_result",
})

MANIFEST_OUTPUT_FILENAMES: dict[str, str] = {
    "benchmark_pool": "V03_BENCHMARK_POOL_MANIFEST.json",
    "split": "V03_SPLIT_MANIFEST.json",
    "oracle": "V03_ORACLE_MANIFEST.json",
    "solver": "V03_SOLVER_MANIFEST.json",
    "perturbation": "V03_PERTURBATION_MANIFEST.json",
    "validation_result": "V03_VALIDATION_RESULTS.json",
}


@dataclass(frozen=True)
class ManifestWritePlan:
    kind: str
    output_path: Path
    manifest: dict[str, Any]
    manifest_hash: str
    is_template_or_test_only: bool = True
    approved_for_real_content: bool = False


def make_manifest_shell(
    kind: str,
    protocol_version: str,
    repo_commit: str,
    entries: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if kind not in ALLOWED_MANIFEST_KINDS:
        raise V03ManifestKindError(f"unknown manifest kind: {kind!r}")
    manifest: dict[str, Any] = {
        "protocol_version": protocol_version,
        "manifest_kind": kind,
        "repo_commit": repo_commit,
    }
    if kind in ("benchmark_pool", "split"):
        manifest["sealed"] = False
        manifest["hidden_opened"] = False
    if entries is not None:
        manifest["entries"] = entries
    else:
        manifest["entries"] = []
    if metadata is not None:
        manifest["metadata"] = metadata
    return manifest


def validate_manifest_is_safe_to_write(
    manifest: dict[str, Any],
    allow_real_content: bool = False,
) -> None:
    metadata = manifest.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    dangerous_flags = []
    if metadata.get("approved_for_real_content") is True and not allow_real_content:
        dangerous_flags.append(
            "approved_for_real_content=True requires allow_real_content=True"
        )
    if metadata.get("hidden_set_generated") is True:
        dangerous_flags.append("hidden_set_generated=True is not permitted")
    if metadata.get("hidden_validation_run") is True:
        dangerous_flags.append("hidden_validation_run=True is not permitted")
    if metadata.get("contains_real_benchmark_content") is True:
        dangerous_flags.append("contains_real_benchmark_content=True is not permitted")
    if metadata.get("contains_expected_outputs") is True:
        dangerous_flags.append("contains_expected_outputs=True is not permitted")
    if metadata.get("contains_hidden_content") is True:
        dangerous_flags.append("contains_hidden_content=True is not permitted")
    if metadata.get("contains_visible_content") is True:
        dangerous_flags.append("contains_visible_content=True is not permitted")

    if dangerous_flags:
        raise V03ManifestContentError(
            "manifest write blocked: " + "; ".join(dangerous_flags)
        )


def make_write_plan(
    kind: str,
    output_dir: str | Path,
    manifest: dict[str, Any],
    allow_real_content: bool = False,
) -> ManifestWritePlan:
    if kind not in ALLOWED_MANIFEST_KINDS:
        raise V03ManifestKindError(f"unknown manifest kind: {kind!r}")
    if kind != manifest.get("manifest_kind"):
        raise V03ManifestKindError(
            f"kind {kind!r} does not match manifest manifest_kind "
            f"{manifest.get('manifest_kind')!r}"
        )
    validate_manifest_is_safe_to_write(manifest, allow_real_content=allow_real_content)
    manifest_hash = hash_json_object(manifest)
    filename = MANIFEST_OUTPUT_FILENAMES[kind]
    output_path = Path(output_dir) / filename
    metadata = manifest.get("metadata", {})
    is_template_only = metadata.get("template_only", True)
    approved = metadata.get("approved_for_real_content", False)
    return ManifestWritePlan(
        kind=kind,
        output_path=output_path,
        manifest=manifest,
        manifest_hash=manifest_hash,
        is_template_or_test_only=is_template_only,
        approved_for_real_content=approved,
    )


def write_manifest_plan(plan: ManifestWritePlan) -> tuple[Path, str]:
    os.makedirs(plan.output_path.parent, exist_ok=True)
    with open(plan.output_path, "w", encoding="utf-8") as handle:
        json.dump(plan.manifest, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")
    return plan.output_path, plan.manifest_hash


def write_template_manifest(
    kind: str,
    output_dir: str | Path,
    protocol_version: str,
    repo_commit: str,
) -> tuple[Path, str]:
    metadata: dict[str, Any] = {
        "template_only": True,
        "contains_real_benchmark_content": False,
        "contains_hidden_content": False,
        "contains_visible_content": False,
        "contains_expected_outputs": False,
        "hidden_set_generated": False,
        "hidden_validation_run": False,
        "full_v03_build_approved": False,
    }
    manifest = make_manifest_shell(
        kind=kind,
        protocol_version=protocol_version,
        repo_commit=repo_commit,
        metadata=metadata,
    )
    plan = make_write_plan(kind=kind, output_dir=output_dir, manifest=manifest)
    return write_manifest_plan(plan)


def assert_real_content_not_approved() -> None:
    raise V03RealContentBlockedError(
        "Real v0.3 manifest content is blocked pending separate explicit approval."
    )

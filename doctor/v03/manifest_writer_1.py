from __future__ import annotations

import json
from pathlib import Path

import pytest

from doctor.v03.manifest_writer import (
    MANIFEST_OUTPUT_FILENAMES,
    V03ManifestContentError,
    V03ManifestKindError,
    V03ManifestWriterError,
    V03RealContentBlockedError,
    assert_real_content_not_approved,
    make_manifest_shell,
    make_write_plan,
    validate_manifest_is_safe_to_write,
    write_manifest_plan,
    write_template_manifest,
)

_VALID_MANIFEST = {
    "protocol_version": "v0.3",
    "manifest_kind": "oracle",
    "repo_commit": "abc123",
    "entries": [{"oracle_id": "test"}],
    "metadata": {"template_only": True},
}

_VALID_KINDS = ("benchmark_pool", "split", "oracle", "solver", "perturbation", "validation_result")


class TestMakeManifestShell:
    def test_creates_empty_manifest_with_required_fields(self) -> None:
        manifest = make_manifest_shell("oracle", "v0.3", "abc123")
        assert manifest["protocol_version"] == "v0.3"
        assert manifest["manifest_kind"] == "oracle"
        assert manifest["repo_commit"] == "abc123"
        assert manifest["entries"] == []

    def test_does_not_invent_entries(self) -> None:
        manifest = make_manifest_shell("oracle", "v0.3", "abc123")
        assert len(manifest["entries"]) == 0

    def test_adds_sealed_and_hidden_opened_for_benchmark_pool(self) -> None:
        manifest = make_manifest_shell("benchmark_pool", "v0.3", "abc123")
        assert manifest["sealed"] is False
        assert manifest["hidden_opened"] is False

    def test_adds_sealed_and_hidden_opened_for_split(self) -> None:
        manifest = make_manifest_shell("split", "v0.3", "abc123")
        assert manifest["sealed"] is False
        assert manifest["hidden_opened"] is False

    def test_accepts_entries(self) -> None:
        entries = [{"problem_id": "test"}]
        manifest = make_manifest_shell("oracle", "v0.3", "abc123", entries=entries)
        assert manifest["entries"] == entries

    def test_accepts_metadata(self) -> None:
        metadata = {"template_only": True}
        manifest = make_manifest_shell(
            "oracle", "v0.3", "abc123", metadata=metadata
        )
        assert manifest["metadata"] == metadata

    def test_rejects_unknown_kind(self) -> None:
        with pytest.raises(V03ManifestKindError, match="unknown manifest kind"):
            make_manifest_shell("invalid_kind", "v0.3", "abc123")


class TestValidateManifestIsSafeToWrite:
    def test_accepts_template_only_metadata(self) -> None:
        manifest = {"metadata": {"template_only": True}}
        validate_manifest_is_safe_to_write(manifest)

    def test_accepts_no_metadata(self) -> None:
        validate_manifest_is_safe_to_write({"entries": []})

    def test_rejects_hidden_set_generated(self) -> None:
        manifest = {"metadata": {"hidden_set_generated": True}}
        with pytest.raises(V03ManifestContentError, match="hidden_set_generated"):
            validate_manifest_is_safe_to_write(manifest)

    def test_rejects_hidden_validation_run(self) -> None:
        manifest = {"metadata": {"hidden_validation_run": True}}
        with pytest.raises(V03ManifestContentError, match="hidden_validation_run"):
            validate_manifest_is_safe_to_write(manifest)

    def test_rejects_contains_hidden_content(self) -> None:
        manifest = {"metadata": {"contains_hidden_content": True}}
        with pytest.raises(V03ManifestContentError, match="contains_hidden_content"):
            validate_manifest_is_safe_to_write(manifest)

    def test_rejects_contains_expected_outputs(self) -> None:
        manifest = {"metadata": {"contains_expected_outputs": True}}
        with pytest.raises(V03ManifestContentError, match="contains_expected_outputs"):
            validate_manifest_is_safe_to_write(manifest)

    def test_rejects_contains_visible_content(self) -> None:
        manifest = {"metadata": {"contains_visible_content": True}}
        with pytest.raises(V03ManifestContentError, match="contains_visible_content"):
            validate_manifest_is_safe_to_write(manifest)

    def test_rejects_contains_real_benchmark_content(self) -> None:
        manifest = {"metadata": {"contains_real_benchmark_content": True}}
        with pytest.raises(
            V03ManifestContentError, match="contains_real_benchmark_content"
        ):
            validate_manifest_is_safe_to_write(manifest)

    def test_rejects_approved_for_real_without_allow(self) -> None:
        manifest = {"metadata": {"approved_for_real_content": True}}
        with pytest.raises(V03ManifestContentError, match="approved_for_real_content"):
            validate_manifest_is_safe_to_write(manifest)

    def test_accepts_approved_for_real_with_allow(self) -> None:
        manifest = {"metadata": {"approved_for_real_content": True}}
        validate_manifest_is_safe_to_write(manifest, allow_real_content=True)


class TestMakeWritePlan:
    def test_computes_stable_hash(self) -> None:
        plan = make_write_plan("oracle", "/tmp", _VALID_MANIFEST)
        plan2 = make_write_plan("oracle", "/tmp", _VALID_MANIFEST)
        assert plan.manifest_hash == plan2.manifest_hash

    def test_hash_is_non_empty(self) -> None:
        plan = make_write_plan("oracle", "/tmp", _VALID_MANIFEST)
        assert isinstance(plan.manifest_hash, str)
        assert len(plan.manifest_hash) > 0

    def test_rejects_unknown_kind(self) -> None:
        manifest = {"protocol_version": "v0.3", "manifest_kind": "unknown"}
        with pytest.raises(V03ManifestKindError, match="unknown manifest kind"):
            make_write_plan("unknown", "/tmp", manifest)

    def test_rejects_kind_mismatch(self) -> None:
        manifest = {"protocol_version": "v0.3", "manifest_kind": "oracle"}
        with pytest.raises(V03ManifestKindError, match="does not match"):
            make_write_plan("split", "/tmp", manifest)

    def test_sets_is_template_or_test_only_from_metadata(self) -> None:
        plan = make_write_plan("oracle", "/tmp", _VALID_MANIFEST)
        assert plan.is_template_or_test_only is True

    def test_uses_correct_filename_per_kind(self) -> None:
        for kind in _VALID_KINDS:
            manifest = {
                "protocol_version": "v0.3",
                "manifest_kind": kind,
                "repo_commit": "abc",
                "metadata": {"template_only": True},
            }
            plan = make_write_plan(kind, "/tmp", manifest)
            expected_filename = MANIFEST_OUTPUT_FILENAMES[kind]
            assert plan.output_path.name == expected_filename, f"failed for {kind}"


class TestWriteManifestPlan:
    def test_writes_json_into_tmp_path(self, tmp_path: Path) -> None:
        plan = make_write_plan("oracle", tmp_path, _VALID_MANIFEST)
        path, hash_val = write_manifest_plan(plan)
        assert path.exists()
        assert path.name == MANIFEST_OUTPUT_FILENAMES["oracle"]
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        assert data["manifest_kind"] == "oracle"
        assert hash_val


class TestWriteTemplateManifest:
    def test_writes_template_only_manifest_to_tmp_path(self, tmp_path: Path) -> None:
        for kind in _VALID_KINDS:
            path, hash_val = write_template_manifest(
                kind, tmp_path, "v0.3", "abc123"
            )
            assert path.exists()
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            assert data["manifest_kind"] == kind
            assert data["protocol_version"] == "v0.3"
            assert data["metadata"]["template_only"] is True
            assert data["metadata"]["contains_real_benchmark_content"] is False
            assert data["metadata"]["contains_hidden_content"] is False
            assert data["metadata"]["contains_visible_content"] is False
            assert data["metadata"]["contains_expected_outputs"] is False
            assert data["metadata"]["hidden_set_generated"] is False
            assert data["metadata"]["hidden_validation_run"] is False
            assert data["metadata"]["full_v03_build_approved"] is False

    def test_computes_hash(self, tmp_path: Path) -> None:
        path, hash_val = write_template_manifest("oracle", tmp_path, "v0.3", "abc123")
        assert hash_val


class TestAssertRealContentNotApproved:
    def test_always_raises(self) -> None:
        with pytest.raises(V03RealContentBlockedError, match="blocked"):
            assert_real_content_not_approved()

"""Golden manifest: serializes, ignores timestamps, required + optional markers."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import (
    GoldenArtifactStatus,
    GoldenManifestBuilder,
    GoldenRunManifest,
)


def _manifest(present=None):
    return GoldenManifestBuilder().build(
        profile_id="fixture_tester_v0", fixture_hash="abc123",
        present_artifacts=present or {"fixture_input": True,
                                      "tester_report": True})


def test_golden_manifest_serializes():
    d = _manifest().to_dict()
    assert d["profile_id"] == "fixture_tester_v0"
    assert d["artifact_count"] > 0
    assert "ignores_timestamps_and_run_ids" in d


def test_timestamps_ignored():
    assert _manifest().to_dict()["ignores_timestamps_and_run_ids"] is True


def test_required_artifacts_defined():
    m = _manifest()
    required = m.required_artifacts
    assert required
    assert any(a.artifact_type == "fixture_input" for a in required)


def test_missing_required_detected():
    m = _manifest({"tester_report": True})  # fixture_input missing
    missing = [a.artifact_type for a in m.missing_required]
    assert "fixture_input" in missing


def test_optional_skipped_markers_supported():
    m = GoldenManifestBuilder().build(
        profile_id="fixture_tester_v0", fixture_hash="abc",
        present_artifacts={}, optional_skipped=["ontogenesis"])
    marker = m.artifact("skipped_optional_stage_marker")
    assert marker is not None
    assert marker.required is False
    assert marker.status in (GoldenArtifactStatus.OPTIONAL_MISSING,
                             GoldenArtifactStatus.PRESENT)
    assert m.optional_skipped == ["ontogenesis"]


def test_write_and_load_roundtrip(tmp_path):
    m = _manifest()
    m.write(str(tmp_path))
    loaded = GoldenRunManifest.load(str(tmp_path))
    assert loaded is not None
    assert loaded.fixture_hash == "abc123"
    assert loaded.profile_id == "fixture_tester_v0"

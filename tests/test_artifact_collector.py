"""Tests for the ArtifactCollector."""

from __future__ import annotations

import pytest

from solaris_ai_nn.evaluation.artifacts import ArtifactCollector


def test_collects_existing_artifacts(tmp_path):
    (tmp_path / "telemetry.json").write_text("{}")
    (tmp_path / "continuity_log.jsonl").write_text("")
    collector = ArtifactCollector(tmp_path)
    found = collector.collect()
    assert "telemetry" in found and "continuity_log" in found
    assert "inner_map" not in found


def test_warns_on_missing_optional(tmp_path):
    collector = ArtifactCollector(tmp_path)
    found = collector.collect()
    assert found == {}
    assert collector.warnings  # every known artifact warned, none raised


def test_required_missing_raises(tmp_path):
    collector = ArtifactCollector(tmp_path)
    with pytest.raises(FileNotFoundError):
        collector.collect(required=["telemetry"])

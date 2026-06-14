"""Post-pilot artifact loader: load, report missing, quarantine corrupt."""

from __future__ import annotations

import json

from solaris_ai_nn.post_pilot import PilotArtifactLoader


def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def test_loads_available_artifacts(tmp_path):
    base = tmp_path / "pilot1"
    state = tmp_path / "state"
    (base).mkdir()
    (base / "observability.jsonl").write_text(
        json.dumps({"kind": "metrics", "payload": {}}) + "\n")
    _write(state / "developmental_state.json", {"epoch": "infancy"})
    arts = PilotArtifactLoader(str(base), str(state)).load()
    assert "observability" in arts.index.present
    assert "developmental_state" in arts.index.present
    assert arts.has("observability")


def test_reports_missing_optional_artifacts(tmp_path):
    base = tmp_path / "pilot1"
    base.mkdir()
    arts = PilotArtifactLoader(str(base), str(tmp_path / "state")).load()
    assert "pilot_report" in arts.index.missing
    assert "hypotheses" in arts.index.missing
    # Missing is reported, never fatal.
    assert arts.completeness < 1.0


def test_corrupted_artifact_marked_unreadable(tmp_path):
    base = tmp_path / "pilot1"
    base.mkdir()
    (base / "PILOT_REPORT.json").write_text("{not valid json")
    arts = PilotArtifactLoader(str(base), str(tmp_path / "state")).load()
    assert "pilot_report" in arts.index.unreadable
    assert "pilot_report" not in arts.index.present


def test_loader_does_not_mutate_sources(tmp_path):
    base = tmp_path / "pilot1"
    base.mkdir()
    path = base / "observability.jsonl"
    path.write_text(json.dumps({"kind": "metrics", "payload": {}}) + "\n")
    before = path.read_text()
    PilotArtifactLoader(str(base), str(tmp_path / "state")).load()
    assert path.read_text() == before


def test_write_index_optional(tmp_path):
    base = tmp_path / "pilot1"
    base.mkdir()
    loader = PilotArtifactLoader(str(base), str(tmp_path / "state"))
    arts = loader.load()
    idx_path = loader.write_index(arts)
    assert (tmp_path / "pilot1" / "artifact_index.json").exists()
    data = json.loads(open(idx_path).read())
    assert "completeness" in data

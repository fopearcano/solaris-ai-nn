"""Snapshot manifest: artifacts indexed, missing/corrupt visible, negatives kept."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import ResearchSnapshotManifest


def test_artifacts_indexed():
    snap = ResearchSnapshotManifest()
    snap.index("post_merge_assimilation_report", payload={"x": 1})
    snap.index("evaluation_report", payload={"y": 2})
    d = snap.to_dict()
    assert d["snapshot_artifact_count"] == 2


def test_missing_artifacts_visible():
    snap = ResearchSnapshotManifest()
    snap.index("evaluation_report", payload={"y": 2})
    d = snap.to_dict()
    # Unsupplied artifact types remain visible as missing.
    assert "replication_report" in d["missing"]
    assert d["missing_snapshot_artifact_count"] >= 1


def test_corrupt_artifacts_visible():
    snap = ResearchSnapshotManifest()
    snap.mark_corrupt("falsification_report", detail="invalid JSON")
    d = snap.to_dict()
    assert "falsification_report" in d["corrupt"]


def test_negative_evidence_included():
    snap = ResearchSnapshotManifest()
    snap.index("falsification_report", payload={"falsified": ["claim_x"]},
               negative_evidence=True)
    d = snap.to_dict()
    assert "falsification_report" in d["negative_evidence_artifacts"]


def test_missing_path_recorded_not_present(tmp_path):
    snap = ResearchSnapshotManifest()
    snap.index("soak_dossier", path=str(tmp_path / "nope.json"))
    assert "soak_dossier" in snap.missing()

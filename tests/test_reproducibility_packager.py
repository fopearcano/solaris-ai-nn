"""Post-pilot reproducibility packager: index, checksums, no secrets."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.post_pilot import PilotArtifactLoader, ReproducibilityPackager


def _fixture(tmp_path, big=False):
    base = tmp_path / "pilot1"
    state = tmp_path / "state"
    base.mkdir()
    state.mkdir()
    (base / "observability.jsonl").write_text(
        json.dumps({"kind": "metrics", "payload": {}}) + "\n")
    (base / "PILOT_REPORT.json").write_text(json.dumps(
        {"sections": {"config": {"seed": 7, "is_simulated": True,
                                 "enabled_modules": ["bridge"]}}}))
    # A secret-looking file that must never be packaged.
    (state / "api_key.json").write_text(json.dumps({"k": "xxx"}))
    if big:
        # Valid JSONL, but large enough to exceed the checksum-by-content cap.
        line = json.dumps({"kind": "incident",
                           "payload": {"pad": "x" * 200}}) + "\n"
        reps = (6 * 1024 * 1024) // len(line) + 1
        (base / "incidents.jsonl").write_text(line * reps)
    return base, state


def test_package_generated(tmp_path):
    base, state = _fixture(tmp_path)
    arts = PilotArtifactLoader(str(base), str(state)).load()
    pkg, paths = ReproducibilityPackager(base_dir=str(base)).build_and_write(
        arts)
    assert os.path.exists(paths["manifest"])
    assert pkg.seed == 7
    assert pkg.is_simulated is True


def test_checksum_manifest_created(tmp_path):
    base, state = _fixture(tmp_path)
    arts = PilotArtifactLoader(str(base), str(state)).load()
    pkg, paths = ReproducibilityPackager(base_dir=str(base)).build_and_write(
        arts)
    assert os.path.exists(paths["checksums"])
    assert any(v.startswith("sha256:") for v in pkg.checksum_manifest.values())


def test_secrets_not_included(tmp_path):
    base, state = _fixture(tmp_path)
    arts = PilotArtifactLoader(str(base), str(state)).load()
    # api_key isn't a tracked artifact name, but guard the rule directly too.
    pkg = ReproducibilityPackager(base_dir=str(base)).build(arts)
    assert all("api_key" not in k for k in pkg.checksum_manifest)


def test_huge_logs_indexed_not_copied(tmp_path):
    base, state = _fixture(tmp_path, big=True)
    arts = PilotArtifactLoader(str(base), str(state)).load()
    pkg = ReproducibilityPackager(base_dir=str(base)).build(arts)
    assert "incidents" in pkg.indexed_only
    assert pkg.checksum_manifest.get("incidents", "").startswith("indexed:")


def test_missing_artifacts_listed(tmp_path):
    base, state = _fixture(tmp_path)
    arts = PilotArtifactLoader(str(base), str(state)).load()
    pkg = ReproducibilityPackager(base_dir=str(base)).build(arts)
    assert "hypotheses" in pkg.missing_artifacts

"""Release manifest: generated, required/optional artifacts, unknown commit allowed."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_packaging import (
    ReleaseManifestBuilder,
    TesterReleaseManifest,
)
from solaris_ai_nn.tester_packaging.release_manifest import ReleaseArtifact


def test_manifest_generated():
    m = ReleaseManifestBuilder().build()
    d = m.to_dict()
    assert d["package_name"] == "solaris-ai-nn"
    assert d["readiness"] in ("ready", "ready_with_warnings", "blocked")
    assert d["calls_git"] is False
    assert d["publishes_release"] is False


def test_required_artifacts_listed():
    d = ReleaseManifestBuilder().build().to_dict()
    names = {a["name"] for a in d["artifacts"] if a["required"]}
    assert "pyproject.toml" in names
    assert "README.md" in names


def test_optional_artifacts_listed():
    d = ReleaseManifestBuilder().build().to_dict()
    kinds = {a["kind"] for a in d["artifacts"]}
    assert "cli_command" in kinds
    assert "module" in kinds


def test_unknown_commit_allowed():
    m = TesterReleaseManifest(commit="unknown")
    assert m.to_dict()["commit"] == "unknown"


def test_missing_required_blocks_readiness():
    m = TesterReleaseManifest()
    m.artifacts.append(ReleaseArtifact("pyproject.toml", "package_file", True,
                                       present=False))
    assert m.readiness == "blocked"


def test_write(tmp_path):
    path = ReleaseManifestBuilder().write(str(tmp_path))
    assert os.path.isfile(path)
    data = json.load(open(path))
    assert data["calls_git"] is False

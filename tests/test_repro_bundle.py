"""Repro bundle: manifest + README generated, no install/run/fetch behavior."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.research_baseline import ReproBundleBuilder
from solaris_ai_nn.research_baseline import repro_bundle


def test_bundle_manifest_generated(tmp_path):
    builder = ReproBundleBuilder()
    bundle = builder.build(baseline_version_id="rb_v1",
                           snapshot={"missing": ["replication_report"]},
                           state_dir=str(tmp_path))
    paths = builder.write(bundle, str(tmp_path))
    assert os.path.isfile(paths["manifest"])
    with open(paths["manifest"], encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["baseline_version_id"] == "rb_v1"
    assert "replication_report" in data["known_missing_artifacts"]


def test_readme_generated(tmp_path):
    builder = ReproBundleBuilder()
    bundle = builder.build(baseline_version_id="rb_v1", snapshot={},
                           state_dir=str(tmp_path))
    paths = builder.write(bundle, str(tmp_path))
    assert os.path.isfile(paths["readme"])
    with open(paths["readme"], encoding="utf-8") as fh:
        text = fh.read()
    assert "Reproducibility Bundle" in text
    assert "not a product release" in text.lower()


def test_no_install_run_fetch_behavior():
    bundle = ReproBundleBuilder().build(baseline_version_id="rb_v1",
                                        snapshot={})
    d = bundle.to_dict()
    assert d["installs_dependencies"] is False
    assert d["runs_commands"] is False
    assert d["fetches_remote"] is False
    src = inspect.getsource(repro_bundle)
    assert "subprocess" not in src
    assert "pip install" not in src
    assert "urllib" not in src and "requests" not in src


def test_distinguishes_evidence_provenance():
    bundle = ReproBundleBuilder().build(baseline_version_id="rb_v1", snapshot={})
    prov = set(bundle.evidence_provenance.values())
    assert "fixture" in prov
    assert "live_read_only" in prov
    assert "operator_provided" in prov

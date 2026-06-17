"""Packaging: console discovers artifacts, docs updated, inner map, eval metrics."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_console import (
    ArtifactKind,
    ConsoleArtifactDiscovery,
    SummaryCardKind,
    TesterConsoleRuntime,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_packaging_helpers import run_packaging  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_console_discovers_packaging_artifacts(tmp_path):
    run_packaging(tmp_path)
    disc = ConsoleArtifactDiscovery(tester_state_dir=str(tmp_path)).discover()
    assert disc.has(ArtifactKind.TESTER_PACKAGING_REPORT)
    assert disc.has(ArtifactKind.TESTER_INSTALL_GUIDE)
    rt = TesterConsoleRuntime(
        state_dir=os.path.join(str(tmp_path), "live"),
        tester_state_dir=str(tmp_path),
        console_dir=os.path.join(str(tmp_path), "console"), html=False)
    rt.run()
    assert any(c.kind == SummaryCardKind.PACKAGING for c in rt.cards)


def test_docs_updated():
    for rel in ("README.md", os.path.join("docs", "ARCHITECTURE.md")):
        text = open(os.path.join(_ROOT, rel)).read().lower()
        assert "packaging" in text or "install" in text


def test_inner_map_record(tmp_path):
    rt = run_packaging(tmp_path)
    rec = rt.inner_map_record()
    assert rec["packaging_run_id"]
    assert rec["installs_packages"] is False
    from solaris_ai_nn.inner_map.model import InnerMapModel
    m = InnerMapModel()
    m.tester_packaging = rec
    assert m.to_dict()["tester_packaging"]["packaging_run_id"]


def test_evaluation_metrics_computed(tmp_path):
    rt = run_packaging(tmp_path)
    from solaris_ai_nn.evaluation.metrics import tester_packaging_metrics
    metrics = tester_packaging_metrics(rt.packaging_status())
    assert metrics["present"] is True
    assert metrics["installs_packages"] is False
    assert metrics["tester_packaging_run_count"] == 1

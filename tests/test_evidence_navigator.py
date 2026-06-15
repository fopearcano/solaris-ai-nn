"""EvidenceNavigator: local artifact indexed; keyword search; corruption."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.operator_console import EvidenceNavigator, EvidenceType


def _seed(base):
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, "research_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"summary": "baseline beat random on safety",
                   "evidence_refs": ["r1", "r2"]}, fh)
    with open(os.path.join(base, "SAFETY_INVARIANT_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"status": "ok", "summary": "all held"}, fh)


def test_local_artifact_indexed(tmp_path):
    base = str(tmp_path / "ev")
    _seed(base)
    nav = EvidenceNavigator([base])
    assert nav.index() == 2


def test_search_by_keyword_works(tmp_path):
    base = str(tmp_path / "ev")
    _seed(base)
    nav = EvidenceNavigator([base])
    nav.index()
    results = nav.search("safety")
    assert results
    assert all("safety" in (r.excerpt + r.title + r.path).lower()
               for r in results)


def test_search_by_evidence_type(tmp_path):
    base = str(tmp_path / "ev")
    _seed(base)
    nav = EvidenceNavigator([base])
    nav.index()
    results = nav.search(evidence_type=EvidenceType.SAFETY_INVARIANT_RESULT)
    assert results
    assert all(r.evidence_type == EvidenceType.SAFETY_INVARIANT_RESULT
               for r in results)


def test_evidence_refs_returned(tmp_path):
    base = str(tmp_path / "ev")
    _seed(base)
    nav = EvidenceNavigator([base])
    nav.index()
    results = nav.search("baseline")
    assert results and results[0].evidence_refs == ["r1", "r2"]


def test_corrupted_artifact_reported(tmp_path):
    base = str(tmp_path / "ev")
    os.makedirs(base, exist_ok=True)
    # A broken symlink is listed by os.walk but cannot be read -> reported.
    link = os.path.join(base, "dangling.json")
    os.symlink(os.path.join(base, "missing_target.json"), link)
    nav = EvidenceNavigator([base])
    nav.index()
    assert nav.snapshot()["corrupted_count"] >= 1
    assert nav.snapshot()["external_search"] is False

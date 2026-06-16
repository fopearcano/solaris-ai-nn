"""Research cycle reports: documents written, disclaimers, ClaimGuard-safe."""

from __future__ import annotations

import os

from solaris_ai_nn.research_cycle import ResearchCycleRuntime


def _run(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "cycle_manifest": {"cycle_id": "cycle_1"},
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0}})
    rt.run()
    return rt


def test_all_documents_written(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("RESEARCH_CYCLE_REPORT.md", "RESEARCH_CYCLE_REPORT.json",
                     "CYCLE_STATE.md", "EVIDENCE_LEDGER.md", "ARTIFACT_GRAPH.md",
                     "DECISION_GATES.md", "OPERATOR_DECISIONS.md",
                     "BLOCKED_STATES.md", "NEXT_ACTIONS.md", "CYCLE_ARCHIVE.md"):
        assert expected in names


def test_report_has_disclaimers(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path), "RESEARCH_CYCLE_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read()
    assert "What this does NOT do" in text
    assert "No source code was modified." in text
    assert "system cannot approve" in text.lower() or \
        "cannot be auto-approved" in text.lower()


def test_report_claim_guard_safe(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    assert report["claim_guard_safe"] is True

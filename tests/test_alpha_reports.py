"""Alpha reports: all generated, safety disclaimers, ClaimGuard scan."""

from __future__ import annotations

import os

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator


def _run(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25)
    orch.run()
    return orch


def test_all_alpha_reports_generated(tmp_path):
    orch = _run(tmp_path)
    out = orch.write_artifacts()
    names = {os.path.basename(p) for p in out["documents"]}
    for expected in ("ALPHA_RESEARCH_SYSTEM_REPORT.md",
                     "ALPHA_RESEARCH_SYSTEM_REPORT.json",
                     "ALPHA_MODULE_REGISTRY.md", "ALPHA_DEMO_REPORT.md",
                     "ALPHA_CYCLE_STATUS.md", "ALPHA_OPERATOR_RUNBOOK.md"):
        assert expected in names


def test_safety_disclaimers_included(tmp_path):
    orch = _run(tmp_path)
    orch.write_artifacts()
    with open(os.path.join(str(tmp_path), "reports",
                           "ALPHA_RESEARCH_SYSTEM_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "no git or github operation occurred" in text
    assert "no feeders or hardware were controlled" in text
    assert "no consciousness/life/agency claim is made" in text


def test_claim_guard_scan_if_available(tmp_path):
    orch = _run(tmp_path)
    report = orch.write_artifacts()["report"]
    # When ClaimGuard is available the report is scanned and must be safe.
    if report["sections"]["claimguard_available"]:
        assert report["claim_guard_safe"] is True


def test_skipped_modules_shown(tmp_path):
    orch = AlphaResearchOrchestrator(state_dir=str(tmp_path), max_ticks=25,
                                     skip_optional=True)
    orch.run()
    orch.write_artifacts()
    with open(os.path.join(str(tmp_path), "reports",
                           "ALPHA_RESEARCH_SYSTEM_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read()
    assert "Skipped modules" in text

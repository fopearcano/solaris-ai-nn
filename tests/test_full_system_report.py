"""Full system report: claim-guarded, honest, written as JSON + Markdown."""

from __future__ import annotations

import json
from pathlib import Path

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    FullSystemReportBuilder,
    IntegrationHealthMonitor,
    RunContext,
    RunMode,
)


def _orch(tmp_path):
    ctx = RunContext(mode=RunMode.SHORT_DEMO, state_dir=str(tmp_path),
                     artifact_dir=str(tmp_path / "art"), max_steps=20,
                     enabled_modules=["bridge", "ecology", "governance",
                                      "world_model", "homeostasis",
                                      "executive"])
    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(ctx)
    orch.initialize()
    orch.run()
    return orch


def test_report_is_claim_guard_safe(tmp_path):
    orch = _orch(tmp_path)
    report = FullSystemReportBuilder().build(orch, IntegrationHealthMonitor())
    assert report.claim_guard_safe is True
    assert report.claim_guard_findings == 0


def test_report_disclaims_personhood(tmp_path):
    orch = _orch(tmp_path)
    report = FullSystemReportBuilder().build(orch)
    text = report.narrative.lower()
    assert "not a person" in text
    assert "simulation only" in text or "simulated" in text
    assert "no real-world action authority" in text


def test_report_written_to_disk(tmp_path):
    orch = _orch(tmp_path)
    report = FullSystemReportBuilder().build_and_write(
        orch, artifact_dir=str(tmp_path / "out"))
    paths = report.sections["report_paths"]
    assert Path(paths["json"]).exists() and Path(paths["markdown"]).exists()
    data = json.loads(Path(paths["json"]).read_text())
    assert data["sections"]["run"]["steps"] == orch.step_count
    assert orch.report_path == paths["json"]


def test_report_lists_modules_and_boundaries(tmp_path):
    orch = _orch(tmp_path)
    report = FullSystemReportBuilder().build(orch)
    assert report.sections["modules"]["enabled"]
    assert "Boundaries upheld" in report.narrative

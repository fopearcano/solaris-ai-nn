"""Tests for ClaimGuard wired into language report saving."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.language.reporting import ExperimentReportBuilder
from solaris_ai_nn.language.serialization import save_report


def _report(claim_text):
    return (ExperimentReportBuilder(title="Test report")
            .add_metadata(run_id="r1")
            .add_section("conclusion", claim_text)
            .build())


def test_safe_report_scanned_and_saved(tmp_path):
    report = _report("the substrate produced a Desire signal and adapted a "
                     "runtime parameter")
    scan = save_report(report, tmp_path / "r.json", tmp_path / "r.md")
    assert scan.safe
    data = json.loads((tmp_path / "r.json").read_text())
    assert data["claim_guard"]["safe"] is True
    md = (tmp_path / "r.md").read_text()
    assert "Claim Guard Warnings" not in md


def test_unsafe_claim_warning_saved(tmp_path):
    report = _report("the system is conscious and it wants more reward")
    scan = save_report(report, tmp_path / "r.json", tmp_path / "r.md")
    assert not scan.safe
    md = (tmp_path / "r.md").read_text()
    assert "## Claim Guard Warnings" in md
    assert "consciousness-inspired" in md or "Desire signal" in md
    data = json.loads((tmp_path / "r.json").read_text())
    assert data["claim_guard"]["finding_count"] >= 2


def test_block_mode_refuses_to_save(tmp_path):
    report = _report("the system is conscious")
    with pytest.raises(ValueError):
        save_report(report, tmp_path / "r.json", tmp_path / "r.md",
                    on_unsafe="block")
    assert not (tmp_path / "r.md").exists()


def test_runner_session_reports_are_clean(tmp_path):
    """The runner's own generated reports never trip ClaimGuard."""
    from solaris_ai_nn.governance.compliance import ClaimGuard
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

    runner = ContinuousRunner(state_dir=str(tmp_path / "state"), max_steps=40,
                              enable_language=True, seed=3)
    runner.run()
    report = getattr(runner, "_session_report", None)
    if report is not None:
        assert ClaimGuard().is_safe(report.to_markdown())

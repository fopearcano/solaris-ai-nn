"""Tests for optional report polishing in the language layer."""

from __future__ import annotations

from solaris_ai_nn.language.reporting import (
    ExperimentReportBuilder,
    save_polished_report,
)
from solaris_ai_nn.language.serialization import save_report
from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter
from solaris_ai_nn.llm_adapter.report_polish import ReportPolisher


def _report():
    return (ExperimentReportBuilder(title="Session report")
            .add_metadata(steps=60)
            .add_section("telemetry", {"steps": 60, "incident_count": 1})
            .build())


def test_raw_report_saved(tmp_path):
    report = _report()
    md_path = tmp_path / "session_report.md"
    save_report(report, tmp_path / "session_report.json", md_path)
    assert md_path.exists()
    result = save_polished_report(report, md_path)  # no polisher
    assert result["accepted"] is False
    assert result["polished"] is None
    assert "no polisher configured" in result["reasons"][0]


def test_polished_report_saved_if_safe(tmp_path):
    report = _report()
    md_path = tmp_path / "session_report.md"
    save_report(report, tmp_path / "session_report.json", md_path)
    result = save_polished_report(
        report, md_path, polisher=ReportPolisher(adapter=MockLLMAdapter()))
    assert result["accepted"] is True
    polished_path = tmp_path / "session_report.polished.md"
    assert polished_path.exists()
    polished = polished_path.read_text()
    assert "# Session report" in polished
    assert "60" in polished  # metrics intact
    # The raw report is untouched and remains the source of truth.
    assert md_path.exists()


def test_fallback_if_polish_unsafe(tmp_path):
    report = _report()
    md_path = tmp_path / "session_report.md"
    save_report(report, tmp_path / "session_report.json", md_path)
    result = save_polished_report(
        report, md_path,
        polisher=ReportPolisher(
            adapter=MockLLMAdapter(force_unsafe_output=True)))
    assert result["accepted"] is False
    assert result["reasons"]  # the rejection names its grounds
    assert not (tmp_path / "session_report.polished.md").exists()

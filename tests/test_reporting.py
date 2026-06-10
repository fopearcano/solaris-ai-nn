"""Tests for report building/rendering."""

from __future__ import annotations

import json

from solaris_ai_nn.language.reporting import ExperimentReportBuilder


def _report():
    return (ExperimentReportBuilder(title="Test report")
            .add_metadata(run_id="r1", substrate="esn")
            .add_section("runtime", {"steps": 50, "duration_seconds": 1.2})
            .add_section("signals", {"events": 50})
            .add_section("habits", {"pathways": 3})
            .build())


def test_builds_json_report():
    report = _report()
    data = json.loads(report.to_json())
    assert data["title"] == "Test report"
    assert data["sections"]["runtime"]["steps"] == 50
    assert data["metadata"]["substrate"] == "esn"


def test_builds_markdown_report():
    md = _report().to_markdown()
    assert md.startswith("# Test report")
    assert "## Runtime" in md and "## Signals" in md
    assert "- **steps**: 50" in md


def test_report_contains_limitations_and_unknowns():
    md = _report().to_markdown()
    assert "## Limitations and Unknowns" in md
    assert "not proven causation" in md
    assert "does not know" in md or "consciousness" in md


def test_extra_limitations_and_none_sections():
    report = (ExperimentReportBuilder()
              .add_section("skipped", None)  # None sections are dropped
              .add_limitation("custom caveat")
              .build())
    d = report.to_dict()
    assert "skipped" not in d["sections"]
    assert "custom caveat" in d["limitations"]

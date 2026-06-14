"""Pilot-2 report: JSON + Markdown generated, ClaimGuard scans."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.pilot2 import (
    GroundingAnalysis,
    Pilot2Config,
    Pilot2ReportBuilder,
    SourceReliabilityMonitor,
)


def _build(tmp_path):
    cfg = Pilot2Config(base_dir=str(tmp_path))
    ga = GroundingAnalysis()
    ga.add("proto_symbol", provenance_complete=True, repeated_pattern=True,
           persistent=True, evidence_refs=["r1"])
    mon = SourceReliabilityMonitor()
    mon.observe_poll("j", success=True, events=10, provenance=10)
    builder = Pilot2ReportBuilder(base_dir=str(tmp_path))
    return builder, builder.build_and_write(config=cfg, grounding=ga,
                                            reliability=mon)


def test_json_and_markdown_generated(tmp_path):
    _builder, report = _build(tmp_path)
    paths = report.sections["report_paths"]
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])
    data = json.loads(open(paths["json"]).read())
    assert data["pilot2_id"] == report.pilot2_id


def test_claim_guard_scans_report(tmp_path):
    _builder, report = _build(tmp_path)
    assert report.claim_guard_safe is True
    assert "never acted on the environment" in report.narrative


def test_report_sections_present(tmp_path):
    _builder, report = _build(tmp_path)
    for key in ("pilot2_summary", "source_reliability", "grounding_analysis",
                "nursery_vs_sensory_comparison", "limitations"):
        assert key in report.sections


def test_report_disclaims_actuation(tmp_path):
    _builder, report = _build(tmp_path)
    text = report.narrative.lower()
    assert "read-only" in text and "no actuation" in text

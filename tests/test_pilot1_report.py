"""Pilot-1 report: JSON + Markdown, structural-change section, ClaimGuard."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.pilot1 import (
    PilotConfig,
    PilotObservabilityCollector,
    PilotReportBuilder,
)


def _build(tmp_path, developmental=None):
    cfg = PilotConfig(base_dir=str(tmp_path))
    obs = PilotObservabilityCollector(base_dir=str(tmp_path))
    obs.observe(snapshot={"structural_change_score": 0.2,
                          "proto_symbol_count": 8,
                          "memory_size_bytes": 5000})
    builder = PilotReportBuilder(base_dir=str(tmp_path))
    return builder, builder.build_and_write(
        config=cfg, observability=obs,
        developmental=developmental or {"epoch": "infancy",
                                        "milestone_count": 2})


def test_json_and_markdown_generated(tmp_path):
    _builder, report = _build(tmp_path)
    paths = report.sections["report_paths"]
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])
    data = json.loads(open(paths["json"]).read())
    assert data["pilot_id"] == report.pilot_id


def test_structural_change_section_present(tmp_path):
    _builder, report = _build(tmp_path)
    section = report.sections["structural_change_analysis"]
    assert "verdict" in section
    assert "evidence_structure_changed" in section
    assert "evidence_only_accumulation" in section


def test_claim_guard_scans_report(tmp_path):
    _builder, report = _build(tmp_path)
    assert report.claim_guard_safe is True
    assert "not a person" in report.narrative.lower()


def test_accumulation_only_verdict(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    obs = PilotObservabilityCollector(base_dir=str(tmp_path))
    obs.observe(snapshot={"structural_change_score": 0.0,
                          "memory_size_bytes": 9999})
    builder = PilotReportBuilder(base_dir=str(tmp_path))
    report = builder.build(config=cfg, observability=obs, developmental={})
    verdict = report.sections["structural_change_analysis"]["verdict"]
    assert verdict in ("only accumulation observed",
                       "insufficient evidence to distinguish")

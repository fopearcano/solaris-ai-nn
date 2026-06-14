"""Sensory membrane reports: JSON + Markdown, ClaimGuard, limitations."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneReportBuilder,
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def _runtime(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    (root / "e.jsonl").write_text('{"a":1}\n{"a":2}\n')
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "state"), allowed_input_roots=[str(root)],
        enabled=True, simulated_sources_only=False,
        real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(root / "e.jsonl"),
                                      enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=2)
    return rt


def test_json_and_markdown_generated(tmp_path):
    rt = _runtime(tmp_path)
    report = SensoryMembraneReportBuilder(
        state_dir=str(tmp_path / "state")).build_and_write(rt)
    paths = report.sections["report_paths"]
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])
    data = json.loads(open(paths["json"]).read())
    assert "registered_sources" in data["sections"]


def test_claim_guard_scans_report(tmp_path):
    rt = _runtime(tmp_path)
    report = SensoryMembraneReportBuilder(
        state_dir=str(tmp_path / "state")).build(rt)
    assert report.claim_guard_safe is True
    assert "the system never acts on the world" in report.narrative


def test_limitations_included(tmp_path):
    rt = _runtime(tmp_path)
    report = SensoryMembraneReportBuilder(
        state_dir=str(tmp_path / "state")).build(rt)
    assert report.sections["limitations"]
    assert "## Limitations" in report.narrative


def test_read_only_flag_present(tmp_path):
    rt = _runtime(tmp_path)
    report = SensoryMembraneReportBuilder(
        state_dir=str(tmp_path / "state")).build(rt)
    assert report.sections["read_only"] is True

"""ResearchReportBuilder: JSON + Markdown; ClaimGuard; limitations."""

from __future__ import annotations

import os

from solaris_ai_nn.research_lab import ResearchReportBuilder


def _build(tmp_path):
    return ResearchReportBuilder(base_dir=str(tmp_path)).build_and_write(
        variants=["full"], baselines=["random_action_baseline"],
        ablations=["no_proto_language", "no_LOGOS"])


def test_json_report_generated(tmp_path):
    _build(tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path), "RESEARCH_REPORT.json"))


def test_markdown_generated(tmp_path):
    _build(tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path), "RESEARCH_REPORT.md"))


def test_claim_guard_scans_report(tmp_path):
    report = _build(tmp_path)
    assert report.claim_guard_safe is True


def test_limitations_included(tmp_path):
    report = _build(tmp_path)
    joined = " ".join(report.sections["limitations"]).lower()
    assert "do not measure or prove consciousness" in joined
    assert "negative and inconclusive results are preserved" in joined


def test_narrative_states_not_consciousness(tmp_path):
    report = _build(tmp_path)
    assert "do not measure or prove consciousness" in report.narrative.lower()

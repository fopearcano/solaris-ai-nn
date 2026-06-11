"""Tests for the executive reports."""

from __future__ import annotations

import json

from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.executive.reports import ExecutiveReportBuilder
from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def _layer(tmp_path):
    layer = ExecutiveLayer(state_dir=tmp_path)
    layer.decide([DesireCandidate(proposal="rest", motivation=0.6,
                                  confidence=0.6),
                  DesireCandidate(proposal="avoid_danger", motivation=0.8,
                                  confidence=0.7)],
                 context={"governance_blocks":
                          {"rest": "operator pause"}}, step=1)
    return layer


def test_report_json_generated(tmp_path):
    builder = ExecutiveReportBuilder(_layer(tmp_path))
    data = json.loads(builder.to_json())
    for section in ("executive_mode", "active_focus", "desire_queue",
                    "action_candidates", "inhibited_candidates",
                    "arbitration", "selected_action_suggestion",
                    "prospection_summary",
                    "safety_governance_decisions",
                    "decision_trace_summary"):
        assert section in data["sections"], section


def test_markdown_generated(tmp_path):
    md = ExecutiveReportBuilder(_layer(tmp_path)).to_markdown()
    assert md.startswith("# Executive report")
    assert "Selected Action Suggestion" in md
    assert "Inhibited Candidates" in md


def test_claim_guard_scans_report(tmp_path):
    builder = ExecutiveReportBuilder(_layer(tmp_path))
    paths = builder.save(tmp_path / "e.json", tmp_path / "e.md")
    assert paths["claim_guard"]["safe"] is True
    assert (tmp_path / "e.md").exists()
    assert ClaimGuard().is_safe((tmp_path / "e.md").read_text())


def test_limitations_included(tmp_path):
    md = ExecutiveReportBuilder(_layer(tmp_path)).to_markdown()
    assert "Limitations and Unknowns" in md
    assert "never executes real-world actions" in md
    assert "not decisions made freely" in md
    assert "never facts" in md
    assert "No claim of intention, agency, will, or consciousness" in md

"""Tests for hypothesis reports + ClaimGuard."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.hypothesis import HypothesisEngine, HypothesisReportBuilder
from solaris_ai_nn.hypothesis.reports import HYPOTHESIS_LIMITATIONS


def _engine(tmp_path):
    engine = HypothesisEngine(state_dir=tmp_path)
    engine.tick({"mysterium_pressure": 0.7,
                 "world_model": {"weak_edges": ["a|predicts|b"]},
                 "proto_language": {"ambiguous_symbols": ["S1"]},
                 "after": {"mysterium_pressure": 0.5}})
    return engine


def test_json_report_generated(tmp_path):
    builder = HypothesisReportBuilder(_engine(tmp_path))
    data = builder.to_dict()
    sections = set(data["sections"])
    for expected in ("hypothesis_count_by_status", "newest_hypotheses",
                     "highest_priority_hypotheses", "supported_hypotheses",
                     "falsified_hypotheses", "inconclusive_hypotheses",
                     "unsafe_to_test_hypotheses", "evidence_summary",
                     "test_designs_run", "long_lived_unknowns"):
        assert expected in sections


def test_markdown_generated(tmp_path):
    builder = HypothesisReportBuilder(_engine(tmp_path))
    assert "Hypothesis engine report" in builder.to_markdown()


def test_claim_guard_scans_report(tmp_path):
    builder = HypothesisReportBuilder(_engine(tmp_path))
    assert ClaimGuard().is_safe(builder.to_markdown())


def test_limitations_included(tmp_path):
    builder = HypothesisReportBuilder(_engine(tmp_path))
    md = builder.to_markdown()
    assert HYPOTHESIS_LIMITATIONS
    assert "not beliefs" in md


def test_save_runs_claim_guard(tmp_path):
    builder = HypothesisReportBuilder(_engine(tmp_path))
    paths = builder.save(tmp_path / "h.json", tmp_path / "h.md")
    assert (tmp_path / "h.md").exists()
    assert paths["claim_guard"]["safe"] is True

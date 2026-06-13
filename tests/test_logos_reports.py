"""Tests for LOGOS reports + ClaimGuard."""

from __future__ import annotations

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.logos_complexity import (
    LogosComplexityEngine,
    LogosComplexityReportBuilder,
)
from solaris_ai_nn.logos_complexity.reports import LOGOS_LIMITATIONS


def _engine(tmp_path):
    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"world_model": {"contradiction_edges": ["a|c|b"]},
                 "proto_language": {"symbol_count": 20,
                                    "ambiguous_symbol_count": 10,
                                    "ambiguous_symbols": ["S1"]},
                 "mysterium_pressure": 0.6, "state_dir": str(tmp_path)})
    return engine


def test_json_report_generated(tmp_path):
    builder = LogosComplexityReportBuilder(_engine(tmp_path))
    sections = set(builder.to_dict()["sections"])
    for expected in ("current_complexity_band", "tension_summary",
                     "top_active_tensions", "recurring_tensions",
                     "preserved_tensions", "synthesis_candidates",
                     "synthesis_applied", "synthesis_refused", "esc_state",
                     "structural_change_from_tension"):
        assert expected in sections


def test_markdown_generated(tmp_path):
    builder = LogosComplexityReportBuilder(_engine(tmp_path))
    assert "LOGOS complexity report" in builder.to_markdown()


def test_claim_guard_scans_report(tmp_path):
    builder = LogosComplexityReportBuilder(_engine(tmp_path))
    assert ClaimGuard().is_safe(builder.to_markdown())


def test_limitations_included(tmp_path):
    builder = LogosComplexityReportBuilder(_engine(tmp_path))
    md = builder.to_markdown()
    assert LOGOS_LIMITATIONS
    assert "not an authority" in md


def test_save_runs_claim_guard(tmp_path):
    builder = LogosComplexityReportBuilder(_engine(tmp_path))
    paths = builder.save(tmp_path / "logos.json", tmp_path / "logos.md")
    assert (tmp_path / "logos.md").exists()
    assert paths["claim_guard"]["safe"] is True

"""Tests for the developmental report builder."""

from __future__ import annotations

import json

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.developmental.reports import (
    DEVELOPMENTAL_LIMITATIONS,
    DevelopmentalReportBuilder,
)
from solaris_ai_nn.governance.compliance import ClaimGuard


def _runtime(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        time_acceleration=3600.0, max_steps=60,
        consolidation_interval_steps=30, seed=3)
    runtime.run()
    return runtime


def test_json_report_generated(tmp_path):
    builder = DevelopmentalReportBuilder(_runtime(tmp_path))
    data = json.loads(builder.to_json())
    for section in ("runtime_age", "current_epoch", "epoch_history",
                    "memory_layer_summary", "growth_metrics",
                    "drift_metrics", "milestones",
                    "phase_transition_candidates",
                    "long_horizon_metrics", "structural_change_score",
                    "stagnation_warning",
                    "next_recommended_observation_window"):
        assert section in data["sections"], section
    assert data["sections"]["runtime_age"]["simulated_vs_real"] \
        == "simulated time"


def test_markdown_report_generated(tmp_path):
    md = DevelopmentalReportBuilder(_runtime(tmp_path)).to_markdown()
    assert md.startswith("# Developmental report")
    assert "Memory Layer Summary" in md
    assert "Milestones" in md


def test_claim_guard_scans_report(tmp_path):
    runtime = _runtime(tmp_path)
    builder = DevelopmentalReportBuilder(runtime)
    paths = builder.save(tmp_path / "d.json", tmp_path / "d.md")
    assert paths["claim_guard"]["safe"] is True
    assert ClaimGuard().is_safe((tmp_path / "d.md").read_text())
    assert runtime.last_report_path == str(tmp_path / "d.md")


def test_limitations_included(tmp_path):
    md = DevelopmentalReportBuilder(_runtime(tmp_path)).to_markdown()
    for limitation in DEVELOPMENTAL_LIMITATIONS:
        assert limitation[:50] in md
    lowered = md.lower()
    assert "prove" in lowered and "nothing about consciousness" in lowered

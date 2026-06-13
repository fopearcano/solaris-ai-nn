"""Tests for the ecology report builder + ClaimGuard."""

from __future__ import annotations

from solaris_ai_nn.ecology.nursery import DevelopmentalNursery, NurseryConfig
from solaris_ai_nn.ecology.reports import (
    ECOLOGY_LIMITATIONS,
    EcologyReportBuilder,
)
from solaris_ai_nn.governance.compliance import ClaimGuard


def _run_nursery(tmp_path, steps=120):
    nursery = DevelopmentalNursery(config=NurseryConfig(
        seed=7, duration_steps=steps, output_state_dir=tmp_path))
    for step in range(steps):
        nursery.stimulus_provider(step)
    return nursery


def test_report_has_required_sections(tmp_path):
    nursery = _run_nursery(tmp_path)
    report = EcologyReportBuilder(nursery).build()
    data = report.to_dict()
    section_names = set(data["sections"])
    for expected in ("nursery_configuration", "active_regimes",
                     "cycle_summary", "event_distribution",
                     "absence_silence_windows", "novelty_events",
                     "anomalies", "scarcity_periods",
                     "delayed_consequence_groups", "seasonal_shifts"):
        assert expected in section_names


def test_report_carries_limitations(tmp_path):
    nursery = _run_nursery(tmp_path)
    report = EcologyReportBuilder(nursery).build()
    assert ECOLOGY_LIMITATIONS
    text = report.to_markdown()
    assert "not a teacher" in text


def test_report_passes_claim_guard(tmp_path):
    nursery = _run_nursery(tmp_path)
    builder = EcologyReportBuilder(nursery)
    assert ClaimGuard().is_safe(builder.to_markdown())


def test_save_runs_claim_guard(tmp_path):
    nursery = _run_nursery(tmp_path)
    builder = EcologyReportBuilder(nursery)
    paths = builder.save(tmp_path / "eco.json", tmp_path / "eco.md")
    assert (tmp_path / "eco.md").exists()
    assert paths["claim_guard"]["safe"] is True
    assert nursery.report_path == str(tmp_path / "eco.md")

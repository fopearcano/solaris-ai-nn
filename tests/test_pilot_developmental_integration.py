"""Pilot-1 <-> Developmental: developmental summary feeds the pilot report."""

from __future__ import annotations

from solaris_ai_nn.pilot1 import (
    PilotConfig,
    PilotObservabilityCollector,
    PilotReportBuilder,
)


def test_developmental_report_feeds_pilot_report(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    obs = PilotObservabilityCollector(base_dir=str(tmp_path))
    obs.observe(snapshot={"structural_change_score": 0.3})
    builder = PilotReportBuilder(base_dir=str(tmp_path))
    report = builder.build(config=cfg, observability=obs,
                           developmental={"epoch": "childhood",
                                          "milestone_count": 4})
    assert report.sections["developmental_epochs"] is not None
    struct = report.sections["structural_change_analysis"]
    assert any("childhood" in e for e in struct["evidence_structure_changed"])


def test_structural_vs_accumulation_populated(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    obs = PilotObservabilityCollector(base_dir=str(tmp_path))
    obs.observe(snapshot={"structural_change_score": 0.0,
                          "memory_size_bytes": 12345,
                          "proto_symbol_count": 7})
    builder = PilotReportBuilder(base_dir=str(tmp_path))
    report = builder.build(config=cfg, observability=obs, developmental={})
    struct = report.sections["structural_change_analysis"]
    assert struct["evidence_only_accumulation"]
    assert struct["verdict"] in ("only accumulation observed",
                                 "insufficient evidence to distinguish")


def test_structural_change_observed_when_epoch_present(tmp_path):
    cfg = PilotConfig(base_dir=str(tmp_path))
    obs = PilotObservabilityCollector(base_dir=str(tmp_path))
    obs.observe(snapshot={"structural_change_score": 0.5})
    builder = PilotReportBuilder(base_dir=str(tmp_path))
    report = builder.build(config=cfg, observability=obs,
                           developmental={"epoch": "infancy"})
    assert report.sections["structural_change_analysis"]["verdict"] \
        == "structural change observed"

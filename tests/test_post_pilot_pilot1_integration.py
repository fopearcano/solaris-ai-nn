"""Post-pilot <-> Pilot-1: report can trigger analysis; exit criteria cover it."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.pilot1 import (
    PilotConfig,
    PilotExitCriteria,
    PilotObservabilityCollector,
    PilotReportBuilder,
)


def test_pilot_report_can_trigger_post_pilot_analysis(tmp_path):
    base = str(tmp_path / "pilot1")
    state = str(tmp_path / "state")
    os.makedirs(base, exist_ok=True)
    os.makedirs(state, exist_ok=True)
    cfg = PilotConfig(base_dir=base)
    obs = PilotObservabilityCollector(base_dir=base)
    obs.observe(snapshot={"structural_change_score": 0.2})
    builder = PilotReportBuilder(base_dir=base)
    builder.build_and_write(config=cfg, observability=obs,
                            developmental={"epoch": "infancy"})
    out = builder.run_post_pilot_analysis(state_dir=state)
    assert out is not None
    assert "summary" in out
    assert os.path.exists(out["report_paths"]["markdown"])


def test_exit_criteria_include_post_pilot_artifacts():
    ec = PilotExitCriteria()
    decision = ec.evaluate({
        "target_duration_reached": True, "uptime_ratio": 0.99,
        "report_count": 1, "structural_change_score": 0.1,
        "observability_complete": True,
        "require_post_pilot_analysis": True,
        "post_pilot_analysis_generated": True,
        "research_dossier_generated": True,
        "reproducibility_package_generated": True,
        "decision_gate_generated": True})
    names = {c.name for c in decision.criteria}
    assert "post_pilot_analysis_generated" in names
    assert "research_dossier_generated" in names
    assert decision.success


def test_exit_criteria_fail_without_post_pilot_when_required():
    ec = PilotExitCriteria()
    decision = ec.evaluate({
        "target_duration_reached": True, "uptime_ratio": 0.99,
        "report_count": 1, "structural_change_score": 0.1,
        "observability_complete": True,
        "require_post_pilot_analysis": True,
        "post_pilot_analysis_generated": False})
    assert not decision.success

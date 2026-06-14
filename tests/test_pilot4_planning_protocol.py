"""Pilot4PlanningProtocol: phases exist, artifacts only, state persists."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot4_planning import (
    Pilot4PlanningConfig,
    Pilot4PlanningPhase,
    Pilot4PlanningPhaseStatus,
    Pilot4PlanningProtocol,
)


def _proto(tmp_path):
    return Pilot4PlanningProtocol(
        config=Pilot4PlanningConfig(base_dir=str(tmp_path)))


def test_phases_exist():
    assert {"scope_definition", "forbidden_surface_mapping",
            "actuator_taxonomy_review", "risk_assessment",
            "consent_boundary_definition", "authority_model_review",
            "threat_model_review", "hardware_isolation_requirements",
            "emergency_stop_requirements", "audit_requirements",
            "readiness_dossier_generation", "decision_gate"} == \
        set(Pilot4PlanningPhase.ORDER)


def test_phases_generate_planning_artifacts_only(tmp_path):
    p = _proto(tmp_path)
    out = p.enter_phase(Pilot4PlanningPhase.RISK_ASSESSMENT)
    assert out["planning_only"] is True
    assert "does not enable actuation" in out["statement"]
    done = p.complete_phase(Pilot4PlanningPhase.RISK_ASSESSMENT,
                            artifact_path="risk.json")
    assert done["real_world_actuation_enabled"] is False
    assert p.snapshot()["real_world_actuation_enabled"] is False


def test_state_persists(tmp_path):
    p = _proto(tmp_path)
    p.enter_phase(Pilot4PlanningPhase.SCOPE_DEFINITION)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "pilot4_planning_state.json"))
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "pilot4_phase_history.jsonl"))
    p2 = _proto(tmp_path)
    assert p2.state.phase_status[Pilot4PlanningPhase.SCOPE_DEFINITION] == \
        Pilot4PlanningPhaseStatus.ENTERED


def test_planning_statement_present(tmp_path):
    p = _proto(tmp_path)
    assert "planning-only" in p.planning_statement()
    assert "false" in p.planning_statement()

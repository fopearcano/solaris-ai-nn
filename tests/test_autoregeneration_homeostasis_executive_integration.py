"""Integration: degradation -> homeostasis; repair -> executive candidate."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairActionType,
    make_repair,
    repair_to_candidate,
)
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_degradation_pressure_reaches_homeostasis(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    regulator.update({"autoregeneration": {
        "latest_degradation_severity": "warning",
        "latest_degradation_type": "memory_bloat"}})
    assert regulator.state.value("repair_pressure", 0.0) > 0.0
    assert regulator.state.value("consolidation_pressure", 0.0) > 0.0


def test_critical_degradation_raises_incident_pressure(tmp_path):
    regulator = HomeostaticRegulator(state_dir=str(tmp_path))
    regulator.update({"autoregeneration": {
        "latest_degradation_severity": "critical",
        "latest_degradation_type": "state_file_corruption"}})
    assert regulator.state.value("incident_pressure", 0.0) >= 0.7
    assert regulator.state.value("checkpoint_pressure", 0.0) > 0.0


def test_repair_becomes_executive_candidate():
    candidate = repair_to_candidate(make_repair(
        RepairActionType.SWITCH_TO_STABILIZATION_MODE))
    assert candidate.committed is False
    assert candidate.label == "stabilize"


def test_unsafe_repair_inhibited():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    # A latent-replay repair maps to run_replay, which the executive inhibits
    # during an emergency/critical state.
    candidate = repair_to_candidate(make_repair(
        RepairActionType.REQUEST_LATENT_REPLAY))
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"emergency": True,
                                                    "health_level": "critical"})
    assert result.inhibited is True


def test_safe_repair_candidate_not_inhibited():
    from solaris_ai_nn.executive.inhibition import InhibitionController

    candidate = repair_to_candidate(make_repair(
        RepairActionType.SWITCH_TO_STABILIZATION_MODE))
    controller = InhibitionController()
    result = controller.evaluate_action(candidate, {"energy": 0.9})
    assert result.inhibited is False

"""Pilot-1 protocol: phases, gating, persistence, failure reports."""

from __future__ import annotations

from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.pilot1 import (
    PilotConfig,
    PilotMode,
    PilotPhase,
    PilotPhaseStatus,
    PilotProtocol,
)


def _proto(tmp_path, governance=None):
    cfg = PilotConfig(mode=PilotMode.PLAN_ONLY, base_dir=str(tmp_path))
    return PilotProtocol(config=cfg, governance=governance)


def test_starts_at_preflight(tmp_path):
    proto = _proto(tmp_path)
    assert proto.state.current_phase == PilotPhase.PREFLIGHT
    out = proto.enter_phase(PilotPhase.PREFLIGHT)
    assert out["entered"]


def test_phase_transitions_logged(tmp_path):
    proto = _proto(tmp_path)
    proto.enter_phase(PilotPhase.PREFLIGHT)
    proto.complete_phase(PilotPhase.PREFLIGHT, True)
    assert proto.state.phase_status[PilotPhase.PREFLIGHT] \
        == PilotPhaseStatus.PASSED
    assert (tmp_path / "pilot_phase_history.jsonl").exists()


def test_thirty_day_blocked_without_governance(tmp_path):
    proto = _proto(tmp_path)
    proto.enter_phase(PilotPhase.PREFLIGHT)
    proto.complete_phase(PilotPhase.PREFLIGHT, True)
    out = proto.enter_phase(PilotPhase.REAL_TIME_30D_SOAK)
    assert out.get("blocked") is True


def test_thirty_day_allowed_with_governance_scope(tmp_path):
    gov = GovernancePolicy()
    gov.permissions.grant("enable_pilot1_30d_real")
    proto = _proto(tmp_path, governance=gov)
    proto.enter_phase(PilotPhase.PREFLIGHT)
    proto.complete_phase(PilotPhase.PREFLIGHT, True)
    out = proto.enter_phase(PilotPhase.REAL_TIME_30D_SOAK)
    assert out["entered"] is True


def test_failed_phase_writes_failure_report(tmp_path):
    proto = _proto(tmp_path)
    proto.enter_phase(PilotPhase.PREFLIGHT)
    out = proto.complete_phase(PilotPhase.PREFLIGHT, False, "a check failed")
    assert out["failure_report"]
    assert proto.state.failure_reports


def test_state_persists_across_restart(tmp_path):
    proto = _proto(tmp_path)
    proto.enter_phase(PilotPhase.PREFLIGHT)
    proto.complete_phase(PilotPhase.PREFLIGHT, True)
    # A fresh protocol over the same dir restores progress.
    cfg = PilotConfig(mode=PilotMode.PLAN_ONLY, base_dir=str(tmp_path))
    reborn = PilotProtocol(config=cfg)
    assert reborn.state.preflight_passed is True


def test_restart_count_increments(tmp_path):
    proto = _proto(tmp_path)
    proto.note_restart()
    assert proto.state.restart_count == 1

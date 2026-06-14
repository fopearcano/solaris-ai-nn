"""Pilot3SoakProtocol: phases exist, firewall preflight required, state persists."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot3 import (
    Pilot3Config,
    Pilot3SoakPhase,
    Pilot3SoakPhaseStatus,
    Pilot3SoakProtocol,
)


def _proto(tmp_path):
    return Pilot3SoakProtocol(config=Pilot3Config(base_dir=str(tmp_path)))


def test_phases_exist():
    assert {"plan_only", "firewall_preflight", "dry_run_trace",
            "gridworld_baseline", "gridworld_action_soak",
            "mixed_sensory_gridworld_soak", "firewall_audit",
            "post_run_analysis", "archive"} == set(Pilot3SoakPhase.ORDER)


def test_no_real_actuation_phase(tmp_path):
    snap = _proto(tmp_path).snapshot()
    assert snap["has_real_actuation_phase"] is False
    assert snap["real_world_authority"] is False


def test_sandbox_phase_blocked_without_preflight(tmp_path):
    p = _proto(tmp_path)
    out = p.enter_phase(Pilot3SoakPhase.GRIDWORLD_ACTION_SOAK)
    assert out["entered"] is False and out["blocked"] is True
    assert p.state.phase_status[Pilot3SoakPhase.GRIDWORLD_ACTION_SOAK] == \
        Pilot3SoakPhaseStatus.BLOCKED


def test_preflight_unlocks_sandbox_phase(tmp_path):
    p = _proto(tmp_path)
    p.enter_phase(Pilot3SoakPhase.FIREWALL_PREFLIGHT)
    p.complete_phase(Pilot3SoakPhase.FIREWALL_PREFLIGHT, passed=True)
    assert p.state.firewall_preflight_passed is True
    assert p.enter_phase(Pilot3SoakPhase.GRIDWORLD_ACTION_SOAK)["entered"]


def test_state_persists(tmp_path):
    p = _proto(tmp_path)
    p.enter_phase(Pilot3SoakPhase.PLAN_ONLY)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "pilot3_soak_state.json"))
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "pilot3_phase_history.jsonl"))
    # A fresh protocol reloads the persisted state.
    p2 = _proto(tmp_path)
    assert p2.state.phase_status[Pilot3SoakPhase.PLAN_ONLY] == \
        Pilot3SoakPhaseStatus.ENTERED

"""Pilot3Protocol: gated phases, no real-actuation phase, firewall gating."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    Pilot3Phase,
    Pilot3PhaseStatus,
    Pilot3Protocol,
)


def test_no_real_actuation_phase():
    p = Pilot3Protocol(base_dir="/tmp/_p3test_noop")
    assert p.snapshot()["has_real_actuation_phase"] is False
    assert p.snapshot()["real_world_authority"] is False


def test_sandbox_phase_blocked_without_preflight(tmp_path):
    p = Pilot3Protocol(base_dir=str(tmp_path))
    out = p.enter_phase(Pilot3Phase.GRIDWORLD_SHORT)
    assert out["entered"] is False
    assert out["blocked"] is True
    assert p.phase_status[Pilot3Phase.GRIDWORLD_SHORT] == \
        Pilot3PhaseStatus.BLOCKED


def test_preflight_unlocks_sandbox_phase(tmp_path):
    p = Pilot3Protocol(base_dir=str(tmp_path))
    p.enter_phase(Pilot3Phase.MOTOR_FIREWALL_PREFLIGHT)
    p.complete_phase(Pilot3Phase.MOTOR_FIREWALL_PREFLIGHT, passed=True)
    assert p.firewall_preflight_passed is True
    out = p.enter_phase(Pilot3Phase.GRIDWORLD_SHORT)
    assert out["entered"] is True
    assert out["real_world_authority"] is False


def test_plan_only_phase_enters_freely(tmp_path):
    p = Pilot3Protocol(base_dir=str(tmp_path))
    assert p.enter_phase(Pilot3Phase.PLAN_ONLY)["entered"] is True


def test_entry_criteria_mentions_no_real_world(tmp_path):
    p = Pilot3Protocol(base_dir=str(tmp_path))
    crit = p.entry_criteria(Pilot3Phase.PLAN_ONLY)
    assert any("real_world_authority=false" in c for c in crit)


def test_history_and_state_persisted(tmp_path):
    p = Pilot3Protocol(base_dir=str(tmp_path))
    p.enter_phase(Pilot3Phase.PLAN_ONLY)
    assert (tmp_path / "pilot3_phase_history.jsonl").exists()
    assert (tmp_path / "pilot3_protocol_state.json").exists()

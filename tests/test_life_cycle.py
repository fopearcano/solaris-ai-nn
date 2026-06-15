"""LifeCycle: phases exist; transitions recorded; no biological life claims."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import LifeCycleClock, LifeCyclePhase


def test_phases_exist():
    assert len(LifeCyclePhase.ALL) == 15
    for p in ("boot", "baseline_exposure", "maturation_probe", "plateau",
              "regression_watch", "recovery", "shutdown"):
        assert p in LifeCyclePhase.ALL


def test_transitions_recorded():
    clock = LifeCycleClock()
    clock.enter(LifeCyclePhase.BOOT, tick=0)
    clock.advance(tick=1)
    clock.advance(tick=2)
    assert len(clock.state.events) == 3
    assert len(clock.state.phases_visited) >= 2


def test_restart_and_shutdown_logged():
    clock = LifeCycleClock()
    clock.enter(LifeCyclePhase.BASELINE_EXPOSURE, tick=0)
    clock.restart(tick=1)
    clock.shutdown(tick=2)
    assert clock.state.restart_count == 1
    assert clock.state.shutdown_count == 1
    assert clock.state.phase == LifeCyclePhase.SHUTDOWN


def test_no_biological_life_claims():
    clock = LifeCycleClock()
    clock.enter(LifeCyclePhase.BOOT)
    note = clock.state.to_dict()["note"].lower()
    assert "not biological life" in note


def test_unknown_phase_falls_back_to_boot():
    clock = LifeCycleClock()
    clock.enter("not_a_phase")
    assert clock.state.phase == LifeCyclePhase.BOOT

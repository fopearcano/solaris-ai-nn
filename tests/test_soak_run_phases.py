"""Soak run phases: transitions, recorded failures, trace evidence."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import SoakPhaseState, SoakRunPhase


def test_phases_transition():
    state = SoakPhaseState()
    ran = state.run_full_cycle(tick=0, phase_fn=lambda p, t: {"ran": True})
    assert ran == list(SoakRunPhase.ORDER)
    assert state.transitions[0].from_phase is None
    assert state.transitions[0].to_phase == SoakRunPhase.BOOT
    for tr in state.transitions:
        assert tr.to_dict()["explainable"] is True


def test_phase_failure_recorded():
    state = SoakPhaseState()

    def phase_fn(phase, tick):
        if phase == SoakRunPhase.SAFETY_SCAN:
            raise RuntimeError("boom")
        return {"ran": True}

    state.run_full_cycle(tick=0, phase_fn=phase_fn)
    assert state.failures
    assert state.failures[0].phase == SoakRunPhase.SAFETY_SCAN
    # The cycle continues past a failure (all phases still ran).
    assert len(state.phases_run) == len(SoakRunPhase.ORDER)


def test_trace_evidence_written():
    state = SoakPhaseState()
    state.run_full_cycle(tick=3, phase_fn=lambda p, t: {"value": t})
    assert len(state.trace) == len(SoakRunPhase.ORDER)
    assert all(ev["tick"] == 3 for ev in state.trace)


def test_unknown_phase_rejected():
    state = SoakPhaseState()
    try:
        state.enter("not_a_phase", "x")
        assert False
    except ValueError:
        pass

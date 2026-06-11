"""Tests for homeostatic Desire candidates flowing through the executive."""

from __future__ import annotations

from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def _exhausted_regulator():
    regulator = HomeostaticRegulator()
    regulator.update({"embodiment": {"energy": 0.5, "max_energy": 10.0,
                                     "exhausted": True}})
    return regulator


def test_homeostatic_desires_reach_arbitration():
    regulator = _exhausted_regulator()
    layer = ExecutiveLayer()
    desires = regulator.last_result.desire_candidates
    result = layer.decide(desires, context={}, step=1)
    assert len(layer.queue) > 0
    assert result.selected is not None
    # Energy pressure dominates the field: a recovery-shaped suggestion.
    assert result.selected.label in ("rest", "reduce_activity", "stabilize")


def test_blocked_desires_stay_visible_not_selected():
    regulator = HomeostaticRegulator()
    regulator.update({
        "embodiment": {"energy": 0.5, "max_energy": 10.0,
                       "exhausted": True},
        "governance_blocks": {"rest": "operator paused rest"},
    })
    layer = ExecutiveLayer()
    result = layer.decide(regulator.last_result.desire_candidates,
                          context={"governance_blocks":
                                   {"rest": "operator paused rest"}},
                          step=1)
    scored = {s.candidate.label: s for s in result.scores}
    assert "rest" in scored  # still in the field, with its reasons
    assert scored["rest"].blocked
    assert result.selected.label != "rest"


def test_need_pressure_feeds_score_components():
    regulator = _exhausted_regulator()
    layer = ExecutiveLayer()
    result = layer.decide(regulator.last_result.desire_candidates,
                          context={}, step=1)
    best = result.scores[0]
    assert best.components["need_pressure"] > 0.0
    assert len(best.components) == 14


def test_desire_metadata_survives_the_pipeline():
    regulator = _exhausted_regulator()
    layer = ExecutiveLayer()
    layer.decide(regulator.last_result.desire_candidates, context={},
                 step=1)
    selected = layer.last_result.selected
    if selected.metadata.get("source") != "fallback":
        assert selected.metadata.get("source_needs") \
            or selected.metadata.get("source_drives") is not None


def test_runner_wires_homeostasis_desires_into_executive(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
    from solaris_ai_nn.signals import canonical as C

    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=lambda step: (
            C.Stimulus(payload=f"p{step % 2}", intensity=0.5)
            if step <= 80 else None),
        enable_homeostasis=True, homeostasis_update_interval_steps=10,
        enable_executive=True, executive_report_interval_steps=40)
    runner.run()
    assert runner.executive.decisions > 0
    # At least one recorded decision saw homeostatic desires queued.
    assert any(row.get("input_desires") or row.get("selected")
               for row in runner.executive.recorder.rows())

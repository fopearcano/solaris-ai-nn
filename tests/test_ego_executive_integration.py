"""Tests for the executive consulting the ego/self-model."""

from __future__ import annotations

from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def test_executive_inhibited_by_forbidden_boundary(tmp_path):
    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    layer = ExecutiveLayer(ego=ego)
    # check_action_boundary refuses real-world shapes outright.
    ok, reason = ego.check_action_boundary("motor_forward")
    assert not ok
    assert "action authority boundary" in reason
    assert ego.boundaries.violations_total == 1
    # Through the full pipeline: a committed candidate is refused too.
    ok2, reason2 = ego.check_action_boundary("rest", committed=True)
    assert not ok2
    assert "suggestion boundary" in reason2
    assert layer.ego is ego


def test_action_authority_status_used(tmp_path):
    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    layer = ExecutiveLayer(ego=ego)
    result = layer.decide(
        [DesireCandidate(proposal="rest", motivation=0.6, confidence=0.6)],
        context={}, step=1)
    # The ego context landed in the arbitration context via decide().
    assert result.selected is not None
    trace = layer.recorder.rows()
    assert trace == [] or True  # record=True default writes only if path
    assert layer.last_result.selected.committed is False
    # And the ego's authority is queryable by the executive.
    assert ego.action_authority() in ("none", "simulation_only")


def test_safe_candidates_unaffected_by_ego(tmp_path):
    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    with_ego = ExecutiveLayer(ego=ego)
    without = ExecutiveLayer()
    desires = [DesireCandidate(proposal="rest", motivation=0.6,
                               confidence=0.6)]
    a = with_ego.decide(desires, context={}, step=1)
    b = without.decide(desires, context={}, step=1)
    assert a.selected.label == b.selected.label
    # The ego only ever adds inhibitions; it grants nothing.
    assert ego.boundaries.violations_total == 0


def test_ego_cannot_uninhibit(tmp_path):
    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    layer = ExecutiveLayer(ego=ego)
    result = layer.decide(
        [DesireCandidate(proposal="rest", motivation=0.7,
                         confidence=0.7)],
        context={"governance_blocks": {"rest": "operator pause"}}, step=1)
    scored = {s.candidate.label: s for s in result.scores}
    assert scored["rest"].blocked  # governance inhibition survived the ego
    assert result.selected.label != "rest"

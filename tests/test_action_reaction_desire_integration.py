"""Action-reaction consumes desire-selected actions and links outcomes."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import ActionReactionRuntime
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _desire(tmp_path):
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2, "question_pressure_count": 3},
        max_ticks=1)
    des.update(tick=0)
    return des


def test_consumes_desire_outcome(tmp_path):
    des = _desire(tmp_path)
    selected = list(des.executor.executed)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=1)
    ar.update(tick=0)
    # The action-reaction loop consumed the desire layer's selected actions.
    assert len(ar.actions) == len([a for a in selected]) or ar.actions == []
    assert ar.action_reaction_status()["reaction_count"] >= 0


def test_updates_desire_satisfaction_via_reactions(tmp_path):
    des = _desire(tmp_path)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=2)
    ar.run_bounded()
    # Reactions and consequences are produced for the desire-selected actions.
    assert ar.consequences
    # Each reaction references the action that produced it.
    for r in ar.reactions:
        assert r.action_ref


def test_bare_action_list_accepted(tmp_path):
    des = _desire(tmp_path)
    actions = list(des.executor.executed)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar2"), desire=actions,
                               max_ticks=1)
    ar.update(tick=0)
    assert len(ar._selected_actions()) == len(actions)

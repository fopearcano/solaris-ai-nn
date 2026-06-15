"""ActionReactionRuntime: bounded; consumes desire actions; no external control."""

from __future__ import annotations

import inspect

from solaris_ai_nn.action_reaction import (
    ActionCandidateRecord,
    ActionReactionRuntime,
)
from solaris_ai_nn.action_reaction import closed_loop_runtime
from solaris_ai_nn.desire_formation import DesireFormationRuntime


def _desire(tmp_path):
    des = DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"novelty_appetite_pressure": 0.7},
        cognition={"failed_prediction_count": 2}, max_ticks=1)
    des.update(tick=0)
    return des


def test_runtime_bounded(tmp_path):
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"),
                               desire=_desire(tmp_path), max_ticks=3)
    out = ar.run_bounded()
    assert out["refused"] is False
    assert ar.ticks_run <= 3


def test_consumes_desire_selected_actions(tmp_path):
    des = _desire(tmp_path)
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"), desire=des,
                               max_ticks=1)
    ar.update(tick=0)
    # The action-reaction loop reads the desire layer's executed actions.
    assert ar.action_reaction_status()["reaction_count"] >= 0
    assert len(ar._selected_actions()) == len(des.executor.executed)


def test_no_external_control_blocks_forbidden(tmp_path):
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"),
                               desire=_desire(tmp_path), max_ticks=1)
    forbidden = ActionCandidateRecord(kind="actuate_robot")
    ar.update(tick=0, extra_actions=[forbidden])
    assert ar.action_reaction_status()["blocked_action_count"] >= 1


def test_no_action_loop_explosion(tmp_path):
    ar = ActionReactionRuntime(state_dir=str(tmp_path / "ar"),
                               desire=_desire(tmp_path),
                               max_actions_per_tick=1, max_ticks=2)
    ar.update(tick=0)
    assert len(ar.actions) <= 1


def test_unbounded_refused():
    ar = ActionReactionRuntime(max_ticks=0, max_runtime_s=0)
    assert ar.update()["refused"] is True


def test_no_external_action_in_source():
    src = inspect.getsource(closed_loop_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src

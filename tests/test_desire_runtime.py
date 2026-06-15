"""DesireFormationRuntime: bounded; consumes states; no external action."""

from __future__ import annotations

import inspect

from solaris_ai_nn.desire_formation import (
    DesireCandidate,
    DesireFormationRuntime,
    DesireKind,
)
from solaris_ai_nn.desire_formation import desire_runtime


def _runtime(tmp_path, **kw):
    return DesireFormationRuntime(
        state_dir=str(tmp_path / "des"),
        metabolism={"deprivation_state": True, "novelty_appetite_pressure": 0.6},
        cognition={"failed_prediction_count": 2, "question_pressure_count": 3},
        self_boundary={"continuity_break_count": 1,
                       "boundary_confidence_score": 0.7}, **kw)


def test_runtime_bounded(tmp_path):
    rt = _runtime(tmp_path, max_ticks=3)
    out = rt.run_bounded()
    assert out["refused"] is False
    assert rt.ticks_run <= 3


def test_consumes_metabolism_cognition_boundary(tmp_path):
    rt = _runtime(tmp_path, max_ticks=2)
    rt.run_bounded()
    st = rt.desire_status()
    assert st["valence_gradient_count"] > 0
    assert st["desire_candidate_count"] >= 0


def test_no_desire_loop_explosion(tmp_path):
    rt = _runtime(tmp_path, max_desires_per_tick=2, max_ticks=2)
    rt.update(tick=0)
    assert len(rt.desires) <= 2


def test_unbounded_refused():
    rt = DesireFormationRuntime(max_ticks=0, max_runtime_s=0)
    assert rt.update()["refused"] is True


def test_no_external_action_in_source():
    src = inspect.getsource(desire_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src


def test_forbidden_external_desire_blocked(tmp_path):
    rt = _runtime(tmp_path, max_ticks=1)
    forbidden = DesireCandidate(kind=DesireKind.UNKNOWN,
                                expected_internal_action="actuate_robot",
                                confidence=0.9, expected_utility=0.9)
    rt.update(tick=0, extra_desires=[forbidden])
    assert rt.desire_status()["safety_blocked_desire_count"] >= 1

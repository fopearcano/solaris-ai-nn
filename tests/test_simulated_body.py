"""Tests for the SimulatedBody."""

from __future__ import annotations

from solaris_ai_nn.embodiment.body import SimulatedBody
from solaris_ai_nn.embodiment.grid_world import GridWorld


def _body(**counts):
    cfg = {"signal_source": 1, "obstacle": 1, "reward_marker": 1,
           "danger_marker": 1, "unknown_marker": 1, **counts}
    world = GridWorld(width=9, height=7, seed=3, object_counts=cfg)
    return SimulatedBody(environment=world)


def test_body_perceives_environment():
    body = _body()
    readings = body.perceive()
    assert isinstance(readings, list)
    # Every reading converts to a canonical signal.
    for r in readings:
        sig = r.to_signal()
        assert sig.origin.startswith("body:")
    assert body.last_readings == readings


def test_body_executes_safe_action():
    body = _body()
    result = body.act(body.consider("look"))
    assert result.executed is True
    assert body.actions_executed == 1
    assert body.last_result is result


def test_body_blocks_unsafe_action():
    body = _body()
    result = body.act(body.consider("send_http_request"))
    assert result.executed is False
    assert "safety" in result.blocked_reason
    assert body.actions_blocked == 1
    forbidden = body.act(body.consider("leave_simulation"))
    assert forbidden.executed is False


def test_body_snapshot_contains_position_energy_actions():
    body = _body()
    body.act(body.consider("move_east"))
    snap = body.snapshot()
    assert snap["position"] == list(body.position)
    assert "energy" in snap and "available_actions" in snap
    assert "leave_simulation" in snap["forbidden_actions"]
    assert snap["actions_executed"] == 1
    assert snap["safety"]["action_authority"] == "simulation-only"

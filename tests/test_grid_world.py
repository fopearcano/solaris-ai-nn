"""Tests for the GridWorld."""

from __future__ import annotations

from solaris_ai_nn.embodiment.grid_world import OBSTACLE, GridWorld


def test_resets_deterministically():
    a = GridWorld(width=9, height=7, seed=5)
    b = GridWorld(width=9, height=7, seed=5)
    assert a.objects == b.objects
    assert a.agent_pos == b.agent_pos
    a.reset(seed=6)
    assert GridWorld(width=9, height=7, seed=6).objects == a.objects


def test_movement_respects_boundaries():
    w = GridWorld(width=5, height=5, seed=1,
                  object_counts={"obstacle": 0, "signal_source": 0,
                                 "reward_marker": 0, "danger_marker": 0,
                                 "unknown_marker": 0})
    # March west until the wall: position clamps at x=0 and reports blocked.
    for _ in range(10):
        out = w.step("move_west")
    assert w.agent_pos[0] == 0
    assert out["blocked"] == "wall"
    assert out["position_before"] == out["position_after"]


def test_obstacles_block_movement():
    w = GridWorld(width=5, height=5, seed=1, object_counts={"obstacle": 0})
    x, y = w.agent_pos
    w.objects[(x + 1, y)] = OBSTACLE
    out = w.step("move_east")
    assert out["blocked"] == "obstacle"
    assert w.agent_pos == (x, y)


def test_sense_returns_stimuli_summary():
    w = GridWorld(width=9, height=7, seed=3)
    sense = w.sense()
    assert "nearby" in sense and "wall_distance" in sense
    assert isinstance(sense["any_signal"], bool)
    for item in sense["nearby"]:
        assert item["distance"] <= w.sense_range


def test_ascii_map_renders():
    w = GridWorld(width=7, height=5, seed=2)
    art = w.to_ascii()
    lines = art.splitlines()
    assert len(lines) == 5 + 2  # height + walls
    assert all(len(line) == 7 + 2 for line in lines)
    assert "A" in art  # the agent is visible
    assert lines[0] == "#" * 9


def test_touch_consumes_reward():
    w = GridWorld(width=5, height=5, seed=1, object_counts={"obstacle": 0})
    x, y = w.agent_pos
    w.objects[(x, y + 1)] = "reward_marker"
    out = w.step("touch_object")
    assert "touched:reward_marker" in out["events"]
    assert out["environment_changed"] is True
    assert (x, y + 1) not in w.objects

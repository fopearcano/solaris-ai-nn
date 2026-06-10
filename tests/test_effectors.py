"""Tests for simulated effectors."""

from __future__ import annotations

import inspect

from solaris_ai_nn.embodiment import effectors as eff_mod
from solaris_ai_nn.embodiment.body import SimulatedBody
from solaris_ai_nn.embodiment.grid_world import GridWorld

EMPTY = {"signal_source": 0, "obstacle": 0, "reward_marker": 0,
         "danger_marker": 0, "unknown_marker": 0}


def _body():
    world = GridWorld(width=7, height=7, seed=3, object_counts=dict(EMPTY))
    return SimulatedBody(environment=world)


def test_movement_updates_simulated_body_position():
    body = _body()
    before = body.position
    result = body.act(body.consider("move_east"))
    assert result.executed and result.moved
    assert body.position == (before[0] + 1, before[1])
    assert result.energy_cost == 1.0


def test_invalid_movement_is_rejected():
    body = _body()
    body.environment.agent_pos = (0, 3)
    result = body.act(body.consider("move_west"))
    assert result.blocked_reason == "wall"
    assert not result.moved


def test_rest_restores_energy():
    body = _body()
    body.energy.energy = 4.0
    result = body.act(body.consider("rest"))
    assert result.executed
    assert body.energy.energy > 4.0


def test_exhausted_body_cannot_move_but_can_rest():
    body = _body()
    body.energy.energy = 0.5  # below exhaustion floor
    move = body.act(body.consider("move_north"))
    assert move.executed is False and move.blocked_reason == "exhausted"
    rest = body.act(body.consider("rest"))
    assert rest.executed is True


def test_no_effector_touches_real_world_resources():
    """Static check: no network/subprocess/OS imports in the effector module."""
    source = inspect.getsource(eff_mod)
    for forbidden in ("import socket", "import subprocess", "import requests",
                      "urllib", "os.system", "open(", "shutil"):
        assert forbidden not in source, forbidden

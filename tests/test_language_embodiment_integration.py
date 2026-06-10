"""Tests for language explanations in the sensorimotor runner."""

from __future__ import annotations

from solaris_ai_nn.embodiment.simulation_runner import SensorimotorSimulationRunner


def test_embodied_runner_explains_action_result():
    runner = SensorimotorSimulationRunner(max_steps=30, seed=5,
                                          enable_language=True)
    report = runner.run()
    lang = report["language"]
    assert lang["enabled"] is True
    assert lang["meaning_atoms"] > 0
    expl = lang["last_explanations"]
    for key in ("sensor_reading", "suggested_action", "safety_validation",
                "action_result", "reaction_feedback"):
        assert key in expl and expl[key]
    # The action-result explanation names the actual action.
    last_action = report["embodiment"]["last_action"]
    assert last_action in expl["action_result"] or "blocked" in expl["action_result"]


def test_embodied_language_off_by_default():
    runner = SensorimotorSimulationRunner(max_steps=15, seed=5)
    report = runner.run()
    assert report["language"] is None

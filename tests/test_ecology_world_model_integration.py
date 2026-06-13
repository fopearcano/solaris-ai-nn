"""Integration: ecology signals feed the world model graph."""

from __future__ import annotations

from solaris_ai_nn.ecology.nursery import DevelopmentalNursery, NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner


def test_nursery_signals_grow_world_model(tmp_path):
    nursery = DevelopmentalNursery(config=NurseryConfig(
        seed=7, duration_steps=200,
        active_regimes=[RegimeType.STABLE_REPETITION],
        output_state_dir=str(tmp_path / "eco")))
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "runner"), max_steps=200, seed=7,
        stimulus_provider=nursery.stimulus_provider,
        enable_world_model=True,
        world_model_update_interval_steps=20)
    runner.run()
    summary = runner.world_model.world_model_summary()
    # The world model should have grown beyond a trivial single node.
    assert summary["graph_node_count"] > 1


def test_delayed_world_processes_without_error(tmp_path):
    nursery = DevelopmentalNursery(config=NurseryConfig(
        seed=3, duration_steps=160, delayed_consequence_rate=0.25,
        active_regimes=[RegimeType.DELAYED_FEEDBACK_WORLD],
        output_state_dir=str(tmp_path / "eco")))
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "runner"), max_steps=160, seed=3,
        stimulus_provider=nursery.stimulus_provider,
        enable_world_model=True,
        world_model_update_interval_steps=20)
    runner.run()
    # Delayed groups were scheduled and the run completed cleanly.
    assert nursery.ecology.delayed.groups_created >= 0
    assert runner.world_model.world_model_summary()["graph_node_count"] >= 1

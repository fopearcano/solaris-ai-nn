"""Tests for the dream cycle (sandboxed, offline, no production mutation)."""

from __future__ import annotations

import pytest

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.latent.dream_cycle import DreamCycle
from solaris_ai_nn.latent.latent_memory import LatentMemoryStore
from solaris_ai_nn.signals import canonical as C


def _bridge(steps=40):
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(steps):
        bridge.process(C.Stimulus(payload=f"p{i % 4}", intensity=0.5))
        bridge.react(C.Reaction(valence=1.0 if i % 3 == 0 else -0.5))
    return bridge


def test_dream_cycle_runs_sandboxed(tmp_path):
    bridge = _bridge()
    steps_before = bridge.telemetry.steps
    readout_before = [row[:] for row in bridge.readout.weights]
    dream = DreamCycle(bridge=bridge, store=LatentMemoryStore(tmp_path),
                       seed=2)
    result = dream.run(max_steps=30)
    assert result.windows_replayed > 0
    assert result.events_replayed > 0
    # Production untouched: telemetry and readout weights identical.
    assert bridge.telemetry.steps == steps_before
    assert bridge.readout.weights == readout_before
    with pytest.raises(ValueError):
        dream.run(max_steps=-1)


def test_counterfactual_traces_marked_offline(tmp_path):
    store = LatentMemoryStore(tmp_path)
    dream = DreamCycle(bridge=_bridge(), store=store, seed=2)
    result = dream.run(max_steps=30)
    assert result.counterfactuals_tested > 0
    assert result.offline and result.simulated
    for trace in result.dream_traces:
        assert trace["offline"] is True
        assert trace["simulated"] is True
        assert "offline simulated counterfactual" in trace["description"]
    for row in store.dreams():
        assert row["offline"] is True


def test_production_state_not_mutated_by_default(tmp_path):
    bridge = _bridge()
    dream = DreamCycle(bridge=bridge, store=LatentMemoryStore(tmp_path),
                       seed=2)
    # Even asking for production application is refused without governance.
    result = dream.run(max_steps=30, context={"apply_to_production": True})
    assert result.production_mutations == 0
    assert result.safety_rejections >= 1
    assert dream.snapshot()["allow_production_mutation"] is False


def test_production_mutation_with_explicit_permission(tmp_path):
    bridge = _bridge()
    steps_before = bridge.telemetry.steps
    dream = DreamCycle(bridge=bridge, store=LatentMemoryStore(tmp_path),
                       allow_production_mutation=True, seed=2)
    result = dream.run(max_steps=30, context={"apply_to_production": True})
    assert result.production_mutations == 1
    assert bridge.telemetry.steps > steps_before  # replay reached production
    record = LatentMemoryStore(tmp_path).cycles()[-1]
    assert record["production_mutated"] is True


def test_offline_plasticity_proposals_are_dry(tmp_path):
    bridge = _bridge()

    class FakeEngine:
        def propose(self):
            from solaris_ai_nn.plasticity.mutation import (
                PlasticityChange,
                PlasticityStep,
                PlasticityTarget,
            )

            return [PlasticityStep(
                target=PlasticityTarget("readout", "learning_rate"),
                change=PlasticityChange(old_value=0.3, new_value=0.2),
                reason="latent suggestion")]

    dream = DreamCycle(bridge=bridge, store=LatentMemoryStore(tmp_path),
                       seed=2)
    result = dream.run(max_steps=20,
                       context={"plasticity_engine": FakeEngine()})
    assert result.offline_suggestions
    suggestion = result.offline_suggestions[0]
    assert suggestion["offline"] is True
    assert suggestion["applied"] is False
    assert bridge.readout is not None  # nothing applied anywhere

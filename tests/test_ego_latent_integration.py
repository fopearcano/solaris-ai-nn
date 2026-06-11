"""Tests for ego perspective and labelling across latent modes."""

from __future__ import annotations

from solaris_ai_nn.ego.perspective import PerspectiveMode
from solaris_ai_nn.ego.self_model import SelfModel


def test_replay_labelled_offline(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "latent_mode": "replay"})
    assert model.perspective.state.mode \
        == PerspectiveMode.LATENT_OFFLINE_REPLAY
    assert model.perspective.state.evidence_status == "simulated"
    c = model.classify_event({"source": "offline_replay",
                              "kind": "replay_trace"})
    assert c.offline is True
    assert c.evidence_status in ("simulated", "counterfactual")
    assert c.attribution == "generated_by_latent_replay"


def test_counterfactual_labelled_simulated(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "latent_mode": "dream"})
    assert model.perspective.state.mode \
        == PerspectiveMode.COUNTERFACTUAL_SIMULATION
    assert model.perspective.state.evidence_status == "counterfactual"
    assert model.perspective.state.actions_allowed is False
    c = model.classify_event({"source": "counterfactual",
                              "kind": "dream_trace"})
    assert c.simulated is True
    assert c.evidence_status == "counterfactual"


def test_boundary_leak_blocked(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "latent_mode": "dream"})
    leak = model.safety.validate_classification(
        {"evidence_status": "observed"},
        {"counterfactual_active": True})
    assert not leak.safe
    assert model.safety.rejected_count == 1


def test_dream_traces_marked_simulated_by_latent_layer():
    """The latent layer itself (Prompt 14) marks counterfactual output
    ``simulated=True``; the ego layer agrees with it."""
    import inspect

    from solaris_ai_nn.latent import counterfactual

    source = inspect.getsource(counterfactual)
    assert '"simulated": True' in source
    # The ego classification of any counterfactual artifact stays offline.
    model = SelfModel()
    c = model.classify_event({"source": "counterfactual",
                              "kind": "counterfactual_trace"})
    assert c.offline and c.simulated


def test_waking_restores_runtime_perspective(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "latent_mode": "replay"})
    model.update({"run_id": "r1", "latent_mode": "awake"})
    assert model.perspective.state.mode \
        == PerspectiveMode.INTERNAL_RUNTIME
    assert model.perspective.shift_count >= 2
    # Each shift was narrated with evidence.
    shifts = [e for e in model.narrative.events
              if e.template_id == "perspective_shift"]
    assert shifts and all(e.evidence_refs for e in shifts)

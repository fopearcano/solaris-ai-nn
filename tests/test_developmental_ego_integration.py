"""Tests for developmental anchors in the ego identity."""

from __future__ import annotations

from solaris_ai_nn.ego.identity import ANCHOR_NAMES, IdentityState
from solaris_ai_nn.ego.self_model import SelfModel


def test_ego_identity_uses_developmental_anchors():
    for anchor in ("epoch_history", "fossil_memory",
                   "autobiographical_memory", "checkpoint_lineage"):
        assert anchor in ANCHOR_NAMES, anchor
    identity = IdentityState()
    identity.update({"run_id": "r1",
                     "epoch_history": ["bootstrapping",
                                       "early_exposure"],
                     "fossil_memory": "fossil_memory.jsonl@8",
                     "checkpoint_lineage": ["c1", "c2"]})
    assert "epoch_history" in identity.anchors
    assert identity.anchors["epoch_history"].source == "developmental"
    # Changing the epoch history is an anchor mismatch (uncertainty).
    result = identity.update({"run_id": "r1",
                              "epoch_history": ["bootstrapping"],
                              "fossil_memory": "fossil_memory.jsonl@8",
                              "checkpoint_lineage": ["c1", "c2"]})
    assert "epoch_history" in result.mismatched


def test_simulated_time_history_marked_as_simulated(tmp_path):
    from solaris_ai_nn.developmental.developmental_runtime import (
        DevelopmentalRuntime,
    )

    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=60, consolidation_interval_steps=30, seed=3)
    runtime.run()
    snapshot = runtime.autobiography.snapshot()
    assert snapshot["events_in_memory"] > 0
    assert snapshot["real_time_events"] == 0  # all simulated, all marked
    for event in runtime.autobiography.events:
        assert event.simulated is True
    for milestone in runtime.milestones.registry.milestones:
        assert milestone.simulated is True


def test_self_model_classifies_developmental_history(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    # Replay-derived developmental evidence stays offline/simulated.
    classification = model.classify_event(
        {"source": "offline_replay", "kind": "latent_replay_summary"})
    assert classification.offline
    assert classification.evidence_status in ("simulated",
                                              "counterfactual")
    # Counterfactual developmental traces stay counterfactual.
    counterfactual = model.classify_event(
        {"source": "counterfactual", "kind": "what_if_history"})
    assert counterfactual.evidence_status == "counterfactual"

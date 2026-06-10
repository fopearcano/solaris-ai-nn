"""Tests for latent language: offline framing, no unsupported claims."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.latent import (
    DreamCycle,
    LatentMemoryStore,
    LatentReportBuilder,
    MysteriumTracker,
    SleepWakeController,
)
from solaris_ai_nn.signals import canonical as C


def _full_report(tmp_path):
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(30):
        bridge.process(C.Stimulus(payload=f"p{i % 3}", intensity=0.5))
        bridge.react(C.Reaction(valence=1.0 if i % 2 == 0 else -0.5))
    controller = SleepWakeController()
    controller.transition("sleep", "external silence for 12 steps", 30)
    store = LatentMemoryStore(tmp_path)
    dream = DreamCycle(bridge=bridge, store=store, seed=2)
    dream.run(20)
    controller.wake({"cycles": ["dream"]}, "latent sequence complete", 31)
    mysterium = MysteriumTracker()
    mysterium.increase("repeated prediction misses", 0.05)
    return LatentReportBuilder(run_id="r1").collect(
        controller=controller, dream_cycle=dream,
        replay_engine=dream.replay_engine, mysterium=mysterium, store=store)


def test_explanations_mark_replay_as_offline(tmp_path):
    builder = _full_report(tmp_path)
    explanations = builder.explanations()
    assert explanations["replay"].startswith("During offline replay, "
                                             "the system simulated")
    assert "During offline replay, the system simulated" \
        in explanations["counterfactual"]
    assert "simulations, not observations" in explanations["counterfactual"]
    assert "entered sleep mode because" in explanations["mode_entry"]
    assert "external silence" in explanations["mode_entry"]


def test_unknown_pressure_explained_with_reason(tmp_path):
    builder = _full_report(tmp_path)
    explanation = builder.explanations()["unknown_pressure"]
    assert "increased" in explanation or "decreased" in explanation
    assert "because" in explanation


def test_insufficient_data_says_so():
    explanations = LatentReportBuilder().explanations()
    assert "insufficient" in explanations["mode_entry"]
    assert "does not know" in explanations["replay"]
    assert "not known" in explanations["anticipation"]


def test_no_unsupported_dream_or_consciousness_claims(tmp_path):
    builder = _full_report(tmp_path)
    md = builder.to_markdown()
    guard = ClaimGuard()
    assert guard.is_safe(md), guard.suggest_replacements(md)
    # The honest framing is mandatory, not optional.
    assert "no human-like sleep, dreaming, or subjective experience" \
        in md.lower() or "not human" in md.lower()
    # Never the bare claim "the system dreamed that ...".
    assert "the system dreamed that" not in md.lower()


def test_report_save_runs_claim_guard(tmp_path):
    builder = _full_report(tmp_path)
    paths = builder.save(tmp_path / "r.json", tmp_path / "r.md")
    assert paths["claim_guard"]["safe"] is True
    text = (tmp_path / "r.md").read_text()
    assert "Limitations and Unknowns" in text

"""Tests for the offline replay engine."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.latent.offline_replay import (
    REPLAY_STRATEGIES,
    OfflineReplayEngine,
    make_sandbox_bridge,
)
from solaris_ai_nn.signals import canonical as C


def _bridge(steps=40):
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(steps):
        bridge.process(C.Stimulus(payload=f"p{i % 4}", intensity=0.5,
                                  is_absence=(i % 7 == 0)))
        bridge.react(C.Reaction(valence=1.0 if i % 3 == 0 else -0.6))
    return bridge


def test_replay_window_selection_deterministic():
    bridge = _bridge()
    rows = [r.to_row() for r in bridge.trace.records]
    for strategy in REPLAY_STRATEGIES:
        first = OfflineReplayEngine(seed=9).select_windows(
            rows, strategy, window_size=6, count=2)
        second = OfflineReplayEngine(seed=9).select_windows(
            rows, strategy, window_size=6, count=2)
        assert [w["start"] for w in first] == [w["start"] for w in second], \
            strategy
        assert all(w["strategy"] == strategy for w in first)
    # A different seed changes the random_seeded selection.
    other = OfflineReplayEngine(seed=10).select_windows(
        rows, "random_seeded", 6, 2)
    base = OfflineReplayEngine(seed=9).select_windows(
        rows, "random_seeded", 6, 2)
    assert [w["start"] for w in other] != [w["start"] for w in base] \
        or len(rows) <= 2


def test_strategy_anchors_match_their_meaning():
    bridge = _bridge()
    engine = OfflineReplayEngine()
    silence = engine.select_windows(bridge.trace, "silence_window",
                                    window_size=3, count=2)
    assert any(row.get("is_absence")
               for w in silence for row in w["rows"])
    valence = engine.select_windows(bridge.trace, "high_valence",
                                    window_size=3, count=2)
    assert any(abs(row.get("valence", 0) or 0) > 0
               for w in valence for row in w["rows"])


def test_replay_runs_without_external_services():
    """Replay is pure local computation over the trace and a sandbox."""
    import inspect

    from solaris_ai_nn.latent import offline_replay

    source = inspect.getsource(offline_replay)
    for forbidden in ("requests", "urllib", "socket", "subprocess",
                      "http.client"):
        assert forbidden not in source, forbidden


def test_before_after_comparison_works():
    bridge = _bridge()
    engine = OfflineReplayEngine(seed=4)
    window = engine.select_windows(bridge.trace, "recent",
                                   window_size=10, count=1)[0]
    sandbox = make_sandbox_bridge(bridge)
    outcome = engine.replay_window(window, sandbox, mutate=True)
    comparison = outcome["comparison"]
    for key in ("state_norm_drift", "readout_weight_delta",
                "habit_pathway_delta", "suggestion_changed",
                "confidence_delta"):
        assert key in comparison, key
    assert outcome["events_replayed"] > 0
    assert outcome["offline"] is True
    report = engine.to_report()
    assert report["replays"] == 1
    assert report["offline"] is True


def test_sandbox_isolated_from_production():
    bridge = _bridge()
    norm_before = bridge.substrate_state_norm()
    weights_before = [row[:] for row in bridge.readout.weights]
    sandbox = make_sandbox_bridge(bridge)
    # The sandbox starts where production is...
    assert abs(sandbox.substrate_state_norm() - norm_before) < 1e-9
    # ...but diverges privately.
    engine = OfflineReplayEngine()
    window = engine.select_windows(bridge.trace, "recent", 10, 1)[0]
    engine.replay_window(window, sandbox, mutate=True)
    assert bridge.substrate_state_norm() == norm_before
    assert bridge.readout.weights == weights_before
    assert sandbox.telemetry.steps > 0 and bridge.telemetry.steps == 40


def test_unknown_strategy_rejected():
    import pytest

    with pytest.raises(ValueError):
        OfflineReplayEngine().select_windows([], "telepathic")

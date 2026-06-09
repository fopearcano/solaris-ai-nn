"""Tests for the event-trace replay system."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.runtime.replay import EventReplay
from solaris_ai_nn.signals.encoding import EventEncoder


def _fresh_bridge(seed: int = 7) -> SolarisNeuralBridge:
    return SolarisNeuralBridge(
        action_labels=["approach", "withdraw", "consume"],
        encoder=EventEncoder(vocabulary=["light", "noise", "food", "I exist!"]),
        seed=seed,
    )


def _record_a_trace(tmp_path, seed: int = 7):
    from solaris_ai_nn.signals import canonical as C

    payloads = ["light", "noise", "food"]
    correct = {"light": "approach", "noise": "withdraw", "food": "consume"}

    def stim(step):
        return C.Stimulus(payload=payloads[step % 3], intensity=0.6, origin="world")

    def react(result, s):
        return 1.0 if result["suggested_action"] == correct[str(s.payload)] else -1.0

    runner = ContinuousRunner(
        state_dir=tmp_path / "rec", max_steps=60, checkpoint_interval_steps=30,
        seed=seed, vocabulary=payloads + ["I exist!"],
        stimulus_provider=stim, reaction_provider=react, silence_threshold=3,
    )
    runner.run()
    return runner.pm.trace_path


def test_trace_can_be_replayed_into_bridge(tmp_path):
    trace_path = _record_a_trace(tmp_path)
    replay = EventReplay.load_trace(trace_path)
    assert len(replay.signal_rows()) > 0

    bridge = _fresh_bridge()
    n = replay.replay_into_bridge(bridge)
    assert n == len(replay.signal_rows())
    assert bridge.telemetry.events == n


def test_deterministic_replay_produces_stable_telemetry(tmp_path):
    trace_path = _record_a_trace(tmp_path)
    replay = EventReplay.load_trace(trace_path)

    b1 = _fresh_bridge(seed=7)
    b2 = _fresh_bridge(seed=7)
    replay.replay_into_bridge(b1)
    replay.replay_into_bridge(b2)

    r1, r2 = b1.telemetry.report(), b2.telemetry.report()
    assert r1["events"] == r2["events"]
    assert r1["readout_updates"] == r2["readout_updates"]
    assert abs(r1["average_prediction_error"] - r2["average_prediction_error"]) < 1e-9
    # Reservoir state is identical too (deterministic substrate + fixed inputs).
    assert b1.esn.state == b2.esn.state


def test_replay_respects_max_events(tmp_path):
    trace_path = _record_a_trace(tmp_path)
    replay = EventReplay.load_trace(trace_path)
    bridge = _fresh_bridge()
    n = replay.replay_into_bridge(bridge, max_events=5)
    assert n == 5
    assert bridge.telemetry.events == 5

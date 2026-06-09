"""Tests for plasticity integration with the ContinuousRunner."""

from __future__ import annotations

import json

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C

WORLD = {"light": "approach", "noise": "withdraw", "food": "consume"}


def _providers():
    payloads = list(WORLD.keys())

    def stim(step):
        if step % 9 < 3:
            return None
        return C.Stimulus(origin="world", payload=payloads[step % 3], intensity=0.6)

    def react(result, s):
        correct = WORLD.get(str(s.payload))
        return None if correct is None else (1.0 if result["suggested_action"] == correct else -1.0)

    return stim, react


def _runner(tmp_path, **kw):
    stim, react = _providers()
    return ContinuousRunner(
        state_dir=tmp_path / "brain", max_steps=kw.pop("steps", 150),
        checkpoint_interval_steps=50, prune_interval_steps=70, seed=7,
        action_labels=["approach", "withdraw", "consume"],
        vocabulary=list(WORLD.keys()) + ["I exist!"],
        stimulus_provider=stim, reaction_provider=react, silence_threshold=3, **kw,
    )


def test_disabled_makes_no_changes(tmp_path):
    runner = _runner(tmp_path, steps=80)  # plasticity off by default
    lr_before = runner.bridge.learner.lr
    snap = runner.run()
    assert runner.plasticity_engine is None
    assert runner.bridge.learner.lr == lr_before
    assert "plasticity" not in snap


def test_dry_run_logs_but_does_not_apply(tmp_path):
    runner = _runner(tmp_path, enable_plasticity=True, plasticity_dry_run=True,
                     plasticity_interval_steps=25)
    lr_before = runner.bridge.learner.lr
    snap = runner.run()
    assert snap["plasticity"]["applied_count"] == 0
    assert runner.bridge.learner.lr == lr_before
    # Proposals were still audited.
    assert runner.plasticity_engine.audit.count() > 0


def test_enabled_applies_safe_bounded_changes(tmp_path):
    runner = _runner(tmp_path, enable_plasticity=True, plasticity_interval_steps=25)
    snap = runner.run()
    pl = snap["plasticity"]
    assert pl["applied_count"] >= 1
    # All applied parameters stay within their safe bounds.
    from solaris_ai_nn.plasticity.safety import SAFE_BOUNDS
    lr = runner.bridge.learner.lr
    lo, hi = SAFE_BOUNDS[("readout", "learning_rate")]
    assert lo <= lr <= hi


def test_checkpoint_includes_plasticity_state(tmp_path):
    runner = _runner(tmp_path, enable_plasticity=True, plasticity_interval_steps=25)
    runner.run()
    with open(runner.pm.checkpoint_path, "r", encoding="utf-8") as fh:
        cp = json.load(fh)
    assert "plasticity" in cp
    assert "mutable_params" in cp
    assert cp["mutable_params"]  # non-empty list of [component, param, value]
    assert cp["plasticity"]["applied_count"] >= 0

"""BaselineAgent: bounded random/fixed runs; no external-action baseline."""

from __future__ import annotations

import pytest

from solaris_ai_nn.research_lab import BaselineAgent, BaselineAgentType


def test_random_baseline_runs_bounded():
    run = BaselineAgent(BaselineAgentType.RANDOM_ACTION, max_steps=25).run()
    assert run.steps == 25
    assert len(run.actions_taken) == 25
    assert run.real_world_action_count == 0


def test_fixed_baseline_runs_bounded():
    run = BaselineAgent(BaselineAgentType.FIXED_WAIT, max_steps=10).run()
    assert run.steps == 10
    assert set(run.actions_taken) == {"wait"}


def test_no_external_action_baseline_exists():
    # No baseline type names a real-world / external action.
    for b in BaselineAgentType.ALL:
        assert "real" not in b and "external" not in b and "llm" not in b
    # Every baseline run takes zero real-world actions.
    for b in BaselineAgentType.ALL:
        assert BaselineAgent(b, max_steps=5).run().real_world_action_count == 0


def test_baseline_is_deterministic_by_seed():
    a = BaselineAgent(BaselineAgentType.RANDOM_ACTION, seed=3, max_steps=10).run()
    b = BaselineAgent(BaselineAgentType.RANDOM_ACTION, seed=3, max_steps=10).run()
    assert a.actions_taken == b.actions_taken


def test_baseline_metrics_variant_compatible():
    run = BaselineAgent(BaselineAgentType.RANDOM_ACTION).run()
    for key in ("structural_change_score", "prediction_accuracy",
                "non_actuation_proof_score"):
        assert key in run.metrics


def test_unknown_baseline_rejected():
    with pytest.raises(ValueError):
        BaselineAgent("llm_baseline")


def test_run_is_bounded_even_with_huge_request():
    run = BaselineAgent(BaselineAgentType.FIXED_WAIT).run(max_steps=10_000_000)
    assert run.steps <= 5000

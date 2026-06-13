"""Tests for active perception reports + ClaimGuard."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActivePerceptionReportBuilder,
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.active_perception.reports import (
    ACTIVE_PERCEPTION_LIMITATIONS,
)
from solaris_ai_nn.governance.compliance import ClaimGuard


def _controller(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    ctx = {"step": 0, "mysterium_pressure": 0.6,
           "world_model": {"graph_node_count": 10, "unknown_node_count": 3,
                           "prediction_accuracy": 0.5}}
    decision = ctrl.select(ctx)
    result = ctrl.execute_if_allowed(decision, ctx)
    ctrl.observe_result(result, ctx, dict(ctx, step=1,
                                          mysterium_pressure=0.4))
    return ctrl


def test_json_report_generated(tmp_path):
    builder = ActivePerceptionReportBuilder(_controller(tmp_path))
    data = builder.to_dict()
    sections = set(data["sections"])
    for expected in ("current_sampling_policy", "salience_map",
                     "uncertainty_state", "curiosity_pressure",
                     "selected_sampling_actions", "blocked_sampling_actions",
                     "expected_vs_observed_information_gain",
                     "exploration_memory_summary", "stagnation_status",
                     "attention_focus_history",
                     "safety_governance_decisions"):
        assert expected in sections


def test_markdown_generated(tmp_path):
    builder = ActivePerceptionReportBuilder(_controller(tmp_path))
    md = builder.to_markdown()
    assert "Active perception report" in md


def test_claim_guard_scans_report(tmp_path):
    builder = ActivePerceptionReportBuilder(_controller(tmp_path))
    assert ClaimGuard().is_safe(builder.to_markdown())


def test_limitations_included(tmp_path):
    builder = ActivePerceptionReportBuilder(_controller(tmp_path))
    md = builder.to_markdown()
    assert ACTIVE_PERCEPTION_LIMITATIONS
    assert "never real-world autonomy" in md


def test_save_runs_claim_guard(tmp_path):
    builder = ActivePerceptionReportBuilder(_controller(tmp_path))
    paths = builder.save(tmp_path / "ap.json", tmp_path / "ap.md")
    assert (tmp_path / "ap.md").exists()
    assert paths["claim_guard"]["safe"] is True

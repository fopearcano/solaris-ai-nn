"""Tests for governance understanding pilot profiles."""

from __future__ import annotations

import json

from solaris_ai_nn.governance import (
    ApprovalRegistry,
    GovernancePolicy,
    PermissionScope,
    RiskLevel,
    assess_manifest,
)
from solaris_ai_nn.governance.runbook import RunbookBuilder
from solaris_ai_nn.pilot.deployment_runner import PilotDeploymentRunner
from solaris_ai_nn.pilot.pilot_manifest import PilotManifest


def _ops_view(features=None):
    return {"mode": "bounded", "checkpoint_interval_steps": 50,
            "max_steps": 100, "enabled_features": features or {}}


def test_pilot_profile_risk_levels():
    simulated = assess_manifest(_ops_view({"embodiment": True}),
                                {"pilot_profile": "simulated"})
    assert simulated.overall_level == RiskLevel.MEDIUM

    stream = assess_manifest(_ops_view(), {"pilot_profile":
                                           "read_only_stream"})
    assert stream.overall_level == RiskLevel.MEDIUM
    assert any(i.name == "external_stream_ingestion" for i in stream.items)

    sidecar = assess_manifest(_ops_view({"sidecar": True}),
                              {"pilot_profile": "solaris_sidecar_observe"})
    assert sidecar.overall_level == RiskLevel.MEDIUM
    assert any(i.name == "sidecar_observation_pilot" for i in sidecar.items)


def test_read_only_stream_profile_requires_correct_permissions(tmp_path):
    """The stream pilot needs only default permissions (bounded run)."""
    src = tmp_path / "in.jsonl"
    src.write_text(json.dumps({"payload": "x"}) + "\n")
    manifest = PilotManifest(profile="read_only_stream", operator="tester",
                             state_dir=str(tmp_path / "state"),
                             artifact_dir=str(tmp_path / "pilots"),
                             input_sources=[str(src)], max_steps=40,
                             notes="t")
    runner = PilotDeploymentRunner(manifest=manifest,
                                   approved_output_roots=[str(tmp_path)])
    runner.acknowledge_risks()
    snapshot = runner.run()
    assert not snapshot["refused"]
    governance = (snapshot["supervisor"] or {}).get("governance") or {}
    assert governance["policy_status"] == "allowed"
    assert "run_bounded" in governance["active_permissions"]


def test_sidecar_suggestion_publishing_requires_approval():
    policy = GovernancePolicy()
    decision = policy.evaluate_sidecar_operation("publish_suggestions", {})
    assert not decision.allowed
    assert PermissionScope.ENABLE_SIDECAR_SUGGESTIONS \
        in decision.required_approvals
    registry = ApprovalRegistry()
    request = registry.request_approval(
        PermissionScope.ENABLE_SIDECAR_SUGGESTIONS, reason="pilot test")
    registry.approve(request.request_id, "tester")
    assert GovernancePolicy(approvals=registry).evaluate_sidecar_operation(
        "publish_suggestions", {}).allowed


def test_real_world_action_prohibited():
    assessment = assess_manifest(_ops_view(),
                                 {"pilot_profile": "read_only_stream",
                                  "real_world_actuation": True})
    assert assessment.blocked
    assert assessment.overall_level == RiskLevel.PROHIBITED
    decision = GovernancePolicy().evaluate_action("robot_gripper_close", {})
    assert not decision.allowed
    assert not decision.required_approvals  # cannot be approved into being


def test_pilot_runbooks_generated():
    builder = RunbookBuilder()
    for runbook_type, marker in (
            ("pilot_simulated", "GridWorld"),
            ("pilot_stream", "read, validated line by line"),
            ("pilot_sidecar", "never committed")):
        runbook = builder.build(runbook_type)
        md = runbook.to_markdown()
        assert marker in md, runbook_type
        assert "Emergency stop procedure" in md

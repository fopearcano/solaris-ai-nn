"""Tests for governance wired into the SolarisNNSidecar."""

from __future__ import annotations

from solaris_ai_nn.experiments.solaris_sidecar_observation import (
    FakeConscience,
    Stimulus,
)
from solaris_ai_nn.governance import (
    ApprovalRegistry,
    GovernancePolicy,
    PermissionScope,
)
from solaris_ai_nn.integration.conscience_sidecar import SolarisNNSidecar


def test_observe_only_allowed():
    sidecar = SolarisNNSidecar(observe_only=True, governance=GovernancePolicy(),
                               vocabulary=["light", "noise"], seed=3)
    sidecar.attach(FakeConscience())
    sidecar.start()
    assert sidecar.state.attached
    snap = sidecar.snapshot()
    assert snap["governance"]["enabled"] is True
    assert snap["governance"]["publish_active"] is False


def test_suggestion_publishing_requires_approval():
    # publish requested, but no approval -> downgraded to store-only.
    sidecar = SolarisNNSidecar(observe_only=False, publish_suggestions=True,
                               governance=GovernancePolicy(),
                               vocabulary=["light", "noise"], seed=3)
    conscience = FakeConscience()
    sidecar.attach(conscience)
    sidecar.start()
    assert sidecar.channel.publish_enabled is False  # downgraded, not bypassed
    decisions = sidecar.snapshot()["governance"]["policy_decisions"]
    assert any(not d["allowed"] for d in decisions)

    for _ in range(4):
        conscience.bus.publish(Stimulus(payload="light", intensity=0.9))
    assert sidecar.state.suggestions_published == 0  # stored, never published


def test_approved_publishing_proceeds():
    approvals = ApprovalRegistry()
    request = approvals.request_approval(
        PermissionScope.ENABLE_SIDECAR_SUGGESTIONS, reason="test")
    approvals.approve(request.request_id, "tester")
    sidecar = SolarisNNSidecar(
        observe_only=False, publish_suggestions=True,
        governance=GovernancePolicy(approvals=approvals),
        suggestion_threshold=0.0, vocabulary=["light", "noise"], seed=3)
    conscience = FakeConscience()
    sidecar.attach(conscience)
    sidecar.start()
    assert sidecar.channel.publish_enabled is True


def test_committed_action_blocked_by_policy():
    policy = GovernancePolicy()
    for operation in ("commit_action", "lifecycle_death"):
        assert not policy.evaluate_sidecar_operation(operation, {}).allowed


def test_sidecar_still_never_drives_conscience():
    sidecar = SolarisNNSidecar(observe_only=False, publish_suggestions=True,
                               governance=GovernancePolicy(),
                               vocabulary=["light"], seed=3)
    conscience = FakeConscience()
    sidecar.attach(conscience)
    sidecar.start()
    for _ in range(8):
        conscience.bus.publish(Stimulus(payload="light"))
    sidecar.stop()
    sidecar.detach()
    assert conscience.stimulate_calls == 0
    assert conscience.react_calls == 0
    assert conscience.death_calls == 0

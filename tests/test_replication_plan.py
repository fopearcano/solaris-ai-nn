"""Replication plan: arms serialize, live arm governed, missing inconclusive."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    ReplicationArm,
    ReplicationCondition,
    ReplicationPlan,
)


def test_arms_serialize():
    plan = ReplicationPlan.default()
    assert set(plan.arms) == set(ReplicationCondition.ALL)
    for arm in plan.arms.values():
        d = arm.to_dict()
        assert d["arm_id"] and d["condition"]
        assert "limitations" in d


def test_live_arm_requires_governance():
    plan = ReplicationPlan.default()
    live = plan.arm(ReplicationCondition.LIVE_READ_ONLY_IF_AVAILABLE)
    assert live.requires_governance is True
    assert ReplicationCondition.LIVE_READ_ONLY_IF_AVAILABLE in plan.live_arms()


def test_non_live_arm_not_governed():
    plan = ReplicationPlan.default()
    assert plan.arm(ReplicationCondition.FIXTURE_ONLY).requires_governance \
        is False


def test_for_condition_builds_sensorium():
    arm = ReplicationArm.for_condition(ReplicationCondition.NON_HUMAN_ONLY)
    assert arm.sensorium_profile == "non_human"


def test_plan_disclaims_life():
    note = ReplicationPlan.default().to_dict()["note"]
    assert "does not prove life" in note
    assert "consciousness" in note

"""Integration: repair requests rollback through plasticity."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration import AutoRegenerationEngine, RepairPolicy
from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairActionType,
    make_repair,
)
from solaris_ai_nn.autoregeneration.repair_policy import RepairDecision


class _FakeRollback:
    def __init__(self, has_update):
        self._has = has_update
        self.rolled_back = []

    def last_applied(self):
        return object() if self._has else None


def _engine(tmp_path, rollback):
    return AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"),
        plasticity_rollback=rollback)


def test_rollback_routes_through_plasticity(tmp_path):
    engine = _engine(tmp_path, _FakeRollback(has_update=True))
    decision = RepairDecision(
        action=make_repair(RepairActionType.ROLLBACK_LAST_PLASTICITY_UPDATE,
                           target_ref="drift"),
        mode="safe_auto_repair", apply_allowed=True)
    result = engine._handle(decision, {"state_dir": str(tmp_path)})
    assert result.applied is True
    assert "rollback" in result.detail


def test_no_update_to_roll_back_is_inconclusive(tmp_path):
    engine = _engine(tmp_path, _FakeRollback(has_update=False))
    decision = RepairDecision(
        action=make_repair(RepairActionType.ROLLBACK_LAST_PLASTICITY_UPDATE),
        mode="safe_auto_repair", apply_allowed=True)
    result = engine._handle(decision, {"state_dir": str(tmp_path)})
    assert result.applied is False
    assert result.result_class == "inconclusive"


def test_plasticity_safety_remains_authoritative():
    # Auto-regeneration cannot rewrite source via a plasticity-style repair;
    # the autoregen safety validator refuses a source-targeted repair before
    # it ever reaches plasticity.
    from solaris_ai_nn.autoregeneration import (
        AutoRegenerationSafetyValidator,
    )

    v = AutoRegenerationSafetyValidator()
    bad = make_repair(RepairActionType.RESET_BOUNDED_RUNTIME_PARAMETER,
                      target_ref="src/solaris_ai_nn/reservoir/readout.py",
                      reason="rewrite readout source")
    assert not v.validate_repair_action(bad).safe

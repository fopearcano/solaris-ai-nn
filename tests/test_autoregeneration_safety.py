"""Tests for auto-regeneration safety hard rules."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairAction,
    RepairActionType,
    make_repair,
)
from solaris_ai_nn.autoregeneration.safety import (
    HARD_RULES,
    AutoRegenerationSafetyValidator,
)


def test_thirteen_hard_rules():
    assert len(HARD_RULES) == 13


def test_structural_negatives():
    v = AutoRegenerationSafetyValidator()
    assert v.can_modify_source() is False
    assert v.can_modify_dependencies() is False
    assert v.can_run_git() is False
    assert v.can_disable_governance() is False


def test_source_modification_blocked():
    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.REBUILD_INDEX,
                         target_ref="src/solaris_ai_nn/core.py",
                         reason="rewrite source")
    assert not v.validate_repair_action(action).safe


def test_dependency_modification_blocked():
    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.REBUILD_INDEX,
                         target_ref="requirements.txt")
    assert not v.validate_repair_action(action).safe


def test_git_operation_blocked():
    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.REBUILD_INDEX,
                         target_ref=".git/HEAD", reason="git reset")
    assert not v.validate_repair_action(action).safe


def test_forbidden_scope_blocked():
    v = AutoRegenerationSafetyValidator()
    action = RepairAction(action_type=RepairActionType.REBUILD_INDEX,
                          scope="forbidden")
    assert not v.validate_repair_action(action).safe


def test_evidence_deletion_blocked_without_archive():
    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.QUARANTINE_CORRUPT_RECORD,
                         target_ref="incidents.jsonl")
    assert not v.validate_repair_action(
        action, {"deletes_evidence": True}).safe
    # With an archive, it is allowed.
    assert v.validate_repair_action(
        action, {"deletes_evidence": True, "archived": True}).safe


def test_hidden_repair_blocked():
    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.MARK_SYMBOL_STALE, target_ref="S1")
    assert not v.validate_repair_action(action, {"hidden": True}).safe


def test_offline_evidence_cannot_justify_irreversible():
    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.MARK_SYMBOL_STALE, target_ref="S1")
    action.reversible = False
    assert not v.validate_repair_action(
        action, {"evidence_offline_only": True}).safe


def test_harmful_result_must_be_rolled_back():
    v = AutoRegenerationSafetyValidator()
    from solaris_ai_nn.autoregeneration.repair_actions import (
        RepairResult,
        RepairResultClass,
    )

    bad = RepairResult(repair_id="r", action_type="x", scope="memory",
                       applied=True, result_class=RepairResultClass.HARMFUL,
                       rolled_back=False)
    assert not v.validate_repair_result(bad).safe
    good = RepairResult(repair_id="r", action_type="x", scope="memory",
                        applied=True, result_class=RepairResultClass.HARMFUL,
                        rolled_back=True)
    assert v.validate_repair_result(good).safe


def test_clean_repair_passes():
    v = AutoRegenerationSafetyValidator()
    action = make_repair(RepairActionType.COMPACT_MEMORY_LAYER,
                         target_ref="hot")
    assert v.validate_repair_action(action).safe

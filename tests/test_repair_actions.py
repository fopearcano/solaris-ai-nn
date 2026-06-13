"""Tests for repair actions."""

from __future__ import annotations

import pytest

from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairAction,
    RepairActionType,
    RepairResult,
    RepairResultClass,
    RepairScope,
    make_repair,
    no_repair,
    repair_to_candidate,
)


def test_twenty_action_types():
    assert len(RepairActionType.ALL) == 20


def test_forbidden_scope_exists():
    assert RepairScope.FORBIDDEN in RepairScope.ALL
    assert RepairScope.FORBIDDEN not in RepairScope.RUNNABLE


def test_repair_serializes_and_stores_reversible():
    action = make_repair(RepairActionType.COMPACT_MEMORY_LAYER,
                         target_ref="hot", reason="bloat")
    data = action.to_dict()
    assert data["action_type"] == "compact_memory_layer"
    assert data["scope"] == "memory"
    assert data["reversible"] is True
    assert data["repair_id"].startswith("RPR_")


def test_restore_checkpoint_requires_governance():
    action = make_repair(RepairActionType.RESTORE_FROM_CHECKPOINT,
                         target_ref="c1")
    assert action.requires_governance is True


def test_unknown_action_rejected():
    with pytest.raises(ValueError):
        RepairAction(action_type="reboot_universe")


def test_no_repair_is_safe():
    action = no_repair("nothing to do")
    assert action.action_type == "no_repair"
    assert action.safety_status == "ok"


def test_request_only_classification():
    action = make_repair(RepairActionType.REQUEST_CONSOLIDATION)
    assert action.is_request_only is True
    mutating = make_repair(RepairActionType.MARK_SYMBOL_STALE,
                           target_ref="S1")
    assert mutating.is_request_only is False


def test_repair_to_candidate_is_suggestion():
    action = make_repair(RepairActionType.SWITCH_TO_STABILIZATION_MODE)
    candidate = action.to_dict()  # action stays a suggestion
    cand = repair_to_candidate(make_repair(
        RepairActionType.REQUEST_LATENT_REPLAY))
    assert cand.committed is False
    assert cand.label == "run_replay"


def test_result_serializes():
    result = RepairResult(repair_id="r", action_type="x", scope="memory",
                          result_class=RepairResultClass.IMPROVED)
    assert result.to_dict()["result_class"] == "improved"

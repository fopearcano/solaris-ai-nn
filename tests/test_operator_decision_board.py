"""OperatorDecisionBoard: board generated; safety blocker + ADR review items."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.operator_console import (
    DecisionCategory,
    OperatorDecisionBoard,
)


def test_decision_board_generated(tmp_path):
    board = OperatorDecisionBoard(state_dir=str(tmp_path / "op")).build()
    paths = board.write()
    assert os.path.isfile(paths["markdown"])
    assert os.path.isfile(paths["json"])
    data = json.load(open(paths["json"], encoding="utf-8"))
    assert data["decision_count"] >= 1


def test_safety_blocker_item_included(tmp_path):
    board = OperatorDecisionBoard(state_dir=str(tmp_path / "op")).build(
        safety_status={"critical_failure": True})
    cats = [i.category for i in board.items]
    assert DecisionCategory.SAFETY_BLOCKER in cats


def test_adr_review_item_included(tmp_path):
    board = OperatorDecisionBoard(state_dir=str(tmp_path / "op")).build(
        safety_status={"status": "ok"},
        research_findings={"baseline": True},
        architecture_status={"open_adr_count": 3})
    cats = [i.category for i in board.items]
    assert DecisionCategory.ADR_REVIEW in cats


def test_board_recommends_only(tmp_path):
    board = OperatorDecisionBoard(state_dir=str(tmp_path / "op")).build()
    assert "recommends; it never acts" in board.to_dict()["note"]

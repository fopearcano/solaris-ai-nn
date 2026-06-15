"""OperatorStatusBoard: JSON + Markdown generated; ClaimGuard; safety shown."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.operator_console import (
    OperatorConsoleConfig,
    OperatorStatusBoard,
    ProfileCatalog,
)


def _board(tmp_path, **kw):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    return OperatorStatusBoard(config=cfg, catalog=ProfileCatalog(), **kw)


def test_json_generated(tmp_path):
    result = _board(tmp_path, safety_status={"status": "ok"}).write()
    assert os.path.isfile(result["json"])
    data = json.load(open(result["json"], encoding="utf-8"))
    assert "available_profile_count" in data


def test_markdown_generated(tmp_path):
    result = _board(tmp_path, safety_status={"status": "ok"}).write()
    assert os.path.isfile(result["markdown"])
    text = open(result["markdown"], encoding="utf-8").read()
    assert "Operator Status Board" in text


def test_claim_guard_scans_report(tmp_path):
    snap = _board(tmp_path, safety_status={"status": "ok"}).build()
    assert snap.claim_guard_safe is True


def test_safety_status_included(tmp_path):
    snap = _board(tmp_path, safety_status={
        "status": "ok", "unresolved_blocker_count": 2}).build()
    assert snap.latest_safety_status == "ok"
    assert snap.unresolved_safety_blocker_count == 2


def test_profile_counts_present(tmp_path):
    snap = _board(tmp_path).build()
    assert snap.available_profile_count > 0
    assert snap.blocked_profile_count >= 1

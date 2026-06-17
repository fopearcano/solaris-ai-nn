"""First tester task sheet: generated, required/optional separated, stop-if-unsure."""

from __future__ import annotations

import os

from solaris_ai_nn.first_tester_protocol import (
    FirstTesterTaskSheet,
    TesterTaskStatus,
)


def test_task_sheet_generated(tmp_path):
    paths = FirstTesterTaskSheet().write(str(tmp_path))
    assert os.path.isfile(paths["markdown"])
    assert os.path.isfile(paths["json"])


def test_required_optional_separated():
    d = FirstTesterTaskSheet().to_dict()
    assert d["required_count"] > 0
    assert d["optional_count"] > 0
    statuses = {t["status"] for t in d["tasks"]}
    assert TesterTaskStatus.REQUIRED in statuses
    assert TesterTaskStatus.OPTIONAL in statuses


def test_stop_if_unsure_present():
    text = FirstTesterTaskSheet().build_text().lower()
    assert "stop if unsure" in text


def test_live_readonly_optional():
    sheet = FirstTesterTaskSheet()
    live = [t for t in sheet.tasks if "live-read-only" in t.text]
    assert live
    assert all(t.status == TesterTaskStatus.OPTIONAL for t in live)

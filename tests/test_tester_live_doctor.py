"""Tester live doctor: missing/disabled governance block, forbidden block, safe pass."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_live_readonly import (
    GovernanceTemplateBuilder,
    TesterLiveDoctor,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_live_helpers import approve_governance, write_feeder_registry  # noqa: E402


def test_missing_governance_blocks(tmp_path):
    write_feeder_registry(str(tmp_path))
    doc = TesterLiveDoctor().check(state_dir=str(tmp_path))
    assert not doc.passed
    assert any(f.check == "governance_file_exists" for f in doc.blockers)


def test_disabled_governance_blocks(tmp_path):
    write_feeder_registry(str(tmp_path))
    GovernanceTemplateBuilder().write_live_governance(str(tmp_path))  # disabled
    doc = TesterLiveDoctor().check(state_dir=str(tmp_path))
    assert not doc.passed
    checks = {f.check for f in doc.blockers}
    assert "governance_enabled" in checks


def test_forbidden_source_blocks(tmp_path):
    write_feeder_registry(str(tmp_path))
    approve_governance(str(tmp_path), allowed_extra=["raw_microphone"])
    doc = TesterLiveDoctor().check(state_dir=str(tmp_path))
    assert not doc.passed
    assert any(f.check == "no_forbidden_source_allowed" for f in doc.blockers)


def test_safe_config_passes(tmp_path):
    write_feeder_registry(str(tmp_path))
    approve_governance(str(tmp_path))
    os.makedirs(os.path.join(str(tmp_path), "inbox"), exist_ok=True)
    os.makedirs(os.path.join(str(tmp_path), "quarantine"), exist_ok=True)
    doc = TesterLiveDoctor().check(state_dir=str(tmp_path))
    assert doc.passed
    assert doc.overall_status in ("pass", "pass_with_warnings")

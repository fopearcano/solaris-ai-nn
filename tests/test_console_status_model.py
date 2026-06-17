"""Console status model: statuses generated, optional missing not failure, blockers."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import (  # noqa: E402
    build_console,
    stage_forbidden_governance,
)
from solaris_ai_nn.tester_console import StageHealth  # noqa: E402


def test_statuses_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    status = rt.status.to_dict()
    assert status["stage_count"] >= 15
    assert status["overall_health"] in StageHealth.ALL


def test_optional_missing_not_failure(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    for stage_id in ("live_ontogenesis", "live_semiogenesis", "live_cognition"):
        st = rt.status.stage(stage_id)
        assert st.health == StageHealth.SKIPPED_OPTIONAL
        assert st.ok is True  # optional skip is not a failure


def test_safety_blocker_overrides_pass(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    stage_forbidden_governance(os.path.join(str(tmp_path), "live"))
    rt2 = build_console(tmp_path, fixture=False)
    # Re-run with the forbidden governance staged.
    assert rt2.status.overall_health == StageHealth.BLOCKED
    assert rt2.status.release_ready is False


def test_missing_required_is_blocker(tmp_path):
    rt = build_console(tmp_path)  # empty -> no fixture demo
    blockers = [b.stage for b in rt.status.blockers]
    assert "tester_fixture_demo" in blockers

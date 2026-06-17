"""Tester live + fixture spine: fixture recommended before live; failure blocks strict."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime


def test_fixture_demo_recommended_before_live(tmp_path):
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tmp_path / "tester"))
    rt.run()
    assert rt.fixture_status["fixture_demo_status"] == "unavailable"
    assert any("fixture" in w.lower() for w in rt.warnings)
    assert any("fixture" in s.lower() for s in rt.recommended_next_steps())


def test_fixture_failure_blocks_strict_live(tmp_path):
    # Tester root is the parent of the tester live state dir.
    tester_live = tmp_path / "tester" / "live"
    reports = tmp_path / "tester" / "reports"
    reports.mkdir(parents=True)
    with open(reports / "TESTER_RUN_SUMMARY_x.json", "w") as fh:
        json.dump({"reproducibility": {"reproducibility_status": "fail"}}, fh)
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=str(tester_live), strict=True)
    rt.run()
    assert rt.fixture_status["fixture_demo_status"] == "failed"
    assert rt.blocked is True
    assert any("fixture" in b.lower() for b in rt.blockers)


def test_fixture_pass_does_not_block(tmp_path):
    tester_live = tmp_path / "tester" / "live"
    reports = tmp_path / "tester" / "reports"
    reports.mkdir(parents=True)
    with open(reports / "TESTER_RUN_SUMMARY_x.json", "w") as fh:
        json.dump({"reproducibility": {"reproducibility_status": "pass"}}, fh)
    rt = TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"), tester_state_dir=str(tester_live))
    rt.run()
    assert rt.fixture_status["fixture_demo_status"] == "passed"

"""Bug report: validates, preserves reproduction/artifacts, no auto-fix."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import BugReportBuilder


def _report():
    return BugReportBuilder().build({
        "bug_id": "b1", "affected_module": "membrane",
        "expected_behavior": "ok", "actual_behavior": "crash",
        "reproduction_steps": ["step 1", "step 2"],
        "artifact_paths": ["a.json", "b.json"],
        "non_training_acknowledgement": True})


def test_bug_report_validates():
    report = _report()
    result = BugReportBuilder().validate(report)
    assert result.valid is True


def test_reproduction_steps_preserved():
    assert _report().reproduction_steps == ["step 1", "step 2"]


def test_artifact_paths_preserved():
    assert _report().artifact_paths == ["a.json", "b.json"]


def test_no_auto_fix_triggered():
    d = _report().to_dict()
    assert d["patches_anything"] is False
    assert d["triggers_auto_fix"] is False
    assert d["creates_github_issue"] is False


def test_missing_ack_fails_validation():
    report = BugReportBuilder().build({"bug_id": "b2",
                                       "actual_behavior": "x"})
    result = BugReportBuilder().validate(report)
    assert result.valid is False

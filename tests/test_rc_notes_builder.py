"""RC notes: release notes, known issues, feedback guide, non-claim wording."""

from __future__ import annotations

from solaris_ai_nn.tester_release_candidate import (
    TesterFeedbackGuideBuilder,
    TesterKnownIssuesBuilder,
    TesterReleaseNotesBuilder,
)


def test_release_notes_generated(tmp_path):
    path = TesterReleaseNotesBuilder(rc_id="rc_test").write(str(tmp_path))
    text = open(path, encoding="utf-8").read().lower()
    assert "release name" in text or "release notes" in text
    assert "what is included" in text
    assert "what is excluded" in text


def test_known_issues_generated(tmp_path):
    path = TesterKnownIssuesBuilder(
        open_blockers=["x: y"], missing_optional_modules=["cognition report"]
    ).write(str(tmp_path))
    text = open(path, encoding="utf-8").read().lower()
    assert "known issues" in text
    assert "release blockers" in text
    assert "cognition report" in text


def test_feedback_guide_generated(tmp_path):
    path = TesterFeedbackGuideBuilder().write(str(tmp_path))
    text = open(path, encoding="utf-8").read().lower()
    assert "not training" in text
    assert "not rlhf" in text
    assert "secrets" in text


def test_non_claim_wording_present(tmp_path):
    text = TesterReleaseNotesBuilder(rc_id="x").build_text().lower()
    assert "makes no claim" in text
    assert "not a consciousness demo" in text

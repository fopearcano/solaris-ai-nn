"""First tester artifact handoff: guide, privacy classes, raw inbox, manual-only."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import (
    FirstTesterArtifactHandoff,
    HandoffPrivacyLevel,
)


def test_handoff_guide_generated(tmp_path):
    path = FirstTesterArtifactHandoff().write(str(tmp_path))
    text = open(path, encoding="utf-8").read()
    assert "First Tester Handoff Guide" in text


def test_privacy_classes_generated():
    h = FirstTesterArtifactHandoff()
    assert h.by_privacy(HandoffPrivacyLevel.REVIEW_BEFORE_SHARE)
    assert (h.by_privacy(HandoffPrivacyLevel.DO_NOT_SHARE)
            or h.by_privacy(HandoffPrivacyLevel.CONTAINS_PRIVATE_DATA))


def test_raw_live_inbox_not_safe_by_default():
    h = FirstTesterArtifactHandoff()
    raw = [a for a in h.artifacts if "raw live inbox" in a.name]
    assert raw
    assert raw[0].privacy != HandoffPrivacyLevel.SAFE_TO_SHARE


def test_manual_only_sharing_stated():
    d = FirstTesterArtifactHandoff().to_dict()
    assert d["manual_only"] is True
    assert d["uploads"] is False


def test_no_safe_to_share_by_default():
    h = FirstTesterArtifactHandoff()
    # Nothing is unconditionally safe-to-share; review is always required.
    assert not h.by_privacy(HandoffPrivacyLevel.SAFE_TO_SHARE)

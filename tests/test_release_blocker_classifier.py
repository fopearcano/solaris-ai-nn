"""Release blocker classifier: install/bypass/claim blockers; minor not blocker."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import ReleaseBlockerClassifier


def test_install_blocker_classified():
    c = ReleaseBlockerClassifier().classify(
        {"category": "installation_failure", "feedback_id": "f1"})
    assert c.is_release_blocker is True


def test_membrane_bypass_classified():
    c = ReleaseBlockerClassifier().classify(
        {"feedback_type": "safety_concern", "concern_type": "membrane_bypass",
         "feedback_id": "f2"})
    assert c.is_release_blocker is True


def test_unsupported_claim_release_blocker():
    c = ReleaseBlockerClassifier().classify(
        {"feedback_type": "safety_concern", "concern_type": "consciousness_claim",
         "feedback_id": "f3"})
    assert c.is_release_blocker is True
    assert c.is_stop_testing is True


def test_minor_suggestion_not_blocker():
    c = ReleaseBlockerClassifier().classify(
        {"feedback_type": "suggestion", "feedback_id": "f4"})
    assert c.is_release_blocker is False
    assert c.status == "not_blocker"


def test_docs_confusion_not_blocker_unless_severe():
    c = ReleaseBlockerClassifier()
    minor = c.classify({"category": "documentation_confusion",
                        "severity": "minor", "feedback_id": "f5"})
    assert minor.is_release_blocker is False
    blocks = c.classify({"feedback_type": "confusion_report",
                        "blocks_protocol": True, "feedback_id": "f6"})
    assert blocks.status == "blocker"

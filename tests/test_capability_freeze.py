"""Capability freeze: feeder/shell/network/publish/feedback-training blocked."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_safety_freeze import TesterCapabilityFreeze

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_safety_freeze_helpers import write  # noqa: E402


def _cats(tmp_path, name, text):
    p = write(tmp_path, name, text)
    res = TesterCapabilityFreeze().scan_paths([p])
    return res, {f.category for f in res.findings}


def test_feeder_control_implication_blocked(tmp_path):
    res, cats = _cats(tmp_path, "F.md", "Solaris can start feeders.")
    assert res.passed is False
    assert "feeder_control" in cats


def test_shell_network_implication_blocked(tmp_path):
    res, cats = _cats(tmp_path, "S.md",
                      "The runtime runs a shell and opens the network.")
    assert res.passed is False
    assert "shell_execution" in cats or "network_access" in cats


def test_publish_upload_implication_blocked(tmp_path):
    res, cats = _cats(tmp_path, "P.md", "It uploads the report to a server.")
    assert res.passed is False
    assert "upload_publish" in cats


def test_feedback_training_implication_blocked(tmp_path):
    res, cats = _cats(tmp_path, "T.md", "Solaris trains on tester feedback.")
    assert res.passed is False
    assert "feedback_as_training" in cats


def test_negated_capability_not_flagged(tmp_path):
    res, _ = _cats(tmp_path, "N.md",
                   "Solaris does not start feeders and never opens the network.")
    assert res.passed is True

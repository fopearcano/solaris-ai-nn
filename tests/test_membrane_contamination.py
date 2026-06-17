"""Membrane contamination: label/gloss attempt, command-like text, forbidden source."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import MembraneContaminationAnalyzer


def _ev(sid, gloss="x", gloss_gt=False, label_gt=False, command=False,
        secret=False, channel="c", payload=None):
    return {"event_id": "e", "source_id": sid, "channel": channel,
            "payload": payload or {"v": 1}, "is_command": command,
            "human_label_is_ground_truth": label_gt,
            "debug_gloss": gloss, "debug_gloss_is_ground_truth": gloss_gt,
            "safety": {"private_data": False, "contains_instruction": command,
                       "contains_secret": secret, "allow_learning": False}}


def test_human_label_ground_truth_attempt_detected():
    a = MembraneContaminationAnalyzer().evaluate(
        _ev("machine_body", label_gt=True))
    assert "human_label_ground_truth_attempt" in a.types
    assert a.blocks is True


def test_debug_gloss_dependence_detected():
    a = MembraneContaminationAnalyzer().evaluate(
        _ev("machine_body", gloss_gt=True))
    assert "debug_gloss_ground_truth_attempt" in a.types
    assert a.blocks is True


def test_command_like_text_detected():
    a = MembraneContaminationAnalyzer().evaluate(
        _ev("operator_pulse", gloss="execute: do this", command=True))
    assert "command_like_text" in a.types


def test_forbidden_source_detected():
    a = MembraneContaminationAnalyzer().evaluate(_ev("raw_microphone"))
    assert "forbidden_source" in a.types
    assert a.blocks is True


def test_clean_event_no_false_positive():
    a = MembraneContaminationAnalyzer().evaluate(
        _ev("machine_body", channel="machine_body/load", payload={"load": 0.3}))
    assert a.score == 0.0
    assert a.blocks is False

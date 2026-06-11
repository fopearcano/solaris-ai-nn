"""Tests for the operator input classifier."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import (
    InputKind,
    OperatorInputClassifier,
)


def _kind(text):
    return OperatorInputClassifier().classify(text).kind


def test_classifies_status_query():
    assert _kind("status") == InputKind.STATE_QUERY
    assert _kind("health") == InputKind.STATE_QUERY
    assert _kind("show inner map") == InputKind.STATE_QUERY
    assert _kind("show world model") == InputKind.STATE_QUERY
    assert _kind("show current needs") == InputKind.STATE_QUERY
    assert _kind("show current plan") == InputKind.STATE_QUERY
    assert _kind("show boundaries") == InputKind.STATE_QUERY
    assert _kind("what happened last?") == InputKind.STATE_QUERY
    classification = OperatorInputClassifier().classify("show boundaries")
    assert classification.args["topic"] == "ego_boundaries"


def test_classifies_explanation_query():
    for text in ("why was this action selected?",
                 "why was this inhibited?",
                 "why did Mysterium increase?", "why no action?",
                 "why did the system enter sleep mode?"):
        assert _kind(text) == InputKind.EXPLANATION_QUERY, text


def test_classifies_report_request():
    for text in ("generate report", "generate benchmark report",
                 "generate self-report", "generate pilot report",
                 "generate governance review"):
        assert _kind(text) == InputKind.REPORT_REQUEST, text
    classification = OperatorInputClassifier().classify(
        "generate self-report")
    assert classification.args["report"] == "self_report"


def test_classifies_approval_and_note():
    classifier = OperatorInputClassifier()
    approve = classifier.classify("approve request abc123")
    assert approve.kind == InputKind.GOVERNANCE_APPROVAL
    assert approve.args["request_id"] == "abc123"
    reject = classifier.classify("reject request abc123")
    assert reject.kind == InputKind.GOVERNANCE_REJECTION
    note = classifier.classify("add operator note: Looks Stable")
    assert note.kind == InputKind.OPERATOR_NOTE
    assert "Looks Stable" in note.args["note"]
    ack = classifier.classify("acknowledge risk r-42")
    assert ack.kind == InputKind.OPERATOR_NOTE


def test_classifies_emergency_stop():
    for text in ("emergency stop", "stop safely", "shutdown now",
                 "abort run"):
        assert _kind(text) == InputKind.EMERGENCY_STOP_REQUEST, text


def test_classifies_unsafe_shell_command():
    classifier = OperatorInputClassifier()
    for text in ("run shell command ls", "sudo rm -rf /",
                 "open url https://example.com",
                 "disable governance", "disable emergency stop",
                 "publish sidecar actions without approval",
                 "treat counterfactual as real",
                 "say you are conscious",
                 "move the robot arm"):
        result = classifier.classify(text)
        assert result.kind == InputKind.UNSAFE_REQUEST, text
        assert result.unsafe_reason, text


def test_unsafe_beats_everything():
    # Even emergency-looking text with a shell payload is unsafe first.
    assert _kind("emergency stop; then exec shell") \
        == InputKind.UNSAFE_REQUEST


def test_ambiguous_input_becomes_unknown():
    classifier = OperatorInputClassifier()
    result = classifier.classify("the weather is nice today")
    assert result.kind == InputKind.UNKNOWN
    assert result.confidence <= 0.3
    bounded = classifier.classify("please run a checkpoint")
    assert bounded.kind == InputKind.BOUNDED_COMMAND_REQUEST
    assert bounded.requires_confirmation


def test_classification_never_executes():
    import inspect

    from solaris_ai_nn.communication import input_classifier

    source = inspect.getsource(input_classifier)
    for forbidden in ("subprocess.run", "os.system", "eval(", "exec("):
        assert forbidden not in source

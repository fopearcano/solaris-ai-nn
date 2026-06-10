"""Tests for the FailureAnalyzer."""

from __future__ import annotations

from solaris_ai_nn.evaluation.failure_analysis import FailureAnalyzer

FA = FailureAnalyzer()


def _names(findings):
    return {f.name for f in findings}


def test_detects_empty_trace():
    findings = FA.analyze({"continuity": {"trace_continuity_ratio": 0.0}})
    assert "memory_trace_empty" in _names(findings)
    critical = [f for f in findings if f.name == "memory_trace_empty"][0]
    assert critical.severity == "critical"
    assert critical.next_step  # always a suggested debug step


def test_detects_no_substrate_change():
    findings = FA.analyze({"substrate": {"state_norm": 0.0, "state_drift": 0.0}})
    assert "no_substrate_change" in _names(findings)


def test_detects_too_many_blocked_actions():
    findings = FA.analyze({"embodiment": {"present": True,
                                          "executed_actions": 2,
                                          "blocked_actions": 8}})
    assert "too_many_blocked_actions" in _names(findings)


def test_detects_missing_checkpoint():
    findings = FA.analyze({"checkpoint_expected": True}, artifacts={})
    assert "checkpoint_missing" in _names(findings)


def test_detects_replay_mismatch_and_plasticity_lockout():
    findings = FA.analyze({
        "reproducibility": {"deterministic": False, "detail": "norm differs"},
        "plasticity": {"proposed_mutations": 5, "applied_mutations": 0},
    })
    names = _names(findings)
    assert "replay_mismatch" in names
    assert "plasticity_rejected_everything" in names


def test_clean_metrics_yield_no_findings():
    findings = FA.analyze({
        "substrate": {"state_norm": 4.0, "state_drift": 0.5,
                      "activity_rate": 0.5, "silence_ratio": 0.2},
        "continuity": {"trace_continuity_ratio": 1.0, "unexpected_deaths": 0},
        "reactivity": {"stimulus_count": 10, "reaction_count": 5},
    })
    assert findings == []

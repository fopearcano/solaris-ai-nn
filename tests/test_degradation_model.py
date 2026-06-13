"""Tests for the degradation model."""

from __future__ import annotations

import pytest

from solaris_ai_nn.autoregeneration.degradation import (
    DegradationSeverity,
    DegradationSignal,
    DegradationState,
    DegradationType,
)


def test_twenty_one_degradation_types():
    assert len(DegradationType.ALL) == 21


def test_four_severities():
    assert len(DegradationSeverity.ALL) == 4
    for s in ("info", "watch", "warning", "critical"):
        assert s in DegradationSeverity.ALL


def test_signal_serializes():
    sig = DegradationSignal(type=DegradationType.MEMORY_BLOAT,
                            severity=DegradationSeverity.WARNING,
                            evidence_refs=["over_budget:hot"])
    data = sig.to_dict()
    assert data["type"] == "memory_bloat"
    assert data["evidence_ok"] is True
    assert data["signal_id"].startswith("DEG_")


def test_warning_requires_evidence():
    sig = DegradationSignal(type=DegradationType.MEMORY_BLOAT,
                            severity=DegradationSeverity.WARNING)
    assert sig.evidence_ok is False
    watch = DegradationSignal(type=DegradationType.MEMORY_BLOAT,
                              severity=DegradationSeverity.WATCH)
    assert watch.evidence_ok is True  # watch does not require evidence


def test_critical_requires_evidence():
    sig = DegradationSignal(type=DegradationType.STATE_FILE_CORRUPTION,
                            severity=DegradationSeverity.CRITICAL)
    assert sig.evidence_ok is False


def test_identity_affecting_requires_governance():
    sig = DegradationSignal(type=DegradationType.IDENTITY_CONTINUITY_GAP,
                            severity=DegradationSeverity.WARNING,
                            evidence_refs=["score"])
    assert sig.requires_governance is True


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        DegradationSignal(type="illness")


def test_state_ranks_by_severity():
    state = DegradationState()
    state.add(DegradationSignal(type=DegradationType.MEMORY_BLOAT,
                                severity=DegradationSeverity.WATCH,
                                evidence_refs=["x"]))
    state.add(DegradationSignal(type=DegradationType.DRIFT_RUNAWAY,
                                severity=DegradationSeverity.CRITICAL,
                                evidence_refs=["y"]))
    assert state.worst_severity() == "critical"
    assert state.ranked()[0].severity == "critical"
    assert len(state.critical()) == 1

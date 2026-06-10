"""Tests for the incident log."""

from __future__ import annotations

import pytest

from solaris_ai_nn.ops.incident import INCIDENT_TYPES, Incident, IncidentLog


def test_writes_jsonl_incident(tmp_path):
    log = IncidentLog(tmp_path / "incidents.jsonl", run_id="r", session_id="s")
    incident = log.record("health_warning", "warning", "heartbeat stale",
                          related_metric="heartbeat",
                          suggested_debug_step="check loop")
    assert incident.run_id == "r"
    rows = log.list_incidents()
    assert len(rows) == 1
    row = rows[0]
    for key in ("timestamp", "run_id", "session_id", "severity", "type",
                "message", "related_metric", "suggested_debug_step",
                "resolved"):
        assert key in row
    assert row["resolved"] is False


def test_incident_types_enforced():
    with pytest.raises(ValueError):
        Incident(type="alien_invasion", severity="warning", message="x")
    with pytest.raises(ValueError):
        Incident(type="health_warning", severity="catastrophic", message="x")
    for required in ("health_warning", "health_critical", "watchdog_shutdown",
                     "unexpected_death_detected", "brain_death_gap",
                     "checkpoint_failure", "artifact_rotation_failure",
                     "replay_mismatch", "plasticity_safety_violation",
                     "embodiment_stuck", "substrate_runaway",
                     "substrate_inert"):
        assert required in INCIDENT_TYPES


def test_counting_and_unresolved(tmp_path):
    log = IncidentLog(tmp_path / "incidents.jsonl")
    log.record("substrate_inert", "warning", "a")
    log.record("substrate_inert", "warning", "b")
    log.record("health_critical", "critical", "c")
    assert log.count_by_type()["substrate_inert"] == 2
    assert log.unresolved_count() == 3
    assert log.last()["type"] == "health_critical"

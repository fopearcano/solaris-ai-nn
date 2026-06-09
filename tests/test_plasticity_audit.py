"""Tests for the plasticity audit log."""

from __future__ import annotations

from solaris_ai_nn.plasticity.audit import PlasticityAuditLog
from solaris_ai_nn.plasticity.mutation import (
    PlasticityChange,
    PlasticityResult,
    PlasticityStep,
    PlasticityTarget,
)


def _step():
    return PlasticityStep(
        target=PlasticityTarget("readout", "learning_rate"),
        change=PlasticityChange(old_value=0.3, new_value=0.4),
        reason="error high", run_id="r", session_id="s", lifetime_step=12,
    )


def test_audit_writes_jsonl_rows(tmp_path):
    log = PlasticityAuditLog(tmp_path / "plasticity_audit.jsonl", run_id="r", session_id="s")
    step = _step()
    log.proposed(step)
    log.applied(step)
    rows = log.read_all()
    assert len(rows) == 2
    required = {"timestamp", "run_id", "session_id", "lifetime_step", "event_type",
                "step_id", "target", "reason", "old_value", "new_value"}
    for row in rows:
        assert required <= set(row)
    assert rows[0]["event_type"] == "proposed"
    assert rows[1]["event_type"] == "applied"
    assert rows[1]["target"] == "readout.learning_rate"


def test_applied_rejected_rollback_rows_valid(tmp_path):
    log = PlasticityAuditLog(tmp_path / "audit.jsonl")
    step = _step()
    log.applied(step)
    log.rejected(step)
    log.rollback(step, PlasticityResult(step_id=step.step_id, status="rolled_back", applied=True))
    log.rollback(step, PlasticityResult(step_id=step.step_id, status="rollback_failed", applied=False))
    types = [r["event_type"] for r in log.read_all()]
    assert types == ["applied", "rejected", "rollback", "rollback_failed"]


def test_unknown_event_type_rejected(tmp_path):
    log = PlasticityAuditLog(tmp_path / "audit.jsonl")
    import pytest

    with pytest.raises(ValueError):
        log.log("not_an_event", _step())

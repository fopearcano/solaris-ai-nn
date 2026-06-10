"""Tests for the emergency stop -- graceful, recorded, never a process kill."""

from __future__ import annotations

import inspect

from solaris_ai_nn.governance import emergency as E
from solaris_ai_nn.governance.audit import GovernanceAuditLog
from solaris_ai_nn.ops.incident import IncidentLog
from solaris_ai_nn.ops.safe_shutdown import SafeShutdownManager


class FakeSupervisor:
    """The minimum graceful surface a supervisor exposes."""

    def __init__(self, tmp_path):
        self.ops_dir = tmp_path / "ops"
        self.ops_dir.mkdir(parents=True, exist_ok=True)
        self.shutdown_manager = SafeShutdownManager(self.ops_dir, run_id="r1")
        self.incidents = IncidentLog(self.ops_dir / "incidents.jsonl",
                                     run_id="r1")
        self.stopped_with = None

    def stop(self, reason):
        self.stopped_with = reason

    def _health_snapshot(self):
        return {"telemetry": {"steps": 42}}


def test_emergency_request_records_incident_and_audit(tmp_path):
    audit = GovernanceAuditLog(tmp_path / "audit.jsonl")
    stop = E.EmergencyStop(state_dir=tmp_path / "state", audit=audit)
    result = stop.request("substrate runaway suspected", operator="alice")
    assert result.requested
    assert result.audit_recorded
    assert audit.last()["event_type"] == "emergency_stop_requested"

    supervisor = FakeSupervisor(tmp_path)
    result = stop.perform(supervisor)
    assert result.incident_recorded
    incidents = supervisor.incidents.list_incidents()
    assert incidents[0]["type"] == "emergency_stop"
    assert incidents[0]["severity"] == "critical"
    assert audit.last()["event_type"] == "emergency_stop_completed"


def test_safe_shutdown_requested_not_forced(tmp_path):
    stop = E.EmergencyStop(state_dir=tmp_path / "state")
    stop.request("test stop")
    supervisor = FakeSupervisor(tmp_path)
    result = stop.perform(supervisor)
    assert result.shutdown_requested
    assert supervisor.shutdown_manager.requested
    assert supervisor.stopped_with.startswith("emergency stop")
    assert result.health_snapshot_written
    assert (supervisor.ops_dir / "emergency_health.json").exists()


def test_sentinel_file_detected(tmp_path):
    state_dir = tmp_path / "state"
    assert not E.sentinel_present(state_dir)
    stop = E.EmergencyStop(state_dir=state_dir)
    stop.request("sentinel test")
    assert E.sentinel_present(state_dir)
    assert stop.sentinel.name == "EMERGENCY_STOP"
    assert stop.requested
    # Clearing is an explicit, separate operator action.
    assert stop.clear_sentinel()
    assert not E.sentinel_present(state_dir)


def test_externally_created_sentinel_counts(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "EMERGENCY_STOP").write_text("operator says stop")
    stop = E.EmergencyStop(state_dir=state_dir)
    assert stop.requested  # the file alone is a request


def test_never_deletes_data(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    precious = state_dir / "latest_checkpoint.json"
    precious.write_text("{}")
    stop = E.EmergencyStop(state_dir=state_dir)
    stop.request("test")
    stop.perform(FakeSupervisor(tmp_path))
    assert precious.exists()


def test_no_process_kill_anywhere():
    """The emergency module never touches the process or signals."""
    source = inspect.getsource(E)
    for forbidden in ("os._exit", "sys.exit", "os.kill", "signal.",
                      "SIGKILL", "SIGTERM", "terminate(", "atexit"):
        assert forbidden not in source, forbidden


def test_available_without_any_permission(tmp_path):
    """EmergencyStop needs no PermissionSet at all -- always available."""
    stop = E.EmergencyStop(state_dir=tmp_path / "state")
    assert stop.snapshot()["available"] is True
    result = stop.request("no permissions consulted")
    assert result.requested

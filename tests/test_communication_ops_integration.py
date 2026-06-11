"""Tests for communication routed to the ops layer."""

from __future__ import annotations

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.incident import IncidentLog
from solaris_ai_nn.ops.safe_shutdown import SafeShutdownManager


def test_health_status_queries_routed_to_ops(tmp_path):
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={
            "governance": GovernancePolicy(),
            "ops_status": {"run_mode": "bounded", "steps": 60,
                           "health_level": "ok"},
            "health": {"level": "ok", "findings": []}})
    status = gateway.handle_input("status")
    assert "run_mode=bounded" in status.text
    health = gateway.handle_input("health")
    assert health.kind == "health"
    assert "level=ok" in health.text


def test_incident_summary_query(tmp_path):
    log = IncidentLog(tmp_path / "incidents.jsonl")
    log.record("health_warning", "warning", "test incident")
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"governance": GovernancePolicy(),
                    "incidents": {"incident_count": 1,
                                  "last": "health_warning"}})
    response = gateway.handle_input("show incidents")
    assert "incident_count=1" in response.text


def test_safe_shutdown_request_routed_safely(tmp_path):
    shutdown = SafeShutdownManager(ops_dir=tmp_path / "ops")
    gateway = CommunicationGateway(
        state_dir=tmp_path,
        components={"governance": GovernancePolicy(),
                    "shutdown": shutdown})
    # Non-emergency shutdown phrasing goes through confirmation first.
    response = gateway.handle_input("emergency stop")
    assert response.kind == "emergency"
    assert shutdown.requested
    assert shutdown.snapshot()["reason"].startswith(
        "operator emergency request")


def test_supervisor_exposes_communication_snapshot(tmp_path):
    """The supervisor health snapshot picks up runner.communication."""
    import inspect

    from solaris_ai_nn.ops.supervisor import OperationalSupervisor

    source = inspect.getsource(OperationalSupervisor._health_snapshot)
    assert 'getattr(runner, "communication", None)' in source
    assert 'snapshot["communication"] = communication.summary()' in source

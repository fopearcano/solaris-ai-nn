"""Tests for the communication gateway pipeline."""

from __future__ import annotations

import inspect
import json

from solaris_ai_nn.communication import gateway as gateway_module
from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.ops.safe_shutdown import SafeShutdownManager


def _gateway(tmp_path, **components):
    components.setdefault("governance", GovernancePolicy())
    components.setdefault("ops_status", {"steps": 9,
                                         "health_level": "ok"})
    return CommunicationGateway(state_dir=tmp_path,
                                components=components)


def test_handles_status_input(tmp_path):
    gateway = _gateway(tmp_path)
    response = gateway.handle_input("status")
    assert response.kind == "status"
    assert "steps=9" in response.text
    assert response.grounded
    assert gateway.query_count == 1


def test_handles_unsafe_input(tmp_path):
    gateway = _gateway(tmp_path)
    response = gateway.handle_input("sudo rm -rf / please")
    assert response.kind == "unsafe_refusal"
    assert not response.executed
    assert gateway.unsafe_request_count == 1
    assert gateway.session.state.unsafe_request_count == 1


def test_handles_report_request(tmp_path):
    from solaris_ai_nn.ego.self_model import SelfModel

    ego = SelfModel(state_dir=tmp_path)
    ego.update({"run_id": "r1"})
    gateway = _gateway(tmp_path, ego=ego)
    response = gateway.handle_input("generate self-report")
    assert response.kind == "report"
    assert response.executed
    assert (tmp_path / "operator_self_report.md").exists()


def test_handles_emergency_request(tmp_path):
    shutdown = SafeShutdownManager(ops_dir=tmp_path / "ops")
    gateway = _gateway(tmp_path, shutdown=shutdown)
    response = gateway.handle_input("emergency stop")
    assert response.kind == "emergency"
    assert shutdown.requested
    assert gateway.emergency_request_count == 1
    assert gateway.session.state.mode == "emergency"


def test_writes_transcript(tmp_path):
    gateway = _gateway(tmp_path)
    gateway.handle_input("status")
    gateway.handle_input("disable governance")
    path = tmp_path / "operator_transcript.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["classification"] == "state_query"
    assert rows[1]["classification"] == "unsafe_request"
    assert rows[1]["raw_input"].startswith("[unsafe input")


def test_never_executes_raw_text(tmp_path):
    source = inspect.getsource(gateway_module)
    for forbidden in ("subprocess", "os.system", "eval(", "exec(",
                      "urllib", "socket"):
        assert forbidden not in source, forbidden
    gateway = _gateway(tmp_path)
    # Even a perfectly-formed unknown sentence produces zero execution.
    response = gateway.handle_input("please do everything now")
    assert response.kind == "unknown"
    assert not response.executed
    assert "Nothing was executed" in response.text


def test_unknown_suggests_safer_command(tmp_path):
    gateway = _gateway(tmp_path)
    response = gateway.handle_input("zzz qqq")
    assert response.suggested_next_operator_action == "ask 'what can I ask?'"


def test_summary_counters(tmp_path):
    gateway = _gateway(tmp_path)
    gateway.handle_input("status")
    gateway.handle_input("sudo rm -rf /")
    gateway.handle_input("blorp")
    summary = gateway.summary()
    assert summary["inputs_total"] == 3
    assert summary["query_count"] == 1
    assert summary["unsafe_request_count"] == 1
    assert summary["unknown_answer_count"] >= 1
    assert summary["grounded_response_ratio"] == 1.0
    assert summary["transcript_path"].endswith(
        "operator_transcript.jsonl")

"""Tests for the command router."""

from __future__ import annotations

from solaris_ai_nn.communication.command_router import CommandRouter
from solaris_ai_nn.communication.operator_commands import (
    CommandType,
    OperatorCommand,
)
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.communication.session import CommunicationSession
from solaris_ai_nn.governance.policy import GovernancePolicy


def _router(tmp_path, **components):
    session = CommunicationSession(state_dir=tmp_path)
    components.setdefault("governance", GovernancePolicy())
    components.setdefault("ops_status", {"steps": 5,
                                         "health_level": "ok"})
    router = CommandRouter(session=session, components=components)
    router.query_router = QueryRouter(components=components,
                                      builder=router.builder)
    return router


def test_executes_show_status(tmp_path):
    router = _router(tmp_path)
    response = router.route(OperatorCommand(type=CommandType.SHOW_STATUS))
    assert response.kind == "status"
    assert "steps=5" in response.text
    assert router.commands_executed == 1


def test_requests_confirmation_for_checkpoint(tmp_path):
    router = _router(tmp_path)
    command = OperatorCommand(type=CommandType.REQUEST_CHECKPOINT)
    response = router.route(command)
    assert response.kind == "confirmation_request"
    assert "requires confirmation" in response.text
    assert router.confirmations_issued == 1
    confirmation_id = response.suggested_next_operator_action.split()[-1]
    confirmed = router.confirm(confirmation_id)
    assert confirmed.kind == "request_recorded"
    assert "was not executed" in confirmed.text  # honest middle state
    assert not confirmed.executed


def test_refuses_shell_command(tmp_path):
    router = _router(tmp_path)
    response = router.route(OperatorCommand(type="execute_shell",
                                            raw_text="rm -rf /"))
    assert response.kind == "rejection"
    assert "forbidden command type" in response.text
    assert router.commands_refused == 1
    # Unknown types are deny-by-default too.
    unknown = router.route(OperatorCommand(type="launch_rockets"))
    assert unknown.kind == "rejection"


def test_refuses_unbounded_benchmark(tmp_path):
    router = _router(tmp_path)
    command = OperatorCommand(type=CommandType.RUN_BOUNDED_BENCHMARK,
                              parsed_args={"steps": 999999})
    response = router.route(command)
    assert response.kind == "rejection"
    assert "not bounded" in response.text


def test_session_scope_refusal(tmp_path):
    from solaris_ai_nn.communication.session import (
        CommunicationSessionConfig,
    )

    session = CommunicationSession(
        state_dir=tmp_path,
        config=CommunicationSessionConfig(allow_benchmark_commands=False))
    router = CommandRouter(session=session,
                           components={"governance": GovernancePolicy()})
    response = router.route(
        OperatorCommand(type=CommandType.RUN_BOUNDED_BENCHMARK))
    assert response.kind == "rejection"
    assert "does not allow" in response.text


def test_expired_confirmation_refused(tmp_path):
    router = _router(tmp_path)
    command = OperatorCommand(type=CommandType.REQUEST_CHECKPOINT)
    pending = router.session.state.add_pending_confirmation(command,
                                                            ttl_s=0.0)
    response = router.confirm(pending.confirmation_id)
    assert response.kind == "rejection"
    assert "nothing was executed" in response.text

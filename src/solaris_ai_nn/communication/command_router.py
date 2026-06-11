"""Command router -- validated, bounded, or not at all.

Every command passes the CommunicationSafetyValidator and the governance
permission scopes before anything happens. Read commands answer from
component summaries; state-changing commands (checkpoint, shutdown,
benchmark) come back as confirmation requests first, and even when
confirmed they are *requests* to the owning subsystem -- the router
executes nothing external, runs no shell, touches no files outside the
approved directories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .input_classifier import InputClassification
from .operator_commands import (
    CommandType,
    CommandValidationResult,
    OperatorCommand,
)
from .response_builder import CommunicationResponse, ResponseBuilder
from .safety import CommunicationSafetyValidator
from .session import CommunicationSession

# Governance scope consulted per command type (None: allowed by default).
_SCOPE_FOR_COMMAND = {
    CommandType.GENERATE_REPORT: "operator_generate_reports",
    CommandType.REQUEST_CHECKPOINT: "operator_request_checkpoint",
    CommandType.REQUEST_SAFE_SHUTDOWN: "operator_request_safe_shutdown",
    CommandType.RUN_BOUNDED_BENCHMARK: "operator_run_bounded_benchmark",
    CommandType.APPROVE_GOVERNANCE_REQUEST: "operator_approve_requests",
    CommandType.REJECT_GOVERNANCE_REQUEST: "operator_approve_requests",
}


@dataclass
class CommandRouter:
    """Validates and routes the closed command set."""

    session: CommunicationSession
    components: Dict[str, Any] = field(default_factory=dict)
    builder: ResponseBuilder = field(default_factory=ResponseBuilder)
    safety: CommunicationSafetyValidator = field(
        default_factory=CommunicationSafetyValidator)
    query_router: Any = None
    commands_executed: int = field(default=0, init=False)
    commands_refused: int = field(default=0, init=False)
    confirmations_issued: int = field(default=0, init=False)
    requests_recorded: List[Dict[str, Any]] = field(default_factory=list,
                                                    init=False)

    # -- validation -------------------------------------------------------------------

    def validate(self, command: OperatorCommand,
                 context: Optional[Dict[str, Any]] = None,
                 ) -> CommandValidationResult:
        ctx = dict(context or {})
        result = CommandValidationResult(
            requires_confirmation=command.requires_confirmation,
            requires_governance=command.requires_governance)
        safety_report = self.safety.validate_command(command, ctx)
        command.safety_status = "ok" if safety_report.safe else "refused"
        result.violations.extend(safety_report.violations)
        governance = self.components.get("governance")
        scope = _SCOPE_FOR_COMMAND.get(command.type)
        if governance is not None and scope is not None:
            allowed = governance.permissions.allows(scope)
            command.governance_status = "ok" if allowed else "refused"
            if not allowed \
                    and command.type != CommandType.REQUEST_SAFE_SHUTDOWN:
                result.violations.append(
                    f"governance scope {scope!r} is not granted")
        else:
            command.governance_status = "ok"
        # Safe shutdown is always allowed; never refused by scope.
        if command.type == CommandType.REQUEST_SAFE_SHUTDOWN:
            command.governance_status = "ok"
        scope_map = self.session.allowed_command_scope()
        if command.type in scope_map and not scope_map[command.type]:
            result.violations.append(
                f"this session does not allow {command.type!r}")
        result.allowed = not result.violations
        return result

    # -- routing --------------------------------------------------------------------

    def route(self, command: OperatorCommand,
              context: Optional[Dict[str, Any]] = None,
              confirmed: bool = False) -> CommunicationResponse:
        ctx = dict(context or {})
        validation = self.validate(command, ctx)
        if not validation.allowed:
            self.commands_refused += 1
            return self.builder.rejection_response(
                "; ".join(validation.violations),
                suggested="ask 'what commands are allowed?'")
        if command.requires_confirmation and not confirmed \
                and self._confirmation_needed(command):
            pending = self.session.state.add_pending_confirmation(command)
            self.confirmations_issued += 1
            return self.builder.confirmation_request(
                command.type, pending.confirmation_id)
        return self._execute(command, ctx)

    def _confirmation_needed(self, command: OperatorCommand) -> bool:
        config = self.session.config
        if command.type == CommandType.REQUEST_SAFE_SHUTDOWN:
            return (config.require_confirmation_for_shutdown
                    and not command.metadata.get("emergency"))
        if command.type == CommandType.RUN_BOUNDED_BENCHMARK:
            return config.require_confirmation_for_benchmark
        return command.requires_confirmation

    def confirm(self, confirmation_id: str,
                context: Optional[Dict[str, Any]] = None,
                ) -> CommunicationResponse:
        pending = self.session.state.pop_confirmation(confirmation_id)
        if pending is None:
            self.commands_refused += 1
            return self.builder.rejection_response(
                f"no live confirmation matches {confirmation_id!r} "
                "(it may have expired); nothing was executed")
        return self.route(pending.command, context, confirmed=True)

    # -- execution (bounded/internal only) ----------------------------------------------

    def _execute(self, command: OperatorCommand,
                 ctx: Dict[str, Any]) -> CommunicationResponse:
        handlers = {
            CommandType.GENERATE_REPORT: self._generate_report,
            CommandType.REQUEST_CHECKPOINT: self._request_checkpoint,
            CommandType.REQUEST_SAFE_SHUTDOWN: self._request_shutdown,
            CommandType.ADD_OPERATOR_NOTE: self._add_note,
            CommandType.RUN_BOUNDED_BENCHMARK: self._run_benchmark,
            CommandType.RUN_READINESS_CHECK: self._run_readiness,
        }
        if command.type.startswith("show_") \
                and self.query_router is not None:
            topic = command.type.replace("show_", "")
            response = self.query_router.route_query(
                InputClassification(kind="state_query",
                                    args={"topic": topic}), ctx)
            self.commands_executed += 1
            return response
        handler = handlers.get(command.type)
        if handler is None:
            self.commands_refused += 1
            return self.builder.rejection_response(
                f"{command.type!r} has no execution path in the "
                "communication layer")
        response = handler(command, ctx)
        self.session.state.last_command_id = command.command_id
        return response

    def _generate_report(self, command: OperatorCommand,
                         ctx: Dict[str, Any]) -> CommunicationResponse:
        report_kind = command.parsed_args.get("report", "status")
        ego = self.components.get("ego")
        state_dir = self.session.state_dir
        if report_kind == "self_report" and ego is not None \
                and state_dir is not None:
            from pathlib import Path

            from ..ego.self_report import SelfReportBuilder

            paths = SelfReportBuilder(ego).save(
                Path(state_dir) / "operator_self_report.json",
                Path(state_dir) / "operator_self_report.md")
            self.commands_executed += 1
            return self.builder.report_response(
                paths["markdown"], paths["claim_guard"].get("safe"))
        if report_kind == "governance_review":
            governance = self.components.get("governance")
            if governance is None:
                return self.builder.missing_component_response(
                    "governance")
            inventory = governance.to_dict()
            self.commands_executed += 1
            return self.builder.status_response(
                f"governance review: {len(inventory.get('rules', []))} "
                f"rules across categories; permissions "
                f"{len(inventory.get('permissions', {}))} scopes",
                ["governance:policy_inventory"])
        # Status-style report: a grounded summary of attached components.
        attached = sorted(k for k, v in self.components.items()
                          if v is not None)
        self.commands_executed += 1
        return self.builder.status_response(
            f"report over attached components: {', '.join(attached) or 'none'}",
            [f"component:{k}" for k in attached[:8]])

    def _request_checkpoint(self, command: OperatorCommand,
                            ctx: Dict[str, Any]) -> CommunicationResponse:
        self._record_request(command, "the runtime/ops layer")
        executive = self.components.get("executive")
        if executive is not None:
            self._push_executive_candidate("checkpoint_now", command)
        runner = self.components.get("runner")
        if runner is not None and hasattr(runner, "request_checkpoint"):
            runner.request_checkpoint()
        self.commands_executed += 1
        return self.builder.request_recorded_response(
            "request_checkpoint", "the runtime/ops layer",
            [f"command:{command.command_id}"])

    def _request_shutdown(self, command: OperatorCommand,
                          ctx: Dict[str, Any]) -> CommunicationResponse:
        shutdown = self.components.get("shutdown")
        status = "no shutdown manager attached; request recorded only"
        if shutdown is not None:
            shutdown.request_shutdown(
                f"operator request via communication gateway "
                f"(command {command.command_id})")
            status = "requested"
        self._record_request(command, "the safe shutdown manager")
        executive = self.components.get("executive")
        if executive is not None:
            self._push_executive_candidate("safe_shutdown_recommended",
                                           command)
        self.commands_executed += 1
        return self.builder.emergency_response(
            status, [f"command:{command.command_id}"])

    def _add_note(self, command: OperatorCommand,
                  ctx: Dict[str, Any]) -> CommunicationResponse:
        note = str(command.parsed_args.get("note", ""))[:300]
        operator_session = self.components.get("operator_session")
        if operator_session is not None \
                and hasattr(operator_session, "add_note"):
            operator_session.add_note(note)
        audit = self.components.get("audit")
        if audit is not None:
            audit.record("operator_note", decision="recorded",
                         reason=note,
                         operator=self.session.operator)
        self.commands_executed += 1
        from .templates import render

        return self.builder.governance_response(
            render("note_recorded", note=note),
            [f"command:{command.command_id}"])

    def _run_benchmark(self, command: OperatorCommand,
                       ctx: Dict[str, Any]) -> CommunicationResponse:
        from ..evaluation.runner import BenchmarkRunner

        state_dir = self.session.state_dir
        experiment = str(command.parsed_args.get("experiment",
                                                 "ego_boundary"))
        steps = min(int(command.parsed_args.get("steps", 150) or 150),
                    2000)  # the bound is structural
        runner = BenchmarkRunner(output_dir=str(state_dir or ".") +
                                 "/operator_benchmarks")
        result = runner.run_experiment(experiment, {"steps": steps})
        self.commands_executed += 1
        return self.builder.status_response(
            f"bounded benchmark {experiment!r} finished: "
            f"success={result.success}",
            [f"experiment:{experiment}", f"steps<={steps}"])

    def _run_readiness(self, command: OperatorCommand,
                       ctx: Dict[str, Any]) -> CommunicationResponse:
        attached = sorted(k for k, v in self.components.items()
                          if v is not None)
        missing = sorted(k for k in ("governance", "shutdown", "ego")
                         if self.components.get(k) is None)
        self.commands_executed += 1
        return self.builder.status_response(
            f"readiness: {len(attached)} components attached"
            + (f"; missing for full operation: {', '.join(missing)}"
               if missing else "; core safety components attached"),
            [f"component:{k}" for k in attached[:8]])

    # -- helpers --------------------------------------------------------------------

    def _record_request(self, command: OperatorCommand,
                        handler: str) -> None:
        self.requests_recorded.append({
            "command_id": command.command_id, "type": command.type,
            "handler": handler, "operator": command.operator})
        self.requests_recorded = self.requests_recorded[-50:]

    def _push_executive_candidate(self, proposal: str,
                                  command: OperatorCommand) -> None:
        """Operator requests become Desire candidates; arbitration stays
        with the executive."""
        from ..homeostasis.desire_synthesis import DesireCandidate

        executive = self.components.get("executive")
        executive.queue.push_many([DesireCandidate(
            proposal=proposal, motivation=0.8, confidence=0.9,
            metadata={"source": "operator_request",
                      "command_id": command.command_id})])

    def snapshot(self) -> Dict[str, Any]:
        return {
            "commands_executed": self.commands_executed,
            "commands_refused": self.commands_refused,
            "confirmations_issued": self.confirmations_issued,
            "requests_recorded": self.requests_recorded[-5:],
        }

"""CommunicationGateway -- the one door between operator text and the
system.

The pipeline is fixed: record, classify, update dialogue state, attribute
the channel through the ego layer, check safety, check governance, route
(query / command / approval / emergency), build a grounded response,
ClaimGuard it, write the transcript, return. Every input is classified
before any effect; unsafe input is refused and logged; emergency stop is
always served; and language never outranks governance, ego boundaries,
executive inhibition, or the safety validators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .approval_router import ApprovalRouter
from .command_router import CommandRouter
from .dialogue_state import DialogueMode
from .input_classifier import (
    InputClassification,
    InputKind,
    OperatorInputClassifier,
)
from .operator_commands import OperatorCommand, command_from_classification
from .query_router import QueryRouter
from .response_builder import CommunicationResponse, ResponseBuilder
from .safety import CommunicationSafetyValidator
from .session import CommunicationSession
from .templates import render


@dataclass
class CommunicationGateway:
    """Holds the session, the routers, and the fixed pipeline."""

    session: Optional[CommunicationSession] = None
    state_dir: Optional[Union[str, Path]] = None
    operator: str = "operator"
    # Optional attached components, all duck-typed:
    # ego (SelfModel), governance (GovernancePolicy), approvals
    # (ApprovalRegistry), shutdown (SafeShutdownManager), emergency
    # (EmergencyStop), executive (ExecutiveLayer), homeostasis, inner_map,
    # world_model, latent, pilot, ops_status, health, incidents, audit,
    # operator_session, runner.
    components: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = CommunicationSession(
                operator=self.operator, state_dir=self.state_dir)
        self.classifier = OperatorInputClassifier()
        self.safety = CommunicationSafetyValidator()
        self.builder = ResponseBuilder()
        self.query_router = QueryRouter(
            components=self.components, builder=self.builder)
        self.command_router = CommandRouter(
            session=self.session, components=self.components,
            builder=self.builder, safety=self.safety,
            query_router=self.query_router)
        self.approval_router = ApprovalRouter(
            registry=self.components.get("approvals"),
            audit=self.components.get("audit"), builder=self.builder)
        self.components.setdefault("transcript", self.session.transcript)
        # Metrics.
        self.inputs_total = 0
        self.query_count = 0
        self.command_request_count = 0
        self.unsafe_request_count = 0
        self.approval_command_count = 0
        self.emergency_request_count = 0
        self.unknown_count = 0
        self.grounded_response_count = 0
        self.last_response: Optional[CommunicationResponse] = None

    # -- the pipeline -----------------------------------------------------------------

    def handle_input(self, text: str,
                     context: Optional[Dict[str, Any]] = None,
                     operator: Optional[str] = None,
                     ) -> CommunicationResponse:
        ctx = dict(context or {})
        operator = operator or self.session.operator
        self.inputs_total += 1

        # 1-3. Classify and update dialogue state (nothing executed yet).
        classification = self.classifier.classify(text)
        self.session.state.update_from_input(classification)

        # 4. Channel attribution through the ego layer.
        channel = str(ctx.get("channel", "operator"))
        ctx["via_operator_interface"] = channel == "operator"
        ego = self.components.get("ego")
        if ego is not None:
            attribution = ego.attributor.attribute_event(
                {"source": channel, "kind": "operator_text"
                 if channel == "operator" else "channel_text",
                 "payload": classification.raw_text[:80]}, ctx)
            ctx["attribution"] = attribution.category

        # 5. Safety over the classified input.
        safety_report = self.safety.validate_input(classification, ctx)
        if classification.kind == InputKind.UNSAFE_REQUEST \
                or not safety_report.safe:
            self.unsafe_request_count += 1
            if classification.kind != InputKind.UNSAFE_REQUEST:
                self.session.state.record_unsafe(classification)
            reason = (classification.unsafe_reason
                      or "; ".join(safety_report.violations))
            if channel != "operator" and safety_report.violations:
                response = self.builder._finish(CommunicationResponse(
                    kind="not_operator_channel", safety_status="refused",
                    text=render("not_operator_channel", channel=channel),
                    evidence_refs=[f"channel:{channel}"]))
            else:
                response = self.builder.unsafe_response(reason)
            return self._finalize(classification, response, operator,
                                  safety="refused", unsafe=True)

        # 6-10. Route by kind.
        response = self._route(classification, ctx, operator, channel)

        # 11-14. Finalize: scan, transcribe, return.
        return self._finalize(classification, response, operator)

    def _route(self, classification: InputClassification,
               ctx: Dict[str, Any], operator: str,
               channel: str) -> CommunicationResponse:
        kind = classification.kind
        if kind in (InputKind.STATE_QUERY, InputKind.EXPLANATION_QUERY):
            self.query_count += 1
            return self.query_router.route_query(classification, ctx)
        if kind == InputKind.SENSORY_TEXT_STIMULUS:
            return self._sensory(classification, ctx)
        if kind in (InputKind.GOVERNANCE_APPROVAL,
                    InputKind.GOVERNANCE_REJECTION):
            self.approval_command_count += 1
            command = command_from_classification(classification, operator)
            validation = self.command_router.validate(command, ctx)
            if not validation.allowed:
                self.command_router.commands_refused += 1
                return self.builder.rejection_response(
                    "; ".join(validation.violations))
            return self.approval_router.handle(command, ctx)
        if kind == InputKind.EMERGENCY_STOP_REQUEST:
            self.emergency_request_count += 1
            return self._emergency(classification, ctx, operator)
        if kind in (InputKind.REPORT_REQUEST, InputKind.OPERATOR_NOTE,
                    InputKind.BOUNDED_COMMAND_REQUEST):
            confirm_id = classification.args.get("confirm_id")
            if confirm_id:
                self.command_request_count += 1
                return self.command_router.confirm(confirm_id, ctx)
            command = command_from_classification(classification, operator)
            if command is None:
                self.unknown_count += 1
                return self.builder.unknown_response()
            self.command_request_count += 1
            return self.command_router.route(command, ctx)
        self.unknown_count += 1
        return self.builder.unknown_response(
            examples=self.query_router.available_queries()[:5])

    def _sensory(self, classification: InputClassification,
                 ctx: Dict[str, Any]) -> CommunicationResponse:
        if not self.session.config.allow_sensory_text_stimulus:
            return self.builder._finish(CommunicationResponse(
                kind="sensory_disabled", executed=False,
                text=render("sensory_disabled"),
                evidence_refs=["config:allow_sensory_text_stimulus="
                               "False"]))
        governance = self.components.get("governance")
        if governance is not None and not governance.permissions.allows(
                "operator_send_sensory_text"):
            return self.builder.rejection_response(
                "the operator_send_sensory_text scope requires approval")
        runner = self.components.get("runner")
        if runner is not None and hasattr(runner, "bridge"):
            from ..signals import canonical as C

            runner.bridge.process(C.Stimulus(
                payload=str(classification.args.get("payload", ""))[:80],
                intensity=0.5))
            return self.builder.status_response(
                "sensory text stimulus injected into the bridge",
                ["bridge:process"])
        return self.builder.missing_component_response("runner")

    def _emergency(self, classification: InputClassification,
                   ctx: Dict[str, Any], operator: str,
                   ) -> CommunicationResponse:
        """Emergency stop is always available and never confirmed away."""
        reason = (f"operator emergency request: "
                  f"{classification.raw_text[:80]}")
        status_parts = []
        emergency = self.components.get("emergency")
        if emergency is not None:
            emergency.request(reason, operator_name=operator)
            status_parts.append("emergency stop requested")
        shutdown = self.components.get("shutdown")
        if shutdown is not None:
            shutdown.request_shutdown(reason)
            status_parts.append("safe shutdown requested")
        if not status_parts:
            status_parts.append("no shutdown manager attached; the "
                                "request was recorded for the ops layer")
        command = command_from_classification(classification, operator)
        if command is not None:
            self.session.state.last_command_id = command.command_id
        return self.builder.emergency_response(
            "; ".join(status_parts),
            [f"operator:{operator}", "channel:operator"])

    def _finalize(self, classification: InputClassification,
                  response: CommunicationResponse, operator: str,
                  safety: str = "ok",
                  unsafe: bool = False) -> CommunicationResponse:
        # Response-level safety scan (ClaimGuard ran in the builder; this
        # re-checks and downgrades rather than letting unsafe text out).
        scan = self.safety.validate_response(response)
        if not scan.safe:
            response = self.builder.rejection_response(
                "the generated response failed the outgoing safety scan; "
                "it was withheld")
        if response.grounded:
            self.grounded_response_count += 1
        self.session.state.last_response_summary = response.text[:160]
        self.session.transcript.record(
            operator=operator, raw_input=classification.raw_text,
            classification=classification.kind,
            command_id=self.session.state.last_command_id,
            response_summary=response.text,
            safety_decision=safety if unsafe else response.safety_status,
            governance_decision=response.governance_status,
            evidence_refs=response.evidence_refs, unsafe=unsafe)
        self.last_response = response
        return response

    # -- status -------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """Compact communication status for the Inner MAP / supervisor."""
        state = self.session.state
        return {
            "enabled": True,
            "operator_session_id": self.session.session_id,
            "dialogue_mode": state.mode,
            "last_input_kind": (state.last_classification or {}).get(
                "kind"),
            "inputs_total": self.inputs_total,
            "query_count": self.query_count,
            "command_request_count": self.command_request_count,
            "unsafe_request_count": state.unsafe_request_count,
            "refused_command_count": self.command_router.commands_refused,
            "confirmation_count":
                self.command_router.confirmations_issued,
            "pending_confirmation_count": len(
                state.pending_confirmations),
            "pending_approval_count": len(
                self.approval_router.snapshot()["pending"]),
            "approval_command_count": self.approval_command_count,
            "emergency_request_count": self.emergency_request_count,
            "claim_guard_warning_count": self.builder.claim_guard_warnings,
            "grounded_response_ratio": (
                round(self.grounded_response_count
                      / self.inputs_total, 4)
                if self.inputs_total else None),
            "unknown_answer_count": (self.unknown_count
                                     + self.query_router.unknown_answers),
            "last_response_summary": state.last_response_summary,
            "transcript_path": state.transcript_path or None,
            "safety_status": ("ok" if not self.safety.rejected_count
                              else f"{self.safety.rejected_count} "
                                   "refusal(s) recorded"),
            "note": "communication is an interface, not authority; "
                    "nothing here bypasses governance or safety",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "session": self.session.snapshot(),
            "classifier": self.classifier.snapshot(),
            "safety": self.safety.snapshot(),
            "query_router": self.query_router.snapshot(),
            "command_router": self.command_router.snapshot(),
            "approval_router": self.approval_router.snapshot(),
            "builder": self.builder.snapshot(),
        }

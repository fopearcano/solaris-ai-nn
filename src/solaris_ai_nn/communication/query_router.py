"""Query router -- operator questions answered from existing machinery.

State queries read component summaries (ops, Inner MAP, world model,
homeostasis, executive, ego, governance, pilot, latent, evaluation);
explanation queries are delegated to the existing ego / executive /
homeostasis query interfaces; communication meta-queries (what can be
asked, what is allowed/forbidden, pending approvals, transcript summary,
evidence support) are answered locally. Missing components produce an
honest "not attached" answer, never an invented one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .input_classifier import InputClassification, InputKind
from .operator_commands import FORBIDDEN_COMMAND_TYPES, CommandType
from .response_builder import CommunicationResponse, ResponseBuilder

AVAILABLE_QUERIES = (
    "status", "health", "show inner map", "show world model",
    "show current needs", "show current plan", "show boundaries",
    "show governance", "show pilot", "show latent",
    "what happened last?", "why was this action selected?",
    "why was this inhibited?", "why no action?",
    "what can I ask?", "what commands are allowed?",
    "what commands are forbidden?", "what approvals are pending?",
    "show transcript summary", "what evidence supports this answer?",
    "what is the system sampling?", "why did it look there?",
    "what is the current attention focus?", "what uncertainty is highest?",
    "is curiosity overriding safety?",
    "what hypotheses exist?", "what is the top hypothesis?",
    "what was tested?", "what was falsified?", "what remains unknown?",
    "why was a test blocked?", "did testing reduce mysterium?",
)


def _summarize(value: Any, limit: int = 6) -> "tuple[str, List[str]]":
    """(compact text, evidence refs) for a component summary."""
    if value is None:
        return ("no data recorded", [])
    if hasattr(value, "summary"):
        value = value.summary()
    elif hasattr(value, "snapshot"):
        value = value.snapshot()
    if isinstance(value, dict):
        parts = []
        refs = []
        for key, item in list(value.items())[:limit]:
            if isinstance(item, (dict, list)):
                item = (f"{len(item)} entries" if isinstance(item, list)
                        else f"{len(item)} fields")
            parts.append(f"{key}={item}")
            refs.append(f"field:{key}")
        return ("; ".join(parts), refs)
    return (str(value)[:200], ["value"])


@dataclass
class QueryRouter:
    """Routes state/explanation/meta queries to their owners."""

    components: Dict[str, Any] = field(default_factory=dict)
    builder: ResponseBuilder = field(default_factory=ResponseBuilder)
    queries_routed: int = field(default=0, init=False)
    unknown_answers: int = field(default=0, init=False)
    last_evidence: List[str] = field(default_factory=list, init=False)

    # -- routing --------------------------------------------------------------------

    def route_query(self, classification: InputClassification,
                    context: Optional[Dict[str, Any]] = None,
                    ) -> CommunicationResponse:
        self.queries_routed += 1
        if classification.kind == InputKind.EXPLANATION_QUERY:
            response = self._explanation(classification)
        else:
            response = self._state(classification)
        self.last_evidence = list(response.evidence_refs)
        return response

    def _state(self, classification: InputClassification,
               ) -> CommunicationResponse:
        topic = classification.args.get("topic", "")
        meta = {
            "supported_queries": self._supported,
            "allowed_commands": self._allowed_commands,
            "forbidden_commands": self._forbidden_commands,
            "pending_approvals": self._pending_approvals,
            "transcript": self._transcript_summary,
            "evidence_support": self._evidence_support,
        }
        if topic in meta:
            return meta[topic]()
        component_keys = {
            "status": "ops_status", "health": "health",
            "inner_map": "inner_map", "world_model": "world_model",
            "homeostasis": "homeostasis", "executive": "executive",
            "ego_boundaries": "ego", "governance": "governance",
            "pilot": "pilot", "latent": "latent", "sidecar": "sidecar",
            "incidents": "incidents", "run_registry": "run_registry",
            "last_event": "last_event",
            "active_perception": "active_perception",
            "hypothesis": "hypothesis",
        }
        key = component_keys.get(topic)
        if key is None:
            self.unknown_answers += 1
            return self.builder.unknown_response(
                examples=list(AVAILABLE_QUERIES[:5]))
        component = self.components.get(key)
        if component is None and topic == "health":
            component = self.components.get("ops_status")
        if component is None:
            self.unknown_answers += 1
            return self.builder.missing_component_response(key)
        if topic == "ego_boundaries" and hasattr(component, "boundaries"):
            text, refs = _summarize(component.boundaries.snapshot())
        else:
            text, refs = _summarize(component)
        if topic == "health":
            return self.builder.health_response(text, refs)
        return self.builder.status_response(text, refs)

    def _explanation(self, classification: InputClassification,
                     ) -> CommunicationResponse:
        question = classification.args.get("question",
                                           classification.raw_text)
        for source, interface in self._query_interfaces():
            result = interface.answer(question)
            if result.answered and result.confidence >= 0.5:
                return self.builder.explanation_response(
                    result.text, [f"query_interface:{source}"],
                    confidence=result.confidence)
        self.unknown_answers += 1
        return self.builder.no_evidence_response()

    def _query_interfaces(self) -> List["tuple[str, Any]"]:
        interfaces: List = []
        ego = self.components.get("ego")
        if ego is not None:
            from ..ego.self_report import EgoQueryInterface

            interfaces.append(("ego", EgoQueryInterface(ego)))
        executive = self.components.get("executive")
        if executive is not None:
            from ..executive.reports import ExecutiveQueryInterface

            interfaces.append(("executive",
                               ExecutiveQueryInterface(executive)))
        homeostasis = self.components.get("homeostasis")
        if homeostasis is not None:
            from ..homeostasis.reports import HomeostasisQueryInterface

            interfaces.append(("homeostasis",
                               HomeostasisQueryInterface(homeostasis)))
        active_perception = self.components.get("active_perception")
        if active_perception is not None:
            from ..active_perception.reports import (
                ActivePerceptionQueryInterface,
            )

            interfaces.append(("active_perception",
                               ActivePerceptionQueryInterface(
                                   active_perception)))
        hypothesis = self.components.get("hypothesis")
        if hypothesis is not None:
            from ..hypothesis.reports import HypothesisQueryInterface

            interfaces.append(("hypothesis",
                               HypothesisQueryInterface(hypothesis)))
        return interfaces

    # -- meta queries -----------------------------------------------------------------

    def _supported(self) -> CommunicationResponse:
        return self.builder.status_response(
            "supported queries: " + "; ".join(AVAILABLE_QUERIES),
            ["communication:available_queries"])

    def _allowed_commands(self) -> CommunicationResponse:
        return self.builder.status_response(
            "allowed command types: " + ", ".join(CommandType.ALL),
            ["communication:command_types"])

    def _forbidden_commands(self) -> CommunicationResponse:
        return self.builder.status_response(
            "forbidden command types (these do not exist here): "
            + ", ".join(FORBIDDEN_COMMAND_TYPES),
            ["communication:forbidden_command_types"])

    def _pending_approvals(self) -> CommunicationResponse:
        approvals = self.components.get("approvals")
        if approvals is None:
            return self.builder.missing_component_response("approvals")
        pending = approvals.list_pending()
        if not pending:
            return self.builder.status_response(
                "no approval requests are pending",
                ["approvals:pending=0"])
        parts = [f"{r.request_id} ({r.requested_permission}, "
                 f"risk {r.risk_level})" for r in pending[:5]]
        return self.builder.status_response(
            "pending approvals: " + "; ".join(parts),
            [f"approval:{r.request_id}" for r in pending[:5]])

    def _transcript_summary(self) -> CommunicationResponse:
        transcript = self.components.get("transcript")
        if transcript is None:
            return self.builder.missing_component_response("transcript")
        text, refs = _summarize(transcript.summary())
        return self.builder.status_response(text, refs)

    def _evidence_support(self) -> CommunicationResponse:
        if not self.last_evidence:
            return self.builder.no_evidence_response()
        return self.builder.status_response(
            "the previous answer was grounded in: "
            + ", ".join(self.last_evidence[:8]),
            list(self.last_evidence[:8]))

    # -- views --------------------------------------------------------------------

    def available_queries(self) -> List[str]:
        return list(AVAILABLE_QUERIES)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "queries_routed": self.queries_routed,
            "unknown_answers": self.unknown_answers,
            "components_attached": sorted(
                k for k, v in self.components.items() if v is not None),
            "available_queries": list(AVAILABLE_QUERIES),
        }

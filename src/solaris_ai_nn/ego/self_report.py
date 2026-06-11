"""Self-report -- the self-model in careful words, ClaimGuard-scanned.

The report covers identity anchors, continuity, perspective, boundaries,
classification and attribution summaries, the body schema, action
authority, unresolved warnings, unknowns, and mandatory limitations. The
query interface answers eight fixed questions in safe vocabulary ("the
self-model classifies…", "runtime continuity is uncertain because…") --
never consciousness, personhood, or first-person claims.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

from ..language.query import normalize
from ..language.reporting import ExperimentReportBuilder, SessionReport
from ..language.schemas import QueryResult

EGO_LIMITATIONS = [
    "Operational identity means runtime continuity over recorded anchors; "
    "no personhood, consciousness, or metaphysical self is claimed or "
    "supported.",
    "The self-model observes and classifies; it executes nothing, grants "
    "nothing, and overrides neither governance nor emergency stop.",
    "Classifications carry explicit confidence; unknown sources are "
    "reported as unknown, never guessed.",
    "Offline replay and counterfactual output are simulated evidence and "
    "are never reclassified as observation.",
    "Suggestions remain suggestions; the self-model records no committed "
    "actions of its own because it has none.",
]


class SelfReportBuilder:
    """Builds the self-report from a SelfModel."""

    def __init__(self, self_model: Any) -> None:
        self.self_model = self_model

    def build(self) -> SessionReport:
        model = self.self_model
        snap = model.snapshot()
        summary = snap["summary"]
        report = (
            ExperimentReportBuilder(title="Self-model report")
            .add_metadata(
                perspective=summary["perspective"],
                identity_continuity=summary["identity_continuity"],
                action_authority=summary["action_authority"])
            .add_section("identity_anchors", snap["identity"])
            .add_section("continuity_score", {
                "identity_continuity": summary["identity_continuity"],
                "identity_confidence": summary["identity_confidence"],
                "last_assessment": snap["continuity"]["last"]})
            .add_section("current_perspective", snap["perspective"])
            .add_section("boundary_status", snap["boundaries"])
            .add_section("classification_summary",
                         summary["classification_counts"])
            .add_section("evidence_summary", {
                "comparator": snap["comparator"],
                "note": "simulated and offline evidence stays labelled as "
                        "such"})
            .add_section("attribution_summary", snap["attribution"])
            .add_section("body_schema", snap["body"])
            .add_section("action_authority_status", {
                "authority": summary["action_authority"],
                "actions_allowed":
                    model.perspective.state.actions_allowed,
                "scope": model.perspective.state.action_scope})
            .add_section("unresolved_identity_warnings",
                         summary["identity_warnings"]
                         or ["no unresolved identity warnings"])
            .add_section("unknowns",
                         (model.last_snapshot.unknowns
                          if model.last_snapshot else [])
                         or ["no recorded unknowns this update"])
            .add_section("safety_status", snap["safety"])
            .add_section("llm_adapter_status", {
                **dict(getattr(model, "llm_status",
                               {"enabled": False})),
                "authority": False,
                "note": "any LLM output is a validated paraphrase of "
                        "grounded text, never primary evidence"})
        )
        for limitation in EGO_LIMITATIONS:
            report.add_limitation(limitation)
        return report.build()

    def to_dict(self) -> Dict[str, Any]:
        return self.build().to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        return self.build().to_markdown()

    def save(self, json_path: Union[str, Path],
             md_path: Union[str, Path]) -> Dict[str, Any]:
        """Persist via the language layer; ClaimGuard and the identity
        scan both run before anything is written."""
        from ..language.serialization import save_report

        markdown = self.to_markdown()
        identity_report = self.self_model.safety.validate_identity_claim(
            markdown)
        if not identity_report.safe:
            raise ValueError("self-report blocked: "
                             + "; ".join(identity_report.violations))
        scan = save_report(self.build(), json_path, md_path)
        result = {"json": str(json_path), "markdown": str(md_path),
                  "claim_guard": scan.to_dict()}
        if hasattr(self.self_model, "narrative"):
            self.self_model.narrative.add(
                "self_report_generated",
                evidence=[f"claim_guard_safe:{scan.to_dict().get('safe')}"],
                path=str(md_path))
        return result


class EgoQueryInterface:
    """Eight fixed queries answered in safe vocabulary."""

    def __init__(self, self_model: Any) -> None:
        self.self_model = self_model
        self._handlers: Dict[str, Callable[..., "tuple[str, float]"]] = {
            "what is the current perspective": self._perspective,
            "is this event internal or external": self._internal_external,
            "was this evidence observed or simulated": self._evidence,
            "what boundaries are active": self._boundaries,
            "what is the identity continuity score": self._continuity,
            "what action authority exists": self._authority,
            "why was this classified as counterfactual":
                self._counterfactual,
            "what is the self-model summary": self._summary,
        }

    def supported_queries(self) -> List[str]:
        return sorted(self._handlers)

    def answer(self, query: str, event: Any = None) -> QueryResult:
        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence = (handler(event)
                            if handler in (self._internal_external,
                                           self._evidence,
                                           self._counterfactual)
                            else handler())
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, confidence=confidence)

    # -- handlers ---------------------------------------------------------------

    def _perspective(self) -> "tuple[str, float]":
        state = self.self_model.perspective.state
        return (f"The current perspective is {state.mode!r} because: "
                f"{state.reason}. Evidence produced under it counts as "
                f"{state.evidence_status!r}; actions are "
                f"{'allowed at scope ' + repr(state.action_scope) if state.actions_allowed else 'not allowed'}. "
                "A perspective is a recorded operating mode, not a point "
                "of view in any experiential sense.", 0.9)

    def _internal_external(self, event: Any) -> "tuple[str, float]":
        if event is None:
            counts = self.self_model.classification_counts
            return ("No event was provided; the running classification "
                    f"counts are {counts}. Pass an event to classify it.",
                    0.5)
        c = self.self_model.classify_event(event)
        return (f"The self-model classifies the event as {c.origin!r} "
                f"(attributed to {c.attribution!r}, confidence "
                f"{c.confidence:.2f}). " + "; ".join(c.reasons[:2]) + ".",
                max(0.4, c.confidence))

    def _evidence(self, event: Any) -> "tuple[str, float]":
        if event is None:
            return ("No event was provided; evidence status depends on "
                    "the event and the active perspective.", 0.4)
        c = self.self_model.classify_event(event)
        return (f"The evidence status is {c.evidence_status!r}: "
                + ("offline replay or counterfactual output stays "
                   "simulated evidence"
                   if c.simulated else
                   "it was recorded as live observation"
                   if c.evidence_status == "observed" else
                   "the source gives no basis to call it observed, so it "
                   "is reported as unknown") + ".",
                max(0.4, c.confidence))

    def _boundaries(self) -> "tuple[str, float]":
        snap = self.self_model.boundaries.snapshot()
        violated = snap["violated"]
        return (f"The boundary registry reports {snap['boundary_count']} "
                f"active boundaries with {snap['violations_total']} "
                "recorded violation(s)"
                + (f"; currently violated: {', '.join(violated)}"
                   if violated else "; none currently violated")
                + ". Hard rules include: " + "; ".join(
                    snap["hard_rules"][:3]) + ".", 0.9)

    def _continuity(self) -> "tuple[str, float]":
        identity = self.self_model.identity
        text = (f"The identity continuity score is "
                f"{identity.continuity_score:.2f} with confidence "
                f"{identity.identity_confidence:.2f}.")
        if identity.identity_warnings:
            text += (" Runtime continuity is uncertain because: "
                     + identity.identity_warnings[-1] + ".")
        else:
            text += (" No anchor mismatches are recorded; this measures "
                     "runtime continuity, nothing more.")
        return (text, 0.9)

    def _authority(self) -> "tuple[str, float]":
        authority = self.self_model.action_authority()
        return (f"The action authority is {authority!r}: simulated "
                "actions may execute only inside the simulation, internal "
                "maintenance is suggestion-gated, and real-world "
                "actuation is structurally forbidden.", 0.9)

    def _counterfactual(self, event: Any) -> "tuple[str, float]":
        if event is None:
            return ("No event was provided. Counterfactual classification "
                    "comes from the counterfactual source label or an "
                    "active counterfactual context, and it is never "
                    "relabelled as observation.", 0.6)
        c = self.self_model.classify_event(event)
        if c.evidence_status != "counterfactual":
            return (f"The event was not classified as counterfactual; its "
                    f"evidence status is {c.evidence_status!r}.", 0.7)
        return ("The event was classified as counterfactual because its "
                "source or context marks it as what-if simulation output; "
                "the counterfactual boundary keeps it from ever counting "
                "as real observation.", 0.9)

    def _summary(self) -> "tuple[str, float]":
        s = self.self_model.summary()
        return (f"The self-model reports perspective {s['perspective']!r}, "
                f"identity continuity {s['identity_continuity']:.2f}, "
                f"{s['boundary_violation_count']} boundary violation(s), "
                f"action authority {s['action_authority']!r}, and "
                f"classification counts {s['classification_counts']}. "
                "It is an operational continuity/boundary model; no "
                "consciousness or personhood claim is made.", 0.9)

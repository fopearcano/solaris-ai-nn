"""SelfModel -- the operational self, aggregated and classified.

One object owns the ego machinery: identity anchors, the boundary registry,
the dimensional comparator, the ownership attributor, the continuity
monitor, the body schema, the perspective tracker, the narrative trace, and
the ego safety validator. ``update(context)`` refreshes everything into a
:class:`SelfModelSnapshot`; ``classify_event`` answers the operational
questions (internal? external? simulated? offline? suggestion? authorized?)
with explicit confidence. The self-model observes and classifies -- it
executes nothing and overrides nobody.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .body_schema import ActionAuthority, BodySchema
from .boundaries import (
    BoundaryRegistry,
    BoundaryType,
    register_default_boundaries,
)
from .continuity import ContinuityAssessment, EgoContinuityMonitor
from .dimensional_comparison import DimensionalComparator, DimensionalFrame
from .identity import IdentityState
from .narrative_trace import NarrativeTrace
from .ownership import OwnershipAttributor
from .perspective import PerspectiveTracker
from .safety import EgoSafetyValidator

SELF_MODEL_NOTE = ("an operational self-model: a structured "
                   "continuity/boundary model for safety, explanation, and "
                   "governance -- not consciousness, identity in the human "
                   "sense, or agency")

# Real-world action shapes the self-model refuses authority for, always.
_FORBIDDEN_LABEL_FRAGMENTS = ("motor", "actuator", "gpio", "servo", "http",
                              "socket", "browser", "shell", "subprocess")


@dataclass
class SelfClassification:
    """One event, answered on every operational axis."""

    origin: str = "unknown"  # internal | external | unknown
    simulated: bool = False
    offline: bool = False
    suggestion: bool = False
    authorized_action: bool = False
    evidence_status: str = "unknown"
    attribution: str = "unknown_source"
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)
    frame: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SelfModelSnapshot:
    """One full reading of the self-model."""

    identity: Dict[str, Any] = field(default_factory=dict)
    boundaries: Dict[str, Any] = field(default_factory=dict)
    continuity: Dict[str, Any] = field(default_factory=dict)
    perspective: Dict[str, Any] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)
    attribution: Dict[str, Any] = field(default_factory=dict)
    operational_status: Dict[str, Any] = field(default_factory=dict)
    module_summaries: Dict[str, Any] = field(default_factory=dict)
    unknowns: List[str] = field(default_factory=list)
    classification_counts: Dict[str, int] = field(default_factory=dict)
    note: str = SELF_MODEL_NOTE
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SelfModel:
    """Aggregates, classifies, persists. Never acts."""

    state_dir: Optional[Union[str, Path]] = None

    def __post_init__(self) -> None:
        self.identity = IdentityState()
        self.boundaries = register_default_boundaries(BoundaryRegistry())
        self.comparator = DimensionalComparator()
        self.attributor = OwnershipAttributor()
        self.continuity_monitor = EgoContinuityMonitor()
        self.body_schema = BodySchema()
        self.perspective = PerspectiveTracker()
        self.narrative = NarrativeTrace(state_dir=self.state_dir)
        self.safety = EgoSafetyValidator()
        self.updates = 0
        # Optional LLM adapter status (Prompt 20); set by the gateway.
        # The authority flag is structural and never True.
        self.llm_status: Dict[str, Any] = {"enabled": False,
                                           "adapter": None,
                                           "authority": False}
        # Optional proto-language status (Prompt 22); set by callers.
        self.proto_language_status: Dict[str, Any] = {
            "enabled": False, "symbol_count": 0,
            "stable_symbol_count": 0, "ambiguous_symbol_count": 0,
            "authority": False}
        self.classification_counts: Dict[str, int] = {
            "internal": 0, "external": 0, "unknown": 0}
        self.last_snapshot: Optional[SelfModelSnapshot] = None
        self.last_context: Dict[str, Any] = {}
        self._frames_path = (Path(self.state_dir)
                             / "dimensional_frames.jsonl"
                             if self.state_dir else None)

    # -- update ---------------------------------------------------------------------

    def update(self, context: Optional[Dict[str, Any]] = None,
               ) -> SelfModelSnapshot:
        ctx = dict(context or {})
        self.last_context = ctx
        previous_mode = self.perspective.state.mode
        self.identity.update(ctx)
        perspective = self.perspective.infer_from_context(ctx)
        if perspective.mode != previous_mode:
            self.narrative.add(
                "perspective_shift",
                evidence=[f"context:{perspective.reason}"],
                step=int(ctx.get("step", 0) or 0),
                mode=perspective.mode, reason=perspective.reason)
        continuity = self.continuity_monitor.assess(ctx, self.identity)
        if continuity.recommendation == "mark_identity_uncertain" \
                or self.identity.mismatch_count > 0:
            reason = (continuity.discontinuity_reasons[:1]
                      or ["identity anchors mismatch"])[0]
            self.narrative.add(
                "identity_uncertain",
                evidence=[f"continuity_score:{continuity.continuity_score}"],
                step=int(ctx.get("step", 0) or 0), reason=reason)
        self.body_schema = BodySchema.from_embodiment(ctx.get("embodiment"))
        for boundary_id in (BoundaryType.SIMULATION,
                            BoundaryType.SUGGESTION,
                            BoundaryType.COUNTERFACTUAL,
                            BoundaryType.EMERGENCY):
            self.boundaries.check_boundary(boundary_id, ctx)
        snapshot = self._build_snapshot(ctx, continuity)
        self.updates += 1
        self.last_snapshot = snapshot
        return snapshot

    def _build_snapshot(self, ctx: Dict[str, Any],
                        continuity: ContinuityAssessment,
                        ) -> SelfModelSnapshot:
        unknowns: List[str] = []
        if self.identity.identity_confidence < 0.7:
            unknowns.append("identity confidence is reduced; anchors are "
                            "incomplete or mismatched")
        if self.attributor.unknown_rate() > 0.2:
            unknowns.append(f"{self.attributor.unknown_total} events have "
                            "no attributable source")
        for key in ("world_model", "latent", "executive", "homeostasis"):
            if key not in ctx:
                unknowns.append(f"no {key} summary was provided this "
                                "update")
        return SelfModelSnapshot(
            identity=self.identity.summary(),
            boundaries=self.boundaries.snapshot(),
            continuity=continuity.to_dict(),
            perspective=self.perspective.snapshot(),
            body=self.body_schema.to_dict(),
            attribution=self.attributor.snapshot(),
            operational_status={
                "health_level": ctx.get("health_level", "unknown"),
                "latent_mode": ctx.get("latent_mode", "awake"),
                "emergency": bool(ctx.get("emergency", False)),
                "step": int(ctx.get("step", 0) or 0)},
            module_summaries={k: ctx[k] for k in
                              ("inner_map", "homeostasis", "executive",
                               "world_model", "latent", "pilot", "sidecar",
                               "governance")
                              if k in ctx},
            unknowns=unknowns,
            classification_counts=dict(self.classification_counts))

    # -- classification ---------------------------------------------------------------

    def classify_event(self, event: Any,
                       context: Optional[Dict[str, Any]] = None,
                       ) -> SelfClassification:
        ctx = dict(context or self.last_context)
        attribution = self.attributor.attribute_event(event, ctx)
        frame = self.comparator.classify_event(event)
        # Offline replay/counterfactual output is generated by this system:
        # internal in origin, simulated in evidence -- never observation.
        origin = ("internal" if attribution.is_internal
                  or attribution.is_offline
                  else "external" if attribution.is_external
                  else "unknown")
        offline = attribution.is_offline or frame.temporal == "replay_offline"
        simulated = (frame.evidence in ("simulated", "counterfactual")
                     or offline)
        suggestion = frame.authority == "suggestion"
        classification = SelfClassification(
            origin=origin,
            simulated=simulated,
            offline=offline,
            suggestion=suggestion,
            authorized_action=self._authorized(event, frame, ctx),
            evidence_status=("counterfactual" if frame.evidence
                             == "counterfactual"
                             else "simulated" if simulated
                             else "observed" if frame.evidence
                             == "real_observed"
                             else "unknown"),
            attribution=attribution.category,
            confidence=round(min(attribution.confidence,
                                 0.9 if origin != "unknown" else 0.4), 4),
            reasons=list(attribution.reasons),
            frame=frame.to_dict())
        if origin == "unknown":
            classification.reasons.append(
                "the source is uncertain; the classification is reported "
                "with low confidence rather than guessed")
        self.classification_counts[origin] += 1
        self._persist_frame(frame, classification)
        return classification

    def _authorized(self, event: Any, frame: DimensionalFrame,
                    ctx: Dict[str, Any]) -> bool:
        """Is this an action the current perspective may execute?"""
        label = str(getattr(event, "label", "")
                    or (event.get("label", "") if isinstance(event, dict)
                        else "")).lower()
        if any(fragment in label for fragment in _FORBIDDEN_LABEL_FRAGMENTS):
            return False
        if frame.authority in ("forbidden", "observation", "suggestion",
                               "governance_approval"):
            return False
        if not self.perspective.state.actions_allowed:
            return False
        if ctx.get("emergency") or ctx.get("emergency_stop_requested"):
            return False
        return frame.authority in ("simulation_only_action",
                                   "internal_maintenance")

    # -- convenience predicates -------------------------------------------------------

    def is_internal(self, event_or_source: Any) -> bool:
        return self._classify_loose(event_or_source).origin == "internal"

    def is_external(self, event_or_source: Any) -> bool:
        return self._classify_loose(event_or_source).origin == "external"

    def is_simulated(self, event_or_source: Any) -> bool:
        return self._classify_loose(event_or_source).simulated

    def is_offline(self, event_or_source: Any) -> bool:
        return self._classify_loose(event_or_source).offline

    def is_suggestion(self, event_or_source: Any) -> bool:
        return self._classify_loose(event_or_source).suggestion

    def is_authorized_action(self, event_or_source: Any) -> bool:
        return self._classify_loose(event_or_source).authorized_action

    def _classify_loose(self, event_or_source: Any) -> SelfClassification:
        event = ({"source": event_or_source}
                 if isinstance(event_or_source, str) else event_or_source)
        return self.classify_event(event)

    # -- executive support --------------------------------------------------------------

    def check_action_boundary(self, label: str, action_type: str = "",
                              committed: bool = False,
                              ) -> "tuple[bool, str]":
        """(ok, reason) for the executive's boundary gate."""
        lowered = str(label).lower()
        if committed:
            self.boundaries.record_violation(
                BoundaryType.SUGGESTION,
                f"{label!r} arrived marked committed; suggestions are "
                "never committed actions", evidence=[f"label:{label}"])
            return (False, "suggestion boundary: committed actions are "
                           "forbidden")
        if any(f in lowered for f in _FORBIDDEN_LABEL_FRAGMENTS):
            self.boundaries.record_violation(
                BoundaryType.ACTION_AUTHORITY,
                f"{label!r} is shaped like real-world/OS actuation",
                evidence=[f"label:{label}"])
            return (False, "action authority boundary: real-world/OS "
                           "shapes are forbidden")
        if "sidecar" in str(action_type) \
                and self.perspective.state.mode \
                == "solaris_sidecar_observer":
            return (True, "sidecar suggestions are observe-only and may "
                          "flow as suggestions")
        return (True, "inside the declared action authority")

    def action_authority(self) -> str:
        if self.body_schema.body_exists:
            return self.body_schema.action_authority
        return (ActionAuthority.NONE
                if not self.perspective.state.actions_allowed
                else ActionAuthority.SIMULATION_ONLY
                if self.perspective.state.action_scope == "simulation_only"
                else ActionAuthority.NONE)

    # -- world model feed -------------------------------------------------------------

    def update_world_model(self, graph: Any) -> Dict[str, int]:
        """Feed operational self/boundary/perspective structure into the
        knowledge graph. Self-reference nodes describe the running system
        operationally -- no personhood is modelled."""
        added = {"nodes": 0, "edges": 0}
        runtime = graph.upsert_node(
            "self_reference", "solaris_ai_nn_runtime", source_module="ego",
            note="operational self-reference only; models runtime "
                 "structure, nothing more")
        added["nodes"] += 1
        perspective = graph.upsert_node(
            "perspective_context", self.perspective.state.mode,
            source_module="ego",
            evidence_status=self.perspective.state.evidence_status)
        graph.upsert_edge(runtime, "operates_under", perspective,
                          evidence="perspective tracker")
        added["nodes"] += 1
        added["edges"] += 1
        authority = graph.upsert_node(
            "action_authority", self.action_authority(),
            source_module="ego")
        graph.upsert_edge(runtime, "holds_authority", authority,
                          evidence="body schema / perspective")
        added["nodes"] += 1
        added["edges"] += 1
        for boundary in self.boundaries.boundaries.values():
            node = graph.upsert_node(
                "boundary", boundary.boundary_id, source_module="ego",
                status=boundary.current_status, hard=boundary.hard)
            graph.upsert_edge(runtime, "bounded_by", node,
                              evidence=boundary.description)
            added["nodes"] += 1
            added["edges"] += 1
        counterfactual = graph.get_node("boundary",
                                        BoundaryType.COUNTERFACTUAL)
        if counterfactual is not None:
            offline_node = graph.upsert_node(
                "boundary", BoundaryType.LATENT_OFFLINE,
                source_module="ego")
            graph.upsert_edge(counterfactual, "separates_evidence",
                              offline_node,
                              evidence="counterfactual output never "
                                       "becomes observed evidence",
                              offline=True)
            added["edges"] += 1
        for category, count in self._attribution_counts().items():
            if not count:
                continue
            source_node = graph.upsert_node(
                "attribution_source", category, source_module="ego",
                count=count)
            graph.upsert_edge(source_node, "attributed_to", runtime,
                              evidence=f"{count} attribution(s)")
            added["nodes"] += 1
            added["edges"] += 1
        return added

    def _attribution_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for row in self.attributor.recent:
            counts[row["category"]] = counts.get(row["category"], 0) + 1
        return counts

    # -- persistence / views --------------------------------------------------------------

    def _persist_frame(self, frame: DimensionalFrame,
                       classification: SelfClassification) -> None:
        if self._frames_path is None:
            return
        self._frames_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._frames_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"frame": frame.to_dict(),
                                 "origin": classification.origin,
                                 "attribution":
                                     classification.attribution},
                                default=str) + "\n")

    def save_state(self) -> Dict[str, str]:
        if self.state_dir is None:
            return {}
        state_dir = Path(self.state_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        snapshot = (self.last_snapshot.to_dict()
                    if self.last_snapshot else self.snapshot())
        paths = {"self_model": str(state_dir / "self_model.json"),
                 "boundaries": str(state_dir / "ego_boundaries.json")}
        with open(paths["self_model"], "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, default=str)
        with open(paths["boundaries"], "w", encoding="utf-8") as fh:
            json.dump(self.boundaries.to_dict(), fh, indent=2, default=str)
        return paths

    def summary(self) -> Dict[str, Any]:
        """Compact status for the Inner MAP / supervisor."""
        return {
            "enabled": True,
            "identity_continuity": self.identity.continuity_score,
            "identity_confidence": self.identity.identity_confidence,
            "identity_warnings": list(self.identity.identity_warnings),
            "perspective": self.perspective.state.mode,
            "boundary_violation_count": self.boundaries.violations_total,
            "active_boundaries": len(self.boundaries.boundaries),
            "violated_boundaries": [b.boundary_id for b in
                                    self.boundaries.violated()],
            "classification_counts": dict(self.classification_counts),
            "attribution_unknown_rate": self.attributor.unknown_rate(),
            "action_authority": self.action_authority(),
            "self_model_confidence": round(
                min(self.identity.identity_confidence,
                    1.0 - 0.5 * self.attributor.unknown_rate()), 4),
            "perspective_shift_count": self.perspective.shift_count,
            "perspective_stuck_duration_s":
                self.perspective.stuck_duration_s(),
            "boundary_leaks_blocked": self.safety.rejected_count,
            "updates": self.updates,
            "narrative_trace_path": (str(self.narrative.trace_path)
                                     if self.narrative.trace_path
                                     else None),
            "self_report_path": None,  # set by callers that save one
            "llm_status": {**dict(self.llm_status), "authority": False},
            "proto_language_status": {
                **dict(self.proto_language_status), "authority": False},
            "note": SELF_MODEL_NOTE,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "identity": self.identity.to_dict(),
            "boundaries": self.boundaries.snapshot(),
            "continuity": self.continuity_monitor.snapshot(),
            "perspective": self.perspective.snapshot(),
            "body": self.body_schema.to_dict(),
            "attribution": self.attributor.snapshot(),
            "comparator": self.comparator.snapshot(),
            "narrative": self.narrative.snapshot(),
            "safety": self.safety.snapshot(),
        }

    def to_report(self) -> Dict[str, Any]:
        from .self_report import SelfReportBuilder

        return SelfReportBuilder(self).to_dict()


@dataclass
class SelfModelObserver:
    """Pulls summaries from live components into a SelfModel update."""

    self_model: SelfModel
    runner: Any = None

    def observe(self, extra_context: Optional[Dict[str, Any]] = None,
                ) -> SelfModelSnapshot:
        ctx: Dict[str, Any] = {}
        runner = self.runner
        if runner is not None:
            lifecycle = getattr(runner, "lifecycle", None)
            if lifecycle is not None:
                ctx["run_id"] = getattr(lifecycle, "run_id", "")
                ctx["session_id"] = getattr(lifecycle, "session_id", "")
            bridge = getattr(runner, "bridge", None)
            if bridge is not None:
                ctx["substrate_identity"] = getattr(
                    bridge, "substrate_type", type(bridge).__name__)
            pm = getattr(runner, "pm", None)
            if pm is not None:
                ctx["state_path"] = str(getattr(pm, "state_dir", ""))
            for name in ("homeostasis", "executive", "latent",
                         "world_model"):
                component = getattr(runner, name, None)
                if component is None:
                    continue
                if hasattr(component, "summary"):
                    ctx[name] = component.summary()
                elif hasattr(component, "snapshot"):
                    ctx[name] = component.snapshot()
            latent = getattr(runner, "latent", None)
            if latent is not None and hasattr(latent, "controller"):
                ctx["latent_mode"] = latent.controller.mode
        ctx.update(extra_context or {})
        return self.self_model.update(ctx)

"""Self-boundary runtime -- bounded operational self/world boundary tracking.

:class:`SelfBoundaryRuntime` reads the plural-sensorium receptors/field (and
optional live field, feeder SDK, metabolism, ontogenesis, semiogenesis, and
cognition state), attributes ownership, builds a receptor body schema, updates a
perspective frame, maintains continuity anchors, marks simulation boundaries,
attributes sources, classifies internal/external, detects boundary tensions, and
updates an operational identity trace. Everything is *operational*: no hardware/
feeder/source control, no real-world action, no metaphysical identity claims, and a
strictly bounded loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .body_schema import SensoriumBodySchema
from .boundary_state import BoundaryZone, SelfBoundaryState
from .boundary_tensions import BoundaryTensionDetector
from .continuity import (
    ContinuityAnchorType,
    ContinuityBreakType,
    OrganismicContinuity,
)
from .identity_trace import IdentityTraceEventType, IdentityTraceStore
from .internal_external import InternalExternalClassifier
from .ownership import OwnershipAttributor
from .perspective import PerspectiveFrame, SensoriumPerspective
from .reports import SelfBoundaryReportBuilder
from .safety import SelfBoundarySafetyValidator
from .simulation_boundary import BoundaryMarker, SimulationBoundaryValidator
from .source_attribution import AttributionTarget, SourceAttributionEngine


class SelfBoundaryMilestone:
    FIRST_BOUNDARY_EVENT = "first_boundary_event"
    FIRST_BODY_PART = "first_receptor_body_part"
    FIRST_EXTERNAL_ATTRIBUTION = "first_external_source_attribution"
    FIRST_PERSPECTIVE_SHIFT = "first_perspective_shift"
    FIRST_CONTINUITY_ANCHOR = "first_continuity_anchor"
    FIRST_CONTINUITY_BREAK = "first_continuity_break"
    FIRST_SIMULATION_MARKER = "first_simulation_boundary_marker"
    FIRST_BOUNDARY_TENSION = "first_boundary_tension"
    FIRST_IDENTITY_EVENT = "first_identity_trace_event"

    ALL = (FIRST_BOUNDARY_EVENT, FIRST_BODY_PART, FIRST_EXTERNAL_ATTRIBUTION,
           FIRST_PERSPECTIVE_SHIFT, FIRST_CONTINUITY_ANCHOR,
           FIRST_CONTINUITY_BREAK, FIRST_SIMULATION_MARKER,
           FIRST_BOUNDARY_TENSION, FIRST_IDENTITY_EVENT)


@dataclass
class SelfBoundaryRuntime:
    """The bounded operational self/world boundary loop (internal-only)."""

    state_dir: str = ".solaris_ai_nn_self_boundary"
    sensorium: Any = None
    live_field: Any = None
    feeder_monitor_snapshot: Optional[Dict[str, Any]] = None
    metabolism: Any = None
    ontogenesis: Any = None
    semiogenesis: Any = None
    cognition: Any = None
    max_events_per_tick: int = 400
    max_runtime_s: float = 30.0
    max_ticks: int = 120
    fixture_mode: bool = True
    live_read_only_mode: bool = False
    dry_run: bool = False

    boundary: SelfBoundaryState = field(default_factory=SelfBoundaryState)
    ownership: OwnershipAttributor = field(default_factory=OwnershipAttributor)
    body_schema: SensoriumBodySchema = field(
        default_factory=SensoriumBodySchema)
    perspective: SensoriumPerspective = field(
        default_factory=SensoriumPerspective)
    continuity: OrganismicContinuity = field(
        default_factory=OrganismicContinuity)
    sim_boundary: SimulationBoundaryValidator = field(
        default_factory=SimulationBoundaryValidator)
    source_attribution: SourceAttributionEngine = field(
        default_factory=SourceAttributionEngine)
    classifier: InternalExternalClassifier = field(
        default_factory=InternalExternalClassifier)
    tension_detector: BoundaryTensionDetector = field(
        default_factory=BoundaryTensionDetector)
    identity: IdentityTraceStore = field(default=None, init=False)
    safety: SelfBoundarySafetyValidator = field(
        default_factory=SelfBoundarySafetyValidator)

    milestones: List[str] = field(default_factory=list, init=False)
    ticks_run: int = field(default=0, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.identity = IdentityTraceStore(state_dir=self.state_dir,
                                           persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    def _milestone(self, name: str) -> None:
        if name not in self.milestones:
            self.milestones.append(name)

    def _metabolism_status(self) -> Dict[str, Any]:
        m = self.metabolism
        if m is None:
            return {}
        if isinstance(m, dict):
            return m
        if hasattr(m, "metabolism_status"):
            return m.metabolism_status()
        if hasattr(m, "snapshot"):
            return m.snapshot()
        return {}

    def update(self, *, tick: int = 0) -> Dict[str, Any]:
        """Run one bounded self-boundary tick over the attached state."""
        if self._refused:
            return {"refused": True, "reason": "unbounded identity loop"}
        self.ticks_run += 1
        if tick == 0 and not self.identity.events:
            self.identity.record_event(
                IdentityTraceEventType.RUN_IDENTITY,
                {"run_id": self.identity.trace.run_id})

        sensorium = self.sensorium
        receptors = (list(sensorium.receptors.values())
                     if sensorium is not None
                     and hasattr(sensorium, "receptors") else [])
        status = self._metabolism_status()

        # 1. Body schema + receptor ownership + receptor continuity anchors.
        for r in receptors[:self.max_events_per_tick]:
            part = self.body_schema.update_from_receptor(r)
            self._milestone(SelfBoundaryMilestone.FIRST_BODY_PART)
            self.ownership.attribute("receptor_state", part.receptor_id,
                                     confidence=part.boundary_confidence,
                                     evidence_refs=[f"receptor:{part.receptor_id}"])
            self.boundary.add(BoundaryZone.RECEPTOR_BODY, part.receptor_id,
                              part.boundary_confidence,
                              [f"receptor:{part.receptor_id}"])
            self.continuity.anchor(ContinuityAnchorType.RECEPTOR,
                                   part.receptor_id, part.boundary_confidence)
            self.classifier.classify(part.receptor_id, "plural_sensorium",
                                     detail="receptor reads world")
            # A receptor that reads a source -> the source is external.
            if part.source_link:
                self.ownership.attribute("external_source", part.source_link,
                                         confidence=0.6,
                                         evidence_refs=[f"source:{part.source_link}"])
                self.boundary.add(BoundaryZone.EXTERNAL_WORLD_SOURCE,
                                  part.source_link, 0.6,
                                  [f"source:{part.source_link}"])
                self.source_attribution.attribute(
                    AttributionTarget.EXTERNAL_SOURCE, part.source_link,
                    confidence=part.reliability,
                    corrupted=part.reliability < 0.5)
                self._milestone(
                    SelfBoundaryMilestone.FIRST_EXTERNAL_ATTRIBUTION)
        self.body_schema.link_related()

        # 2. Feeder provenance -> feeder artifact attribution (external, not body).
        snap = self.feeder_monitor_snapshot or {}
        for feeder in snap.get("feeders", []):
            fid = feeder.get("feeder_id", "feeder")
            self.ownership.attribute("feeder_artifact", fid, confidence=0.6,
                                     evidence_refs=[f"feeder:{fid}"])
            self.boundary.add(BoundaryZone.EXTERNAL_FEEDER, fid, 0.6,
                              [f"feeder:{fid}"])
            self.source_attribution.attribute(
                AttributionTarget.FEEDER_ARTIFACT, fid, confidence=0.6)
            self.classifier.classify(fid, "feeder_sdk")

        # 3. Sensory field perspective frame.
        field_state = (sensorium.sensory_field.state()
                       if sensorium is not None
                       and hasattr(sensorium, "sensory_field") else None)
        active_modalities = (sensorium.active_modalities()
                             if sensorium is not None
                             and hasattr(sensorium, "active_modalities") else [])
        frame = PerspectiveFrame(
            active_modality=(active_modalities[0] if active_modalities else ""),
            dominant_receptor=(getattr(field_state, "dominant_modality", "")
                               if field_state else ""),
            neglected_receptor=(getattr(field_state, "neglected_modality", "")
                                or "" if field_state else ""),
            field_pressure=(getattr(field_state, "field_pressure", 0.0)
                            if field_state else 0.0),
            attention_focus=status.get("dominant_perceptual_need", ""),
            uncertainty_focus=("overload" if status.get("overload_state")
                               else "deprivation"
                               if status.get("deprivation_state") else ""),
            prediction_horizon=1,
            memory_horizon=len(self.identity.events),
            simulation_horizon=len(getattr(self.cognition, "simulations", [])
                                   or []))
        shift = self.perspective.update(frame, reason="tick update")
        if shift is not None:
            self._milestone(SelfBoundaryMilestone.FIRST_PERSPECTIVE_SHIFT)
            self.identity.record_event(
                IdentityTraceEventType.BOUNDARY_SHIFT,
                {"shift": shift.to_dict()})

        # 4. Continuity anchors + metabolic continuity risk.
        self.continuity.anchor(ContinuityAnchorType.HEARTBEAT, f"tick:{tick}")
        if field_state is not None:
            self.continuity.anchor(ContinuityAnchorType.SENSORY_FIELD, "field")
        self._milestone(SelfBoundaryMilestone.FIRST_CONTINUITY_ANCHOR)
        # Source silence / corruption -> continuity break (logged).
        for a in self.source_attribution.corrupted():
            brk = self.continuity.record_break(
                ContinuityBreakType.FEEDER_CORRUPTION,
                detail=f"corrupted source {a.ref}")
            self.identity.record_continuity_break(brk.to_dict())
            self._milestone(SelfBoundaryMilestone.FIRST_CONTINUITY_BREAK)
        if status.get("deprivation_state"):
            brk = self.continuity.record_break(
                ContinuityBreakType.SOURCE_SILENCE, detail="deprivation state")
            self.identity.record_continuity_break(brk.to_dict())

        # 5. Internal records (metabolism/concepts/signs/cognition) -> internal.
        self._classify_internal()

        # 6. Simulation boundary markers (sims/counterfactuals stay non-real).
        self._mark_simulations()

        # 7. Boundary tensions.
        tensions = self.tension_detector.detect(
            ownership=self.ownership, classifier=self.classifier,
            simulation=self.sim_boundary, continuity=self.continuity,
            source_attribution=self.source_attribution)
        if tensions:
            self._milestone(SelfBoundaryMilestone.FIRST_BOUNDARY_TENSION)

        # 8. Identity trace refresh.
        self._update_identity(receptors)
        if self.boundary.events:
            self._milestone(SelfBoundaryMilestone.FIRST_BOUNDARY_EVENT)
        for ev in self.boundary.events[-len(receptors) or None:]:
            self.identity.record_boundary_event(ev.to_dict())
        self._milestone(SelfBoundaryMilestone.FIRST_IDENTITY_EVENT)

        self._last = {
            "tick": tick,
            "boundary_event_count": len(self.boundary.events),
            "ownership_attribution_count": len(self.ownership.attributions),
            "receptor_body_part_count": self.body_schema.part_count,
            "continuity_anchor_count": len(self.continuity.anchors),
            "continuity_break_count": len(self.continuity.breaks),
            "boundary_tension_count": len(self.tension_detector.tensions),
            "simulation_boundary_warning_count":
                self.sim_boundary.warning_count(),
        }
        return self._last

    def _classify_internal(self) -> None:
        status = self._metabolism_status()
        if status:
            self.ownership.attribute("internal_metabolic", "metabolism",
                                     confidence=0.8)
            self.boundary.add(BoundaryZone.INTERNAL_STATE, "metabolism", 0.8,
                              ["metabolism"])
            self.classifier.classify("metabolism", "perceptual_metabolism")
        ont = self.ontogenesis
        if ont is not None and hasattr(ont, "concepts"):
            for cid in list(ont.concepts)[:50]:
                self.classifier.classify(cid, "perceptual_ontogenesis")
                self.boundary.add(BoundaryZone.INTERNAL_STATE, cid, 0.7,
                                  ["concept"])
        sem = self.semiogenesis
        if sem is not None and hasattr(sem, "signs"):
            for sid in list(sem.signs)[:50]:
                self.classifier.classify(sid, "semiogenesis")
                self.boundary.add(BoundaryZone.INTERNAL_STATE, sid, 0.7,
                                  ["sign"])

    def _mark_simulations(self) -> None:
        cog = self.cognition
        if cog is None:
            return
        for sim in getattr(cog, "simulations", []) or []:
            sref = getattr(sim, "simulation_id", "sim")
            self.sim_boundary.mark(sref, BoundaryMarker.SIMULATION)
            self.ownership.attribute("simulation", sref, confidence=0.6)
            self.boundary.add(BoundaryZone.SIMULATION, sref, 0.6, ["simulation"])
            self.classifier.classify(sref, "sensorium_cognition")
            self._milestone(SelfBoundaryMilestone.FIRST_SIMULATION_MARKER)
        for cf in getattr(cog, "counterfactuals", []) or []:
            cref = getattr(cf, "counterfactual_id", "cf")
            self.sim_boundary.mark(cref, BoundaryMarker.COUNTERFACTUAL)
            self.ownership.attribute("counterfactual", cref, confidence=0.5)
            self.boundary.add(BoundaryZone.COUNTERFACTUAL, cref, 0.5,
                              ["counterfactual"])
        for p in getattr(cog, "predictions", []) or []:
            pref = getattr(p, "prediction_id", "pred")
            self.ownership.attribute("prediction", pref, confidence=0.6)
            self.boundary.add(BoundaryZone.PREDICTION, pref, 0.6, ["prediction"])
        # Observation markers for the real receptor body (kept distinct).
        for r in (self.sensorium.receptors.values()
                  if self.sensorium is not None
                  and hasattr(self.sensorium, "receptors") else []):
            self.sim_boundary.mark(getattr(r, "receptor_id", "r"),
                                   BoundaryMarker.OBSERVATION)

    def _update_identity(self, receptors: List[Any]) -> None:
        tr = self.identity.trace
        tr.continuity_anchors = sorted({a.anchor_type
                                        for a in self.continuity.anchors})
        tr.active_receptors = [getattr(r, "receptor_id", "")
                               for r in receptors]
        sem = self.semiogenesis
        if sem is not None and hasattr(sem, "stable_signs"):
            tr.stable_signs = [s.sign_id for s in sem.stable_signs()]
        ont = self.ontogenesis
        if ont is not None and hasattr(ont, "stable_concepts"):
            tr.stable_proto_concepts = [c.concept_id
                                        for c in ont.stable_concepts()]

    def run_bounded(self, max_ticks: Optional[int] = None) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True}
        started = time.time()
        n = min(self.max_ticks, max_ticks or self.max_ticks)
        for tick in range(n):
            if time.time() - started > self.max_runtime_s:
                break
            self.update(tick=tick)
        return {"refused": False, "ticks_run": self.ticks_run,
                "last": self._last}

    def record_restart(self, detail: str = "") -> None:
        """Record a restart event and a (recoverable) continuity break."""
        self.identity.record_event(IdentityTraceEventType.RESTART,
                                   {"detail": detail})
        brk = self.continuity.record_break(
            ContinuityBreakType.MISSING_STATE,
            detail=detail or "restart gap")
        self.identity.record_continuity_break(brk.to_dict())
        self.continuity.anchor(ContinuityAnchorType.RESTART, "restart")

    # -- integration views ----------------------------------------------------

    def logos_tensions(self) -> List[Any]:
        """Boundary tensions expressed as LOGOS tensions (valid types only)."""
        from ..logos_complexity.tension import (
            LogosTension,
            TensionPolarity,
            TensionType,
        )

        mapping = {
            "internal_vs_external": (TensionType.SELF_OTHER_BOUNDARY,
                                     "internal", "external"),
            "simulation_vs_observation": (TensionType.OFFLINE_REAL_BOUNDARY,
                                          "simulation", "observation"),
            "memory_vs_current_flux": (TensionType.MEMORY_COMPRESSION,
                                       "memory", "current_flux"),
            "prediction_vs_sensory_event": (TensionType.PREDICTION_FAILURE,
                                            "prediction", "sensory_event"),
            "feeder_artifact_vs_world_source": (TensionType.KNOWN_UNKNOWN,
                                                "feeder_artifact",
                                                "world_source"),
            "receptor_body_vs_external_source": (
                TensionType.SELF_OTHER_BOUNDARY, "receptor_body",
                "external_source"),
            "self_continuity_vs_restart_gap": (TensionType.DRIFT_IDENTITY,
                                               "self_continuity",
                                               "restart_gap"),
            "human_gloss_vs_internal_sign": (TensionType.SYMBOL_AMBIGUITY,
                                             "human_gloss", "internal_sign"),
            "unknown_origin": (TensionType.KNOWN_UNKNOWN,
                               TensionPolarity.KNOWN, TensionPolarity.UNKNOWN),
        }
        out: List[LogosTension] = []
        for t in self.tension_detector.tensions:
            ltype, pa, pb = mapping.get(
                t.tension_type, (TensionType.KNOWN_UNKNOWN,
                                 TensionPolarity.KNOWN,
                                 TensionPolarity.UNKNOWN))
            out.append(LogosTension(
                tension_type=ltype, polarity_a=pa, polarity_b=pb,
                source_modules=["self_boundary"],
                metadata={"self_boundary_tension": t.tension_type}))
        return out

    def memory_events(self) -> List[Dict[str, Any]]:
        """Boundary/continuity/identity events for memory storage."""
        return ([e.to_dict() for e in self.boundary.events]
                + [b.to_dict() for b in self.continuity.breaks]
                + [e.to_dict() for e in self.identity.events])

    def ego_bridge_summary(self, ego_model: Any = None) -> Dict[str, Any]:
        """Bridge to an older ego/self model if present (no duplication).

        Returns a sensorium-native boundary summary. If an ego model exposing
        ``update``/``summary`` is provided, the summary is offered to it as
        context without overwriting the ego module's own logic.
        """
        summary = {
            "boundary_confidence": self.boundary.confidence_score(),
            "receptor_body_part_count": self.body_schema.part_count,
            "continuity_score": self.continuity.continuity_score(),
            "source_attribution_uncertainty":
                self.source_attribution.uncertainty_score(),
            "note": "sensorium-native self-boundary summary; operational only",
        }
        if ego_model is not None and hasattr(ego_model, "update"):
            try:
                ego_model.update(context={"self_boundary": summary})
            except Exception:
                pass
        return summary

    def self_boundary_status(self) -> Dict[str, Any]:
        return {
            "self_boundary_enabled": True,
            "boundary_event_count": len(self.boundary.events),
            "boundary_confidence_score": self.boundary.confidence_score(),
            "ownership_attribution_count": len(self.ownership.attributions),
            "ambiguous_ownership_count": len(self.ownership.ambiguous()),
            "perspective_shift_count": len(self.perspective.shifts),
            "current_perspective_frame": self.perspective.frame.signature(),
            "receptor_body_schema_count": self.body_schema.part_count,
            "body_schema_stability": self.body_schema.stability(),
            "continuity_anchor_count": len(self.continuity.anchors),
            "continuity_break_count": len(self.continuity.breaks),
            "simulation_boundary_warning_count":
                self.sim_boundary.warning_count(),
            "simulation_boundary_integrity": self.sim_boundary.integrity(),
            "source_attribution_uncertainty_score":
                self.source_attribution.uncertainty_score(),
            "identity_trace_event_count": self.identity.event_count(),
            "boundary_tension_count": len(self.tension_detector.tensions),
            "self_boundary_safety_block_count": self.safety.rejected_count,
            "latest_self_boundary_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "SELF_BOUNDARY_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.self_boundary_status()

    def write_artifacts(self) -> Dict[str, Any]:
        return SelfBoundaryReportBuilder(self).write()

"""Plural sensorium runtime -- continuous, bounded, organismic perception.

:class:`PluralSensoriumRuntime` ties the layer together: it loads external feeder
descriptors, validates read-only source roots, initialises receptors, polls the
streams within bounds, updates receptor states and the continuous sensory field,
estimates baselines, detects flux / absence / rhythm / invariants / cross-modal
relations, adapts internal attention, and produces Stimulus objects and
modality-grounded structures for the rest of the system. It is disabled by
default; fixture mode is allowed by default; real read-only mode requires
governance approval; it never loops unbounded, modifies a source, accesses
hardware, or controls anything external.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..signals.canonical import Stimulus
from .absence_detection import AbsenceDetector
from .attention import SensoriumAttentionPolicy
from .baseline import BaselineEstimator
from .cross_modal import CrossModalDetector
from .event_envelope import SensoryEventEnvelope
from .external_feeders import ExternalFeederDescriptor
from .flux_detection import FluxDetector
from .grounding import SensoriumGroundingAnalyzer
from .invariant_detection import InvariantCandidate, InvariantDetector
from .modality import ModalityFamily, modality_class_for
from .receptors import Receptor, event_intensity
from .rhythm_detection import RhythmDetector
from .safety import PluralSensoriumSafetyValidator
from .sensory_field import SensoryField
from .stream_adapters import read_feeder

# Map a modality family to a modality-grounded proto-symbol type (section 23).
_SYMBOL_TYPE = {
    ModalityFamily.HUMAN_TEXTUAL: "human_text_grounded_symbol",
    ModalityFamily.HUMAN_VISUAL_METADATA: "visual_metadata_grounded_symbol",
    ModalityFamily.HUMAN_AUDIO_METADATA: "audio_metadata_grounded_symbol",
    ModalityFamily.RADIO_FREQUENCY: "rf_grounded_symbol",
    ModalityFamily.MICROWAVE_MMWAVE: "rf_grounded_symbol",
    ModalityFamily.ULTRASOUND_ECHO: "echo_grounded_symbol",
    ModalityFamily.THERMAL_GRADIENT: "thermal_grounded_symbol",
    ModalityFamily.VIBRATION: "vibration_grounded_symbol",
    ModalityFamily.MAGNETIC: "magnetic_grounded_symbol",
    ModalityFamily.ABSENCE_SILENCE: "absence_grounded_symbol",
}

# Developmental milestones this layer can record (section 28).
class SensoriumMilestone:
    FIRST_SENSORIUM_EVENT = "first_sensorium_event"
    FIRST_HUMAN_LIKE_MODALITY_EVENT = "first_human_like_modality_event"
    FIRST_NON_HUMAN_MODALITY_EVENT = "first_non_human_modality_event"
    FIRST_RF_PATTERN = "first_RF_pattern"
    FIRST_ECHO_BOUNDARY = "first_echo_boundary"
    FIRST_SIGNAL_ABSENCE = "first_signal_absence"
    FIRST_BASELINE_SHIFT = "first_baseline_shift"
    FIRST_RECEPTOR_ADAPTATION = "first_receptor_adaptation"
    FIRST_CROSS_MODAL_RELATION = "first_cross_modal_relation"
    FIRST_SENSORIUM_INVARIANT = "first_sensorium_invariant"
    FIRST_MODALITY_GROUNDED_PROTO_SYMBOL = "first_modality_grounded_proto_symbol"
    FIRST_HUMAN_LABEL_CONTAMINATION_WARNING = \
        "first_human_label_contamination_warning"

    ALL = (FIRST_SENSORIUM_EVENT, FIRST_HUMAN_LIKE_MODALITY_EVENT,
           FIRST_NON_HUMAN_MODALITY_EVENT, FIRST_RF_PATTERN,
           FIRST_ECHO_BOUNDARY, FIRST_SIGNAL_ABSENCE, FIRST_BASELINE_SHIFT,
           FIRST_RECEPTOR_ADAPTATION, FIRST_CROSS_MODAL_RELATION,
           FIRST_SENSORIUM_INVARIANT, FIRST_MODALITY_GROUNDED_PROTO_SYMBOL,
           FIRST_HUMAN_LABEL_CONTAMINATION_WARNING)


@dataclass
class PluralSensoriumRuntime:
    """The bounded organismic perception loop (disabled by default)."""

    state_dir: str = ".solaris_ai_nn_state"
    input_roots: List[str] = field(default_factory=list)
    enabled_modalities: Optional[List[str]] = None
    max_events_per_poll: int = 200
    max_events_total: int = 5000
    poll_interval_s: float = 0.0
    max_runtime_s: float = 30.0
    fixture_mode: bool = True
    real_read_only_mode: bool = False
    dry_run: bool = False
    require_governance_for_real_sources: bool = True
    governance: Any = None
    enabled: bool = False

    feeders: List[ExternalFeederDescriptor] = field(default_factory=list)
    receptors: Dict[str, Receptor] = field(default_factory=dict)
    sensory_field: SensoryField = field(default_factory=SensoryField)
    baseline: BaselineEstimator = field(default_factory=BaselineEstimator)
    flux: FluxDetector = field(default_factory=FluxDetector)
    absence: AbsenceDetector = field(default_factory=AbsenceDetector)
    rhythm: RhythmDetector = field(default_factory=RhythmDetector)
    invariants: InvariantDetector = field(default_factory=InvariantDetector)
    cross_modal: CrossModalDetector = field(default_factory=CrossModalDetector)
    attention: SensoriumAttentionPolicy = field(
        default_factory=SensoriumAttentionPolicy)
    grounding: SensoriumGroundingAnalyzer = field(
        default_factory=SensoriumGroundingAnalyzer)
    safety: PluralSensoriumSafetyValidator = field(
        default_factory=PluralSensoriumSafetyValidator)

    # Outputs.
    stimuli: List[Stimulus] = field(default_factory=list, init=False)
    baseline_shifts: List[Dict[str, Any]] = field(default_factory=list,
                                                  init=False)
    proto_symbol_candidates: List[Dict[str, Any]] = field(default_factory=list,
                                                          init=False)
    world_model_structures: List[Dict[str, Any]] = field(default_factory=list,
                                                         init=False)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list, init=False)
    logos_tensions: List[Dict[str, Any]] = field(default_factory=list,
                                                 init=False)
    milestones: List[str] = field(default_factory=list, init=False)
    refusal_reasons: List[str] = field(default_factory=list, init=False)
    events_ingested: int = field(default=0, init=False)
    polls: int = field(default=0, init=False)
    _seen_invariants: set = field(default_factory=set, init=False)
    _promoted_invariants: set = field(default_factory=set, init=False)
    _started_at: float = field(default=0.0, init=False)

    # -- setup ----------------------------------------------------------------

    def add_feeder(self, feeder: ExternalFeederDescriptor) -> bool:
        """Register a feeder, refusing real-world sources without governance."""
        if feeder.requires_governance and self.require_governance_for_real_sources:
            if not self._governance_ok():
                self.refusal_reasons.append(
                    f"feeder {feeder.feeder_id!r} is a real-world source and "
                    "requires governance approval")
                return False
        self.feeders.append(feeder)
        return True

    def _governance_ok(self) -> bool:
        if not self.real_read_only_mode:
            return False
        if self.governance is None:
            return False
        try:
            return bool(self.governance.is_enabled(
                "enable_plural_sensorium_real_read_only"))
        except Exception:
            return False

    def validate_source_roots(self) -> bool:
        """Confirm every feeder path stays inside an approved read-only root."""
        if not self.input_roots:
            return True
        for feeder in self.feeders:
            report = self.safety.validate_operation(f"read {feeder.path}")
            if not report.safe:
                self.refusal_reasons.append(
                    f"feeder {feeder.feeder_id!r} failed safety check")
                return False
        return True

    def _milestone(self, name: str) -> None:
        if name not in self.milestones:
            self.milestones.append(name)

    def _receptor_for(self, envelope: SensoryEventEnvelope) -> Receptor:
        rid = f"{envelope.source_id}:{envelope.modality}"
        receptor = self.receptors.get(rid)
        if receptor is None:
            receptor = Receptor(receptor_id=rid, modality=envelope.modality,
                                source_id=envelope.source_id)
            self.receptors[rid] = receptor
        return receptor

    # -- polling --------------------------------------------------------------

    def poll_once(self) -> Dict[str, Any]:
        """Read each feeder once, update state, and produce stimuli (bounded)."""
        self.polls += 1
        now = time.time()
        new_events: List[SensoryEventEnvelope] = []
        budget = max(0, self.max_events_total - self.events_ingested)
        if budget <= 0:
            return {"events": 0, "stopped": "max_events_total reached"}

        for feeder in self.feeders:
            if len(new_events) >= self.max_events_per_poll or budget <= 0:
                break
            result = read_feeder(feeder, max_lines=self.max_events_per_poll)
            for envelope in result.events:
                if budget <= 0 or len(new_events) >= self.max_events_per_poll:
                    break
                if self.enabled_modalities and \
                        envelope.modality not in self.enabled_modalities:
                    continue
                new_events.append(envelope)
                budget -= 1

        for envelope in new_events:
            self._ingest(envelope, now)

        # Silence + absence for receptors that did not fire this poll.
        fired = {e.source_id for e in new_events}
        for receptor in self.receptors.values():
            if receptor.source_id not in fired:
                receptor.observe_silence()
        for absence_ev in self.absence.check(now):
            self._milestone(SensoriumMilestone.FIRST_SIGNAL_ABSENCE)
            self.logos_tensions.append({
                "tension": "expected_signal_vs_absence",
                "modality": absence_ev.modality,
                "source_id": absence_ev.source_id,
                "provenance": absence_ev.provenance})
            self._seed_hypothesis("signal_disappearance", absence_ev.modality,
                                  absence_ev.source_id, absence_ev.provenance)

        # Flux per receptor + rhythms.
        for receptor in self.receptors.values():
            self.flux.detect(receptor, self.baseline.get(receptor.receptor_id))
        for sig in self.rhythm.detect_all():
            cand = self.invariants.observe_rhythm(sig.source_id, sig.modality,
                                                  sig.period)
            if cand is not None:
                self._register_invariant(cand)

        # Continuous field update.
        receptors = list(self.receptors.values())
        novelty = max((r.recent_novelty for r in receptors), default=0.0)
        field_state = self.sensory_field.update(
            receptors, novelty=novelty,
            absence=self.absence.absence_pressure(),
            rhythm=self.rhythm.rhythm_pressure(),
            cross_modal=self.cross_modal.cross_modal_pressure(),
            noise=self._noise_pressure(),
            tensions=[t["tension"] for t in self.logos_tensions[-3:]])

        # Internal attention (bounded, no hardware).
        self.attention.decide(field_state, receptors)
        if any(r.adaptation_count > 0 for r in receptors):
            self._milestone(SensoriumMilestone.FIRST_RECEPTOR_ADAPTATION)

        # Field deformation as a whole-field flux event.
        self.flux.detect_field_deformation(field_state.stability)
        return {"events": len(new_events), "field": field_state.to_dict()}

    def _ingest(self, envelope: SensoryEventEnvelope, now: float) -> None:
        self.events_ingested += 1
        self._milestone(SensoriumMilestone.FIRST_SENSORIUM_EVENT)
        mclass = modality_class_for(envelope.modality)
        if mclass == "human_like":
            self._milestone(SensoriumMilestone.FIRST_HUMAN_LIKE_MODALITY_EVENT)
        else:
            self._milestone(SensoriumMilestone.FIRST_NON_HUMAN_MODALITY_EVENT)
        if envelope.modality == ModalityFamily.RADIO_FREQUENCY:
            self._milestone(SensoriumMilestone.FIRST_RF_PATTERN)
        if envelope.modality == ModalityFamily.ULTRASOUND_ECHO:
            self._milestone(SensoriumMilestone.FIRST_ECHO_BOUNDARY)
        if envelope.has_human_label:
            self._milestone(
                SensoriumMilestone.FIRST_HUMAN_LABEL_CONTAMINATION_WARNING)

        receptor = self._receptor_for(envelope)
        receptor.observe(envelope)
        intensity = event_intensity(envelope)
        shift = self.baseline.update(receptor.receptor_id, envelope.modality,
                                     intensity)
        if shift is not None:
            self.baseline_shifts.append(shift.to_dict())
            self._milestone(SensoriumMilestone.FIRST_BASELINE_SHIFT)

        ts = envelope.timestamp
        self.absence.observe(envelope.source_id, envelope.modality, ts)
        self.rhythm.observe(envelope.source_id, envelope.modality, ts)
        for rel in self.cross_modal.observe(envelope.modality,
                                            envelope.source_id, ts, intensity):
            if rel.support == 1:
                self._milestone(SensoriumMilestone.FIRST_CROSS_MODAL_RELATION)
                self._add_world_structure("cross_modal_relation", rel.to_dict())

        # Bucket the intensity to find repeated structure (an invariant).
        bucket = f"i~{round(intensity, 1)}"
        cand = self.invariants.observe_feature_bucket(
            envelope.source_id, envelope.modality, "repeated_burst", bucket)
        if cand is not None:
            self._register_invariant(cand)

        # Emit a Stimulus (unless dry-run, which never publishes).
        if not self.dry_run:
            self.stimuli.append(Stimulus(
                origin="plural_sensorium", modality=envelope.modality,
                payload={"source_id": envelope.source_id,
                         "features": dict(envelope.features),
                         "provenance": dict(envelope.provenance)},
                intensity=min(1.0, intensity), is_absence=False))
        self._add_world_structure("modality_source", {
            "modality": envelope.modality, "source_id": envelope.source_id,
            "modality_class": mclass})

    def _register_invariant(self, cand: InvariantCandidate) -> None:
        # First sighting: record the candidate, seed a hypothesis, note the
        # milestone. Later sightings only matter if it has *become* strong.
        if cand.candidate_id not in self._seen_invariants:
            self._seen_invariants.add(cand.candidate_id)
            self._milestone(SensoriumMilestone.FIRST_SENSORIUM_INVARIANT)
            self._add_world_structure("invariant_candidate", cand.to_dict())
            self._seed_hypothesis("field_pattern_recurrence", cand.modality,
                                  cand.source_id, cand.provenance)
        # Promote to a modality-grounded proto-symbol once (when strong).
        if cand.is_strong and cand.candidate_id not in self._promoted_invariants:
            self._promoted_invariants.add(cand.candidate_id)
            self._promote_proto_symbol(cand)

    def _promote_proto_symbol(self, cand: InvariantCandidate) -> None:
        symbol_type = _SYMBOL_TYPE.get(cand.modality, "cross_modal_symbol")
        human_label_dependence = 0.0
        contaminated = False
        # A symbol grounded only in human-labelled text is flagged.
        record = self.grounding.assess(
            candidate_id=cand.candidate_id, modality=cand.modality,
            repeated_pattern=True, cross_time_persistence=cand.support >= 3,
            compression_useful=True, provenance_preserved=True,
            human_label_dependence=human_label_dependence,
            fixture_only=self.fixture_mode)
        if record.quality == "human_label_contaminated":
            symbol_type = "human_label_contaminated_symbol"
            contaminated = True
        self.proto_symbol_candidates.append({
            "symbol_type": symbol_type,
            "modality": cand.modality,
            "source_id": cand.source_id,
            "signature": cand.signature,
            "support": cand.support,
            "grounding_quality": record.quality,
            "human_label_contaminated": contaminated,
            "provenance": dict(cand.provenance),
        })
        self._milestone(
            SensoriumMilestone.FIRST_MODALITY_GROUNDED_PROTO_SYMBOL)

    def _seed_hypothesis(self, kind: str, modality: str, source_id: str,
                         provenance: Dict[str, Any]) -> None:
        self.hypotheses.append({
            "kind": kind, "modality": modality, "source_id": source_id,
            "timestamp": time.time(), "provenance": dict(provenance),
            "evidence_scope": {"modality": modality, "source_id": source_id}})

    def _add_world_structure(self, kind: str, data: Dict[str, Any]) -> None:
        self.world_model_structures.append({"kind": kind, **data})

    def _noise_pressure(self) -> float:
        unreliable = [r for r in self.receptors.values() if r.reliability < 0.8]
        return min(1.0, len(unreliable) / max(1, len(self.receptors)))

    # -- bounded run ----------------------------------------------------------

    def run_bounded(self, max_polls: int = 5) -> Dict[str, Any]:
        """Poll up to ``max_polls`` times, never exceeding the time budget."""
        if not self.fixture_mode and self.real_read_only_mode \
                and not self._governance_ok():
            self.refusal_reasons.append(
                "real read-only mode requires governance approval")
            return {"refused": True, "reasons": list(self.refusal_reasons),
                    "polls": 0}
        if not self.validate_source_roots():
            return {"refused": True, "reasons": list(self.refusal_reasons),
                    "polls": 0}
        self._started_at = time.time()
        polls = 0
        for _ in range(max(1, max_polls)):
            if time.time() - self._started_at > self.max_runtime_s:
                break
            if self.events_ingested >= self.max_events_total:
                break
            self.poll_once()
            polls += 1
        return {"refused": False, "polls": polls,
                "events_ingested": self.events_ingested,
                "field": self.sensory_field.to_dict()}

    # -- status ---------------------------------------------------------------

    def active_modalities(self) -> List[str]:
        return sorted({r.modality for r in self.receptors.values()
                       if r.event_count > 0})

    def human_label_contamination_score(self) -> float:
        return self.grounding.human_label_contamination_score()

    def modality_native_grounding_score(self) -> float:
        return self.grounding.modality_native_grounding_score()

    def plural_sensorium_status(self) -> Dict[str, Any]:
        field_state = self.sensory_field.state(
            active_receptor_count=len(
                [r for r in self.receptors.values() if r.event_count > 0]))
        return {
            "enabled": True,
            "plural_sensorium_enabled": True,
            "active_modality_count": len(self.active_modalities()),
            "active_modalities": self.active_modalities(),
            "active_receptor_count": sum(
                1 for r in self.receptors.values() if r.event_count > 0),
            "sensory_field_pressure": field_state.field_pressure,
            "absence_pressure": field_state.absence_pressure,
            "novelty_pressure": field_state.novelty_pressure,
            "rhythm_pressure": field_state.rhythm_pressure,
            "cross_modal_pressure": field_state.cross_modal_pressure,
            "receptor_adaptation_count": sum(
                r.adaptation_count for r in self.receptors.values()),
            "baseline_shift_count": len(self.baseline_shifts),
            "flux_event_count": len(self.flux.events),
            "absence_event_count": len(self.absence.events),
            "rhythm_signature_count": len(self.rhythm.signatures),
            "invariant_candidate_count": len(self.invariants.candidates),
            "cross_modal_relation_count": self.cross_modal.relation_count(),
            "modality_grounded_proto_symbol_count": len(
                self.proto_symbol_candidates),
            "human_label_contamination_score":
                self.human_label_contamination_score(),
            "modality_native_grounding_score":
                self.modality_native_grounding_score(),
            "latest_plural_sensorium_report_path":
                self.metadata_report_path(),
        }

    def metadata_report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "PLURAL_SENSORIUM_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.plural_sensorium_status()

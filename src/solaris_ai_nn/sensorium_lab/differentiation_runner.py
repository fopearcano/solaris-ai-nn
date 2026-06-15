"""Differentiation runner -- run each study arm and compare the structures.

:class:`SensoriumDifferentiationRunner` prepares a study, runs each arm through the
Prompt-41 :class:`PluralSensoriumRuntime` over bounded, seed-replayable events,
builds a world signature, structure metrics, modality fingerprints, and an
ontology-drift result per arm, and compares the arms. Runs are bounded; no
hardware is accessed; no feeder is auto-started; live arms require governance
approval (and are marked blocked, not failed, when it is missing); and the
debug-truth files of earlier prompts never enter perception.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..organismic_demo import PerceptionChangeProbe
from ..plural_sensorium import PluralSensoriumRuntime
from ..plural_sensorium.event_envelope import AnnotationStatus, SensoryEventEnvelope
from ..plural_sensorium.modality import ModalityFamily as MF
from .label_contamination import HumanLabelContaminationAnalyzer
from .modality_fingerprint import ModalityFingerprintBuilder
from .ontology_drift import OntologyDriftDetector
from .safety import SensoriumLabSafetyValidator
from .sensorium_profiles import SensoriumProfile, SensoriumProfileBuilder
from .structure_metrics import SensoriumStructureMetrics
from .study_design import SensoriumStudyArm, SensoriumStudyDesign
from .world_signature import SensoriumWorldSignature, WorldSignatureBuilder

# Human-like modalities whose feeders may carry annotations.
_HUMAN_TEXT = MF.HUMAN_TEXTUAL


@dataclass
class ArmRunResult:
    arm: SensoriumStudyArm
    profile: SensoriumProfile
    runtime: Optional[PluralSensoriumRuntime] = None
    signature: Optional[SensoriumWorldSignature] = None
    metrics: Optional[SensoriumStructureMetrics] = None
    fingerprints: List[Any] = field(default_factory=list)
    ontology_drift: Optional[Any] = None
    contamination: Optional[Any] = None
    probe_result: Optional[Any] = None
    blocked: bool = False
    inconclusive: bool = False
    reasons: List[str] = field(default_factory=list)
    passive: bool = False
    total_events: int = 0
    human_labelled_events: int = 0

    def to_study_result(self) -> Dict[str, Any]:
        return {
            "arm_id": self.arm.arm_id,
            "condition": self.arm.condition,
            "blocked": self.blocked,
            "inconclusive": self.inconclusive,
            "reasons": list(self.reasons),
            "world_signature": (self.signature.to_dict()
                                if self.signature else None),
            "structure_metrics": (self.metrics.to_dict()
                                  if self.metrics else None),
            "modality_fingerprints": [f.to_dict() for f in self.fingerprints],
            "ontology_drift": (self.ontology_drift.to_dict()
                               if self.ontology_drift else None),
            "contamination": (self.contamination.to_dict()
                              if self.contamination else None),
        }


@dataclass
class SensoriumDifferentiationRunner:
    """Runs a bounded sensorium differentiation study, arm by arm."""

    state_dir: str = ".solaris_ai_nn_sensorium_lab"
    design: Optional[SensoriumStudyDesign] = None
    governance: Any = None
    safety: SensoriumLabSafetyValidator = field(
        default_factory=SensoriumLabSafetyValidator)
    profile_builder: SensoriumProfileBuilder = field(
        default_factory=SensoriumProfileBuilder)
    arm_results: Dict[str, ArmRunResult] = field(default_factory=dict,
                                                 init=False)

    def prepare_study(self, design: SensoriumStudyDesign) -> bool:
        bounded = self.safety.validate_bounded(design.ticks, design.max_events)
        if not bounded.safe:
            return False
        self.design = design
        return True

    def run_all(self) -> Dict[str, ArmRunResult]:
        if self.design is None:
            self.design = _default_design()
        for arm in self.design.arms:
            self.arm_results[arm.arm_id] = self.run_arm(arm)
        return self.arm_results

    def run_arm(self, arm: SensoriumStudyArm) -> ArmRunResult:
        profile = self.profile_builder.build(arm.profile_type)
        result = ArmRunResult(arm=arm, profile=profile)

        if arm.live and not self._governance_ok():
            result.blocked = True
            result.reasons.append("live read-only arm requires governance "
                                  "approval")
            return result

        events = self._generate_events(arm, profile)
        result.total_events = len(events)
        result.human_labelled_events = sum(
            1 for e in events
            if e["annotation_status"] == AnnotationStatus.HUMAN_LABEL_EXTERNAL)

        if profile.passive_only:
            result.passive = True
            result.metrics = SensoriumStructureMetrics.compute(None,
                                                               passive=True)
            result.signature = SensoriumWorldSignature(
                arm_id=arm.arm_id, condition=arm.condition)
            result.contamination = HumanLabelContaminationAnalyzer().analyze(
                None)
            return result

        runtime = PluralSensoriumRuntime(
            state_dir=f"{self.state_dir}/{arm.arm_id}",
            enabled_modalities=profile.enabled_modalities,
            max_events_total=self.design.max_events)
        responses: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        by_tick: Dict[int, List[SensoryEventEnvelope]] = defaultdict(list)
        for ev in events:
            by_tick[ev["tick"]].append(self._envelope(ev))

        for tick in range(self.design.ticks):
            fired: List[str] = []
            for env in by_tick.get(tick, []):
                runtime.observe_envelope(env, now=float(tick))
                fired.append(env.source_id)
                rid = f"{env.source_id}:{env.modality}"
                receptor = runtime.receptors.get(rid)
                if receptor is not None:
                    if not profile.receptor_adaptation_enabled:
                        receptor.sensitivity.value = 0.5
                        receptor.adaptation_count = 0
                    responses[env.modality].append({
                        "novelty": receptor.recent_novelty,
                        "sensitivity": receptor.sensitivity.value,
                        "baseline": receptor.baseline})
            runtime.advance_tick(fired, now=float(tick))
            if profile.attention_policy == "fixed":
                runtime.attention.state.shifts = 0

        result.runtime = runtime
        result.probe_result = PerceptionChangeProbe().compute(dict(responses),
                                                              runtime)
        result.signature = WorldSignatureBuilder().build(
            arm.arm_id, arm.condition, runtime,
            probe_result=result.probe_result)
        result.metrics = SensoriumStructureMetrics.compute(
            runtime, dict(responses), result.probe_result)
        result.fingerprints = ModalityFingerprintBuilder().build(runtime)
        result.ontology_drift = OntologyDriftDetector().detect(runtime)
        result.contamination = HumanLabelContaminationAnalyzer().analyze(
            runtime, human_labelled_events=result.human_labelled_events,
            total_events=result.total_events)
        return result

    def build_world_signature(self, arm_result: ArmRunResult,
                              ) -> Optional[SensoriumWorldSignature]:
        return arm_result.signature

    def compare_results(self):
        from .comparative_analysis import SensoriumComparison

        payload = {
            arm_id: {
                "condition": r.arm.condition,
                "blocked": r.blocked, "inconclusive": r.inconclusive,
                "signature": r.signature,
                "metrics": r.metrics.flat() if r.metrics else {}}
            for arm_id, r in self.arm_results.items()}
        return SensoriumComparison().compare(payload)

    def architecture_proposals(self) -> List[Dict[str, Any]]:
        """Generate architecture-evolution proposal *inputs* (proposals only).

        These are evidence-backed suggestions -- modality additions/pruning,
        receptor/attention revision, label-contamination mitigation, feeder
        improvements, live follow-ups -- for the architecture-evolution layer to
        review. They never trigger automatic code changes.
        """
        proposals: List[Dict[str, Any]] = []
        for arm_id, r in self.arm_results.items():
            for fp in r.fingerprints:
                if fp.structurally_weak:
                    proposals.append({
                        "proposal_type": "consider_modality_pruning",
                        "target": fp.modality, "arm": arm_id,
                        "rationale": "many events but no structural effect",
                        "evidence_refs": [arm_id]})
            if r.contamination and r.contamination.contamination_score > 0.3:
                proposals.append({
                    "proposal_type": "label_contamination_mitigation",
                    "target": arm_id,
                    "rationale": "human-label contamination is significant; "
                                 "prefer feature-only streams",
                    "evidence_refs": [arm_id]})
            if r.ontology_drift and r.ontology_drift.dominant_ontology == \
                    "modality_native_ontology":
                proposals.append({
                    "proposal_type": "receptor_revision",
                    "target": arm_id,
                    "rationale": "modality-native structure is strong; consider "
                                 "promoting these receptors",
                    "evidence_refs": [arm_id]})
        if not proposals:
            proposals.append({
                "proposal_type": "live_field_follow_up_study",
                "target": "all",
                "rationale": "no strong proposal from fixtures; run a governed "
                             "live read-only follow-up",
                "evidence_refs": ["sensorium_differentiation_report"]})
        return proposals

    def write_artifacts(self):
        from .study_report import SensoriumDifferentiationStudyReportBuilder

        return SensoriumDifferentiationStudyReportBuilder(self).write()

    # -- event generation -----------------------------------------------------

    def _generate_events(self, arm: SensoriumStudyArm,
                         profile: SensoriumProfile) -> List[Dict[str, Any]]:
        rng = random.Random(self.design.seed + hash(arm.arm_id) % 1000)
        events: List[Dict[str, Any]] = []
        modalities = [m for m in profile.enabled_modalities
                      if m != MF.ABSENCE_SILENCE]
        absence_heavy = MF.ABSENCE_SILENCE in profile.enabled_modalities
        ticks = self.design.ticks

        for tick in range(ticks):
            # Absence-heavy: sources go silent for the back half of the run.
            if absence_heavy and tick > ticks // 2 and tick % 3:
                continue
            for i, modality in enumerate(modalities):
                if rng.random() < 0.6 + 0.1 * (i % 2):
                    value = round(0.5 + 0.3 * rng.random(), 3)
                    annotation = None
                    status = AnnotationStatus.NONE
                    if profile.human_labels_allowed and modality == _HUMAN_TEXT:
                        annotation = f"observed event {tick}"
                        status = AnnotationStatus.HUMAN_LABEL_EXTERNAL
                    events.append({
                        "tick": tick, "source_id": modality,
                        "modality": modality, "value": value,
                        "annotation": annotation, "annotation_status": status})
                    # A cross-modal coupling for the first two modalities.
                    if profile.cross_modal_detection_enabled and i == 0 \
                            and len(modalities) > 1 and rng.random() < 0.7:
                        events.append({
                            "tick": tick + 1, "source_id": modalities[1],
                            "modality": modalities[1],
                            "value": round(0.4 + 0.2 * rng.random(), 3),
                            "annotation": None,
                            "annotation_status": AnnotationStatus.NONE})
        return events

    def _envelope(self, ev: Dict[str, Any]) -> SensoryEventEnvelope:
        return SensoryEventEnvelope(
            source_id=ev["source_id"], source_kind="fixture_replay",
            modality=ev["modality"], features={"v": ev["value"]},
            timestamp=float(ev["tick"]), annotation=ev["annotation"],
            annotation_status=ev["annotation_status"],
            provenance={"source_id": ev["source_id"],
                        "feeder": "sensorium_lab_fixture"})

    def _governance_ok(self) -> bool:
        if self.governance is None:
            return False
        try:
            return bool(self.governance.is_enabled(
                "enable_live_field_read_only_pilot"))
        except Exception:
            return False


def _default_design() -> SensoriumStudyDesign:
    from .study_design import default_study_design

    return default_study_design()

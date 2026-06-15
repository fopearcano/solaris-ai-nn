"""Plural sensorium -- Solaris as an organism bathed in environmental flux.

This package treats Solaris-AI-NN as an evolving organism continuously exposed to
stimuli through its own peculiar senses. The goal is not to imitate human
intelligence but to ask, in the spirit of Nagel's "what is it like to be a bat?",
what kind of intelligence-like internal structure emerges from a *particular*
sensorium.

Input is modelled as a continuous sensory field, not isolated parsed events:
environmental flux -> external read-only feeders -> sensory membrane -> receptor
state update -> continuous sensory field -> novelty/absence/rhythm/cross-modal
detection -> Stimulus -> internal adaptation -> changed future perception. The
sensorium is plural: human-like modalities are valid, non-human and
machine-native modalities are equally valid, and human ontology never dominates
by default. No modality is privileged, human labels are never ground truth, and
nothing here controls hardware, captures media, touches the network, modifies a
source, or actuates the real world.
"""

from __future__ import annotations

from .absence_detection import (
    AbsenceDetector,
    AbsenceEvent,
    ExpectedSignal,
)
from .attention import (
    AttentionShift,
    SensoriumAttentionPolicy,
    SensoriumAttentionState,
)
from .baseline import (
    BaselineEstimator,
    BaselineShift,
    PerceptualBaseline,
)
from .cross_modal import (
    CrossModalDetector,
    CrossModalEvent,
    CrossModalRelation,
)
from .event_envelope import (
    AnnotationStatus,
    SensoryEventEnvelope,
    TrustLevel,
)
from .external_feeders import (
    ExternalFeederDescriptor,
    FeederSourceType,
    FeederTrustLevel,
    fixture_feeder,
)
from .flux_detection import FluxDetector, FluxEvent, FluxType
from .grounding import (
    GroundingQuality,
    SensoriumGroundingAnalyzer,
    SensoriumGroundingRecord,
)
from .invariant_detection import (
    InvariantCandidate,
    InvariantDetector,
    SensoriumInvariant,
)
from .modality import (
    ModalityClass,
    ModalityFamily,
    ModalityStatus,
    SensoriumModality,
    family_for_hint,
    modality_class_for,
)
from .receptors import (
    Receptor,
    ReceptorAdaptation,
    ReceptorSensitivity,
    ReceptorState,
)
from .reports import PluralSensoriumReport, PluralSensoriumReportBuilder
from .rhythm_detection import RhythmDetector, RhythmSignature
from .safety import HARD_RULES, PluralSensoriumSafetyValidator
from .sensorium_runtime import PluralSensoriumRuntime, SensoriumMilestone
from .sensory_field import (
    FieldContinuity,
    FieldPressure,
    SensoryField,
    SensoryFieldState,
)
from .stream_adapters import (
    StreamReadResult,
    read_csv_stream,
    read_feeder,
    read_fixture_replay,
    read_jsonl_stream,
    read_text_log,
    read_watched_folder,
)

__all__ = [
    "AbsenceDetector", "AbsenceEvent", "ExpectedSignal",
    "AttentionShift", "SensoriumAttentionPolicy", "SensoriumAttentionState",
    "BaselineEstimator", "BaselineShift", "PerceptualBaseline",
    "CrossModalDetector", "CrossModalEvent", "CrossModalRelation",
    "AnnotationStatus", "SensoryEventEnvelope", "TrustLevel",
    "ExternalFeederDescriptor", "FeederSourceType", "FeederTrustLevel",
    "fixture_feeder",
    "FluxDetector", "FluxEvent", "FluxType",
    "GroundingQuality", "SensoriumGroundingAnalyzer", "SensoriumGroundingRecord",
    "InvariantCandidate", "InvariantDetector", "SensoriumInvariant",
    "ModalityClass", "ModalityFamily", "ModalityStatus", "SensoriumModality",
    "family_for_hint", "modality_class_for",
    "Receptor", "ReceptorAdaptation", "ReceptorSensitivity", "ReceptorState",
    "PluralSensoriumReport", "PluralSensoriumReportBuilder",
    "RhythmDetector", "RhythmSignature",
    "HARD_RULES", "PluralSensoriumSafetyValidator",
    "PluralSensoriumRuntime", "SensoriumMilestone",
    "FieldContinuity", "FieldPressure", "SensoryField", "SensoryFieldState",
    "StreamReadResult", "read_csv_stream", "read_feeder", "read_fixture_replay",
    "read_jsonl_stream", "read_text_log", "read_watched_folder",
]

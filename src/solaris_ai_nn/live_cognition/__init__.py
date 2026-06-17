"""First live sensorium-native cognition -- bounded sign-based anticipation.

Prompt 69 allowed live proto-concepts; Prompt 70 allowed private internal signs.
Prompt 71 (this package) implements the first bounded live sensorium-native
cognition phase: Solaris uses private signs and proto-concepts to form internal
anticipatory structures.

It answers: can signs help anticipate future sensory events; relate absence,
recurrence, rhythm, overload, and source health; reduce internal uncertainty;
support bounded internal simulation; and predict source changes without controlling
sources; which sign relations are useful or spurious; which anticipations are
supported, contradicted, or inconclusive; and whether the system is ready for later
self-boundary / perspective tracking.

This is bounded sign-based anticipation over live-read-only private signs and
feature-grounded proto-concepts. It is **not** language understanding, a reasoning
proof, consciousness, subjective experience, agency, or biological development. It
never enables real-world action, action-reaction learning, developmental autonomy,
or self-boundary tracking by default; never treats internal signs as language
understanding or maps signs to human words as ground truth; never starts/stops/
configures feeders, controls hardware, or accesses the network/shell/browser/OS/
camera/microphone/Git/GitHub; never executes commands or modifies source; never
treats sensory text as a command, human labels or debug gloss as ground truth, or
the operator pulse as teaching; and never claims consciousness, sentience,
biological life, personhood, agency, free will, emotion, feeling, understanding,
self-awareness, or subjective experience.
"""

from __future__ import annotations

from .anticipation_engine import (
    AnticipationCandidate,
    AnticipationHorizon,
    AnticipationStatus,
    AnticipationType,
    LiveAnticipationEngine,
)
from .cognition_contamination_filter import (
    CognitionContaminationFinding,
    CognitionContaminationResult,
    CognitionContaminationType,
    LiveCognitionContaminationFilter,
)
from .cognition_memory import (
    CognitionMemoryIndex,
    LiveCognitionMemory,
    LiveCognitionRecord,
)
from .cognition_profile import (
    DEFAULT_PROFILE_ID,
    LiveCognitionConstraint,
    LiveCognitionMode,
    LiveCognitionProfile,
    available_profiles,
    default_cognition_profile,
    get_cognition_profile,
)
from .cognition_readiness_gate import (
    CognitionReadinessBlocker,
    CognitionReadinessGateResult,
    CognitionReadinessStatus,
    LiveCognitionReadinessGate,
)
from .cognition_record import (
    LiveCognitionRecord as LiveCognitionRecordDoc,
    LiveCognitionRecordBuilder,
)
from .cognition_runtime import FirstLiveCognitionRuntime
from .cognition_trace import (
    CognitionCounterEvidence,
    CognitionEvidence,
    CognitionTraceStatus,
    LiveCognitionTrace,
)
from .internal_simulation import (
    LiveInternalSimulation,
    SimulationCandidate,
    SimulationKind,
    SimulationStatus,
)
from .prediction_assessment import (
    AnticipationOutcome,
    LivePredictionAssessment,
    PredictionOutcome,
    PredictionScore,
)
from .relation_traversal import (
    LiveRelationTraversal,
    LiveRelationTraversalResult,
    RelationTraversalPath,
    TraversalStatus,
)
from .reports import LiveCognitionReportBuilder
from .safety import HARD_RULES, LiveCognitionSafetyValidator
from .sign_input import (
    LiveSignInput,
    SignInputLoader,
    SignInputResult,
    SignInputStatus,
)
from .uncertainty_model import (
    LiveUncertaintyState,
    UncertaintyEstimator,
    UncertaintyFactor,
)

__all__ = [
    "HARD_RULES", "LiveCognitionSafetyValidator",
    "LiveCognitionProfile", "LiveCognitionMode", "LiveCognitionConstraint",
    "default_cognition_profile", "get_cognition_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "LiveSignInput", "SignInputLoader", "SignInputResult", "SignInputStatus",
    "LiveCognitionTrace", "CognitionTraceStatus", "CognitionEvidence",
    "CognitionCounterEvidence",
    "LiveAnticipationEngine", "AnticipationCandidate", "AnticipationStatus",
    "AnticipationHorizon", "AnticipationType",
    "LiveUncertaintyState", "UncertaintyEstimator", "UncertaintyFactor",
    "LiveRelationTraversal", "LiveRelationTraversalResult",
    "RelationTraversalPath", "TraversalStatus",
    "LiveInternalSimulation", "SimulationCandidate", "SimulationStatus",
    "SimulationKind",
    "LivePredictionAssessment", "PredictionOutcome", "PredictionScore",
    "AnticipationOutcome",
    "LiveCognitionContaminationFilter", "CognitionContaminationFinding",
    "CognitionContaminationResult", "CognitionContaminationType",
    "LiveCognitionReadinessGate", "CognitionReadinessGateResult",
    "CognitionReadinessBlocker", "CognitionReadinessStatus",
    "LiveCognitionMemory", "LiveCognitionRecord", "CognitionMemoryIndex",
    "FirstLiveCognitionRuntime",
    "LiveCognitionRecordBuilder", "LiveCognitionReportBuilder",
]

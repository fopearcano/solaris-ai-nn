"""First live ontogenesis -- conservative, feature-grounded proto-concept formation.

Prompt 67 opened the live-read-only membrane; Prompt 68 observed source health,
source diet, rhythm, absence, overload, deprivation, and metabolism calibration.
Prompt 69 (this package) implements the first live ontogenesis phase: limited
proto-concept formation from validated real environmental flux.

It answers: are there recurring live feature patterns; which are stable enough to be
proto-concept candidates; which are source-specific artifacts; which are fixture-like
or label-contaminated; which survive absence, noise, and recurrence tests; which
should be born, weakened, suspended, or rejected; is the field ready for later
semiogenesis; and what evidence and counterevidence bear on each candidate.

This is feature-grounded proto-concept formation from live-read-only environmental
recurrence. It is **not** semantic learning from human labels, language acquisition,
symbolic understanding, consciousness, or biological development. It never enables
semiogenesis, action-reaction learning, or developmental autonomy by default; never
starts/stops/configures feeders, controls hardware, or accesses the network/shell/
browser/OS/camera/microphone/Git/GitHub; never executes commands or modifies source;
never treats sensory text as a command or human labels / debug gloss as ground truth;
never treats the operator pulse as teaching; and never claims consciousness,
sentience, biological life, personhood, agency, free will, emotion, feeling,
understanding, self-awareness, or subjective experience.
"""

from __future__ import annotations

from .concept_birth_gate import (
    ConceptBirthBlocker,
    ConceptBirthGateResult,
    ConceptBirthGateStatus,
    LiveConceptBirthGate,
)
from .concept_memory import (
    ConceptMemoryIndex,
    LiveConceptMemory,
    LiveConceptRecord,
)
from .contamination_filter import (
    ContaminationFinding,
    ContaminationResult,
    ContaminationType,
    LiveOntogenesisContaminationFilter,
)
from .feature_extraction import (
    FeatureExtractionResult,
    LiveFeatureExtractor,
    LiveFeatureVector,
)
from .ontogenesis_profile import (
    DEFAULT_PROFILE_ID,
    LiveOntogenesisConstraint,
    LiveOntogenesisMode,
    LiveOntogenesisProfile,
    available_profiles,
    default_ontogenesis_profile,
    get_ontogenesis_profile,
)
from .ontogenesis_record import (
    LiveOntogenesisRecord,
    LiveOntogenesisRecordBuilder,
)
from .ontogenesis_runtime import FirstLiveOntogenesisRuntime
from .proto_concept_candidate import (
    CandidateCounterEvidence,
    CandidateEvidence,
    LiveProtoConceptCandidate,
    ProtoConceptCandidateStatus,
)
from .recurrence_tracker import (
    LiveRecurrenceTracker,
    RecurrencePattern,
    RecurrenceStrength,
)
from .reports import LiveOntogenesisReportBuilder
from .safety import HARD_RULES, LiveOntogenesisSafetyValidator
from .stability_scoring import (
    LiveConceptStabilityScore,
    StabilityFactor,
    StabilityScorer,
)

__all__ = [
    "HARD_RULES", "LiveOntogenesisSafetyValidator",
    "LiveOntogenesisProfile", "LiveOntogenesisMode",
    "LiveOntogenesisConstraint", "default_ontogenesis_profile",
    "get_ontogenesis_profile", "available_profiles", "DEFAULT_PROFILE_ID",
    "LiveFeatureVector", "LiveFeatureExtractor", "FeatureExtractionResult",
    "LiveProtoConceptCandidate", "ProtoConceptCandidateStatus",
    "CandidateEvidence", "CandidateCounterEvidence",
    "LiveRecurrenceTracker", "RecurrencePattern", "RecurrenceStrength",
    "LiveConceptStabilityScore", "StabilityScorer", "StabilityFactor",
    "LiveOntogenesisContaminationFilter", "ContaminationFinding",
    "ContaminationResult", "ContaminationType",
    "LiveConceptBirthGate", "ConceptBirthGateResult", "ConceptBirthBlocker",
    "ConceptBirthGateStatus",
    "LiveConceptMemory", "LiveConceptRecord", "ConceptMemoryIndex",
    "FirstLiveOntogenesisRuntime",
    "LiveOntogenesisRecord", "LiveOntogenesisRecordBuilder",
    "LiveOntogenesisReportBuilder",
]

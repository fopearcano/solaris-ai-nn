"""First live semiogenesis -- private sign formation over live proto-concepts.

Prompt 69 allowed limited live proto-concept formation from validated feature
recurrence. Prompt 70 (this package) implements the first live semiogenesis phase:
Solaris generates **private internal signs** for stable live proto-concepts.

It answers: which proto-concepts are stable enough to receive signs; which sign
candidates are internally useful (reduce ambiguity, compression cost, or retrieval
friction, or relate recurring patterns across sources); which signs are contaminated
by human labels, debug gloss, or operator text; which are merely source artifacts;
which should be born, deferred, suspended, or rejected; whether the system is ready
for later sensorium-native cognition; and what evidence and counterevidence bear on
each sign.

This is private sign formation over feature-grounded live proto-concepts. It is
**not** language acquisition, semantic understanding, a proof of symbolic
intelligence, consciousness, or biological development. It never enables full
cognition, action-reaction learning, or developmental autonomy by default; never
treats internal signs as language understanding or maps signs to human words as
ground truth; never starts/stops/configures feeders, controls hardware, or accesses
the network/shell/browser/OS/camera/microphone/Git/GitHub; never executes commands
or modifies source; never treats sensory text as a command, human labels or debug
gloss as ground truth, or the operator pulse as teaching; and never claims
consciousness, sentience, biological life, personhood, agency, free will, emotion,
feeling, understanding, self-awareness, or subjective experience.
"""

from __future__ import annotations

from .concept_input import (
    ConceptInputLoader,
    ConceptInputResult,
    ConceptInputStatus,
    LiveConceptInput,
)
from .private_syntax import (
    LivePrivateSyntaxRelation,
    PrivateSyntaxBuilder,
    PrivateSyntaxGraph,
    PrivateSyntaxRelationType,
)
from .reports import LiveSemiogenesisReportBuilder
from .safety import HARD_RULES, LiveSemiogenesisSafetyValidator
from .semiogenesis_profile import (
    DEFAULT_PROFILE_ID,
    LiveSemiogenesisConstraint,
    LiveSemiogenesisMode,
    LiveSemiogenesisProfile,
    available_profiles,
    default_semiogenesis_profile,
    get_semiogenesis_profile,
)
from .semiogenesis_record import (
    LiveSemiogenesisRecord,
    LiveSemiogenesisRecordBuilder,
)
from .semiogenesis_runtime import FirstLiveSemiogenesisRuntime
from .sign_birth_gate import (
    LiveSignBirthGate,
    SignBirthBlocker,
    SignBirthGateResult,
    SignBirthGateStatus,
)
from .sign_candidate import (
    LiveSignCandidate,
    SignCandidateStatus,
    SignCounterEvidence,
    SignEvidence,
)
from .sign_contamination_filter import (
    LiveSignContaminationFilter,
    SignContaminationFinding,
    SignContaminationResult,
    SignContaminationType,
)
from .sign_generator import (
    GeneratedSignToken,
    LivePrivateSignGenerator,
    SignGenerationResult,
)
from .sign_memory import LiveSignMemory, LiveSignRecord, SignMemoryIndex
from .sign_utility import (
    LiveSignUtilityAssessment,
    SignUtilityFactor,
    SignUtilityScore,
)

__all__ = [
    "HARD_RULES", "LiveSemiogenesisSafetyValidator",
    "LiveSemiogenesisProfile", "LiveSemiogenesisMode",
    "LiveSemiogenesisConstraint", "default_semiogenesis_profile",
    "get_semiogenesis_profile", "available_profiles", "DEFAULT_PROFILE_ID",
    "LiveConceptInput", "ConceptInputLoader", "ConceptInputResult",
    "ConceptInputStatus",
    "LiveSignCandidate", "SignCandidateStatus", "SignEvidence",
    "SignCounterEvidence",
    "LivePrivateSignGenerator", "GeneratedSignToken", "SignGenerationResult",
    "LiveSignUtilityAssessment", "SignUtilityScore", "SignUtilityFactor",
    "LivePrivateSyntaxRelation", "PrivateSyntaxGraph",
    "PrivateSyntaxRelationType", "PrivateSyntaxBuilder",
    "LiveSignContaminationFilter", "SignContaminationFinding",
    "SignContaminationResult", "SignContaminationType",
    "LiveSignBirthGate", "SignBirthGateResult", "SignBirthBlocker",
    "SignBirthGateStatus",
    "LiveSignMemory", "LiveSignRecord", "SignMemoryIndex",
    "FirstLiveSemiogenesisRuntime",
    "LiveSemiogenesisRecord", "LiveSemiogenesisRecordBuilder",
    "LiveSemiogenesisReportBuilder",
]

"""Environmental membrane core -- the perceptual boundary organ.

The Environmental Membrane (Prompt 72) is a first-class architectural organ: external
events never flow directly into internal modules. The path is external feeders ->
Live Birth inbox -> event validator -> **Environmental Membrane** -> sensory
impressions -> Plural Sensorium -> Perceptual Metabolism -> Live Observation ->
Ontogenesis -> Semiogenesis -> Cognition.

Validation says valid/invalid. The membrane says allowed / blocked / attenuated /
amplified / deferred / quarantined / metabolically-risky / source-dominant /
operator-contaminated / safe-impression. It decides what enters, what is blocked,
what is attenuated/amplified, what becomes absence/overload/deprivation, what is
noise or contamination, what source pressure exists, what receptor handled the
signal, and what internal sensory impression is produced.

It never starts/stops/configures feeders, controls hardware, accesses the network/
shell/browser/OS/camera/microphone/Git/GitHub, executes commands, modifies source or
the feeder registry/governance, lets raw events bypass it into ontogenesis/
semiogenesis/cognition, treats sensory text as a command or human labels/debug gloss
as ground truth or the operator pulse as teaching, or claims consciousness, sentience,
biological life, personhood, agency, free will, emotion, feeling, understanding,
self-awareness, or subjective experience.
"""

from __future__ import annotations

from .contamination import (
    MembraneContaminationAnalyzer,
    MembraneContaminationAssessment,
    MembraneContaminationFinding,
    MembraneContaminationType,
)
from .immune_response import (
    ImmuneResponseAction,
    ImmuneResponseRecord,
    MembraneImmuneResponse,
)
from .membrane_memory import (
    MembraneMemory,
    MembraneMemoryRecord,
    MembraneSourceMemory,
)
from .membrane_profile import (
    DEFAULT_PROFILE_ID,
    EnvironmentalMembraneProfile,
    MembraneConstraint,
    MembraneProfileMode,
    available_profiles,
    default_membrane_profile,
    get_membrane_profile,
)
from .membrane_runtime import EnvironmentalMembraneRuntime
from .permeability import (
    MembranePermeabilityGate,
    PermeabilityDecision,
    PermeabilityFactor,
    PermeabilityStatus,
)
from .receptor_field import (
    EnvironmentalReceptorField,
    MembraneReceptor,
    ReceptorKind,
    ReceptorMatchResult,
)
from .reports import EnvironmentalMembraneReportBuilder
from .safety import HARD_RULES, EnvironmentalMembraneSafetyValidator
from .salience_modulation import (
    MembraneSalienceModulator,
    SalienceFactor,
    SalienceScore,
)
from .sensory_impression import (
    SensoryImpression,
    SensoryImpressionGrounding,
    SensoryImpressionKind,
    SensoryImpressionQuality,
    SensoryImpressionStore,
)
from .source_pressure import (
    MembraneSourcePressure,
    SourcePressureAssessment,
    SourcePressureStatus,
)

__all__ = [
    "HARD_RULES", "EnvironmentalMembraneSafetyValidator",
    "EnvironmentalMembraneProfile", "MembraneProfileMode", "MembraneConstraint",
    "default_membrane_profile", "get_membrane_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "EnvironmentalReceptorField", "MembraneReceptor", "ReceptorKind",
    "ReceptorMatchResult",
    "MembranePermeabilityGate", "PermeabilityDecision", "PermeabilityStatus",
    "PermeabilityFactor",
    "SensoryImpression", "SensoryImpressionKind", "SensoryImpressionGrounding",
    "SensoryImpressionQuality", "SensoryImpressionStore",
    "MembraneSourcePressure", "SourcePressureAssessment", "SourcePressureStatus",
    "MembraneSalienceModulator", "SalienceScore", "SalienceFactor",
    "MembraneContaminationAnalyzer", "MembraneContaminationAssessment",
    "MembraneContaminationFinding", "MembraneContaminationType",
    "MembraneImmuneResponse", "ImmuneResponseAction", "ImmuneResponseRecord",
    "MembraneMemory", "MembraneMemoryRecord", "MembraneSourceMemory",
    "EnvironmentalMembraneRuntime", "EnvironmentalMembraneReportBuilder",
]

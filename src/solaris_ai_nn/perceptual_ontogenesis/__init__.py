"""Perceptual ontogenesis -- how an internal world begins to form from perception.

Prompts 41-46 gave Solaris-AI-NN a plural sensorium, external feeders, and a
perceptual metabolism. This layer adds *ontogenesis*: the gradual birth of
sensorium-native proto-concepts from repeated perceptual structures --

    continuous sensory field -> recurrent patterns -> perceptual atoms ->
    proto-concepts -> concept families -> world-forming relations ->
    memory stabilization -> future perception changes

A proto-concept is NOT a word and NOT a human category (person/object/room/dog/
sentence). It is a stabilized internal structure that helps Solaris compress,
predict, relate to, or respond to its sensorium. Human ontology is never the
default, human labels are never ground truth, and "world formation" here is an
observable internal *structural* world -- NOT subjective experience, qualia,
understanding, consciousness, sentience, life, personhood, agency, or free will.
Nothing here controls hardware, starts or controls a feeder, accesses the network,
runs a shell, modifies a source, or actuates the real world.
"""

from __future__ import annotations

from .concept_birth import (
    ConceptBirthCandidate,
    ConceptBirthEngine,
    ConceptBirthTrigger,
)
from .concept_family import (
    ConceptFamily,
    ConceptFamilyBuilder,
    ConceptFamilyRelation,
    ConceptFamilyType,
)
from .concept_memory import (
    ConceptMemoryIndex,
    ConceptMemoryRecord,
    ConceptMemoryStore,
)
from .contamination import (
    ConceptContaminationAnalyzer,
    ConceptContaminationReport,
)
from .decay import ConceptDecayEngine, DecayReason, DecayResult
from .ontogenesis_runtime import (
    OntogenesisMilestone,
    PerceptualOntogenesisRuntime,
)
from .perceptual_atoms import (
    PerceptualAtom,
    PerceptualAtomKind,
    PerceptualAtomSource,
    PerceptualAtomTrace,
)
from .proto_concepts import (
    ProtoConcept,
    ProtoConceptGrounding,
    ProtoConceptKind,
    ProtoConceptStatus,
    neutral_operational_name,
)
from .relation_growth import (
    ConceptRelation,
    ConceptRelationGrowthEngine,
    ConceptRelationType,
)
from .reports import PerceptualOntogenesisReportBuilder
from .safety import HARD_RULES, PerceptualOntogenesisSafetyValidator
from .stabilization import (
    ConceptStabilizationEngine,
    StabilityEvidence,
    StabilizationResult,
)
from .world_formation import (
    SensoriumWorld,
    WorldFormationBuilder,
    WorldFormationState,
)

__all__ = [
    "ConceptBirthCandidate", "ConceptBirthEngine", "ConceptBirthTrigger",
    "ConceptFamily", "ConceptFamilyBuilder", "ConceptFamilyRelation",
    "ConceptFamilyType",
    "ConceptMemoryIndex", "ConceptMemoryRecord", "ConceptMemoryStore",
    "ConceptContaminationAnalyzer", "ConceptContaminationReport",
    "ConceptDecayEngine", "DecayReason", "DecayResult",
    "OntogenesisMilestone", "PerceptualOntogenesisRuntime",
    "PerceptualAtom", "PerceptualAtomKind", "PerceptualAtomSource",
    "PerceptualAtomTrace",
    "ProtoConcept", "ProtoConceptGrounding", "ProtoConceptKind",
    "ProtoConceptStatus", "neutral_operational_name",
    "ConceptRelation", "ConceptRelationGrowthEngine", "ConceptRelationType",
    "PerceptualOntogenesisReportBuilder",
    "HARD_RULES", "PerceptualOntogenesisSafetyValidator",
    "ConceptStabilizationEngine", "StabilityEvidence", "StabilizationResult",
    "SensoriumWorld", "WorldFormationBuilder", "WorldFormationState",
]

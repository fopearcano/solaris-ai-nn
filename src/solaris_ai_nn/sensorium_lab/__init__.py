"""Sensorium differentiation lab -- do different senses build different worlds?

Prompts 41-43 gave Solaris-AI-NN a plural sensorium, an observable organism demo,
and a real read-only live field. This lab runs the comparative study they were
built for: it asks, in the spirit of Nagel's "what is it like to be a bat?", the
narrower and *observable* question -- does a different sensorium build a different
internal structure?

It compares human-like, non-human, machine-native, absence-heavy, mixed,
human-labelled, feature-only, passive, and adaptive sensorium configurations, and
produces world signatures, modality fingerprints, ontology-drift reports,
contamination analysis, structural metrics, and pairwise comparisons. This is a
structural differentiation study, not a task benchmark and not a consciousness
test: a world signature is an observable fingerprint, never subjective experience,
never qualia. No sensorium is ranked as "more conscious" or "more alive"; human
labels are always annotations, never ground truth; and no claim of consciousness,
sentience, life, personhood, agency, or free will is made.
"""

from __future__ import annotations

from .comparative_analysis import (
    DifferenceStrength,
    SensoriumComparison,
    SensoriumComparisonResult,
    SensoriumDifference,
)
from .differentiation_runner import (
    ArmRunResult,
    SensoriumDifferentiationRunner,
)
from .label_contamination import (
    ContaminationReport,
    ContaminationSource,
    HumanLabelContaminationAnalyzer,
)
from .modality_fingerprint import ModalityFingerprint, ModalityFingerprintBuilder
from .ontology_drift import (
    OntologyDrift,
    OntologyDriftDetector,
    OntologyDriftResult,
    OntologyKind,
)
from .safety import HARD_RULES, SensoriumLabSafetyValidator
from .sensorium_profiles import (
    SensoriumProfile,
    SensoriumProfileBuilder,
    SensoriumProfileType,
)
from .structure_metrics import SensoriumStructureMetrics
from .study_design import (
    SensoriumStudyArm,
    SensoriumStudyCondition,
    SensoriumStudyDesign,
    SensoriumStudyResult,
    default_study_design,
)
from .study_report import SensoriumDifferentiationStudyReportBuilder
from .world_signature import (
    SensoriumWorldSignature,
    WorldSignatureBuilder,
    WorldSignatureComparison,
)

__all__ = [
    "DifferenceStrength", "SensoriumComparison", "SensoriumComparisonResult",
    "SensoriumDifference",
    "ArmRunResult", "SensoriumDifferentiationRunner",
    "ContaminationReport", "ContaminationSource",
    "HumanLabelContaminationAnalyzer",
    "ModalityFingerprint", "ModalityFingerprintBuilder",
    "OntologyDrift", "OntologyDriftDetector", "OntologyDriftResult",
    "OntologyKind",
    "HARD_RULES", "SensoriumLabSafetyValidator",
    "SensoriumProfile", "SensoriumProfileBuilder", "SensoriumProfileType",
    "SensoriumStructureMetrics",
    "SensoriumStudyArm", "SensoriumStudyCondition", "SensoriumStudyDesign",
    "SensoriumStudyResult", "default_study_design",
    "SensoriumDifferentiationStudyReportBuilder",
    "SensoriumWorldSignature", "WorldSignatureBuilder",
    "WorldSignatureComparison",
]

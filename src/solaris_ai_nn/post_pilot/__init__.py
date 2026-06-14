"""Post-pilot developmental forensics -- a long run is only valuable if it is
analyzable.

After Pilot-1 (or any long-horizon run), this package reads the run's own
artifacts and asks: did the system merely accumulate data, or did it
structurally change for traceable reasons? It loads artifacts read-only,
compares baselines, distinguishes accumulation from growth, audits
traceability, builds an evidence ledger, detects regression, packages
reproducibility material, applies a Phase-2 decision gate, and produces a
research dossier and post-pilot report.

It never claims consciousness, sentience, understanding, or life; never treats
operational success as cognitive proof; never reclassifies simulated time as
real; and never deletes or edits raw evidence.
"""

from __future__ import annotations

from .accumulation_vs_growth import (
    AccumulationVsGrowthAnalyzer,
    GrowthClassification,
    GrowthDiscriminationResult,
)
from .artifact_loader import (
    ArtifactIndex,
    PilotArtifactLoader,
    PilotArtifactSet,
)
from .baseline import (
    BaselineComparator,
    BaselineComparison,
    BaselineSnapshot,
)
from .decision_gate import (
    DecisionGateResult,
    DecisionOption,
    Phase2DecisionGate,
)
from .developmental_evidence import (
    ClaimType,
    DevelopmentalClaim,
    DevelopmentalEvidenceLedger,
    EvidenceStrength,
)
from .forensics import PostPilotForensics
from .regression_analysis import (
    RegressionAnalyzer,
    RegressionNextStep,
    RegressionReport,
    RegressionSeverity,
    RegressionSignal,
)
from .reports import PostPilotAnalysis, PostPilotReportBuilder
from .reproducibility import (
    ReproducibilityPackage,
    ReproducibilityPackager,
)
from .research_dossier import ResearchDossier, ResearchDossierBuilder
from .safety import HARD_RULES, PostPilotSafetyReport, PostPilotSafetyValidator
from .sensory_exposure import (
    SensoryExposureClassification,
    SensoryExposureComparison,
    classify_sensory_exposure,
)
from .structural_change import (
    Stability,
    StructuralChangeAnalyzer,
    StructuralChangeCategory,
    StructuralChangeEvidence,
)
from .trace_audit import DevelopmentalTraceAuditor, TraceAuditResult

__all__ = [
    # loader
    "PilotArtifactLoader", "PilotArtifactSet", "ArtifactIndex",
    # baseline
    "BaselineComparator", "BaselineComparison", "BaselineSnapshot",
    # structural change
    "StructuralChangeAnalyzer", "StructuralChangeEvidence",
    "StructuralChangeCategory", "Stability",
    # accumulation vs growth
    "AccumulationVsGrowthAnalyzer", "GrowthDiscriminationResult",
    "GrowthClassification",
    # trace audit / evidence
    "DevelopmentalTraceAuditor", "TraceAuditResult",
    "DevelopmentalEvidenceLedger", "DevelopmentalClaim", "ClaimType",
    "EvidenceStrength",
    # regression
    "RegressionAnalyzer", "RegressionReport", "RegressionSignal",
    "RegressionSeverity", "RegressionNextStep",
    # reproducibility / decision / dossier / report
    "ReproducibilityPackager", "ReproducibilityPackage",
    "Phase2DecisionGate", "DecisionGateResult", "DecisionOption",
    "ResearchDossierBuilder", "ResearchDossier",
    "PostPilotReportBuilder", "PostPilotAnalysis",
    # forensics façade / safety
    "PostPilotForensics",
    "PostPilotSafetyValidator", "PostPilotSafetyReport", "HARD_RULES",
    # sensory-exposure comparison (Pilot-2)
    "classify_sensory_exposure", "SensoryExposureComparison",
    "SensoryExposureClassification",
]

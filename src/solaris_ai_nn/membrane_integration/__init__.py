"""Membrane integration across the live pipeline -- audit and enforcement.

Prompt 72 created the Environmental Membrane; Prompt 73 (this package) integrates it
into the live pipeline so the correct path becomes: external feeders -> Live Birth
inbox -> event validator -> Environmental Membrane -> sensory impressions -> Plural
Sensorium -> Perceptual Metabolism -> Live Observation -> Ontogenesis -> Semiogenesis
-> Cognition -> Scientific Claims / Research Cycle / Reports.

Raw events remain available for audit and debugging, but downstream organismic
modules should primarily consume sensory impressions. This layer answers: did a
module use impressions or raw events; which membrane report and receptor and
permeability decision were involved; which impression supported each proto-concept /
sign / cognition trace; did contamination or operator-text dominance propagate
downstream; and did any module bypass the membrane (and was the bypass allowed,
warned, or blocked).

It is an architectural audit/enforcement layer, not a new theory layer. It is bounded
and local-only; it never starts/stops/configures feeders, controls hardware, accesses
the network/shell/browser/OS/Git/GitHub, executes commands, modifies source or
governance, lets raw events silently bypass the membrane into ontogenesis/
semiogenesis/cognition, or claims consciousness, sentience, biological life,
personhood, agency, free will, emotion, feeling, understanding, self-awareness, or
subjective experience.
"""

from __future__ import annotations

from .ancestry import (
    AncestryValidationResult,
    MembraneAncestryBuilder,
    MembraneAncestryChain,
    MembraneAncestryRef,
)
from .bypass_detector import (
    MembraneBypassDetector,
    MembraneBypassFinding,
    MembraneBypassSeverity,
)
from .downstream_contracts import (
    DownstreamContractRequirement,
    DownstreamContractStatus,
    MembraneDownstreamContract,
    evaluate_contracts,
)
from .impression_loader import (
    ImpressionLoadResult,
    LoadedSensoryImpression,
    SensoryImpressionLoader,
)
from .integration_profile import (
    DEFAULT_PROFILE_ID,
    MembraneIntegrationConstraint,
    MembraneIntegrationMode,
    MembraneIntegrationProfile,
    available_profiles,
    default_integration_profile,
    get_integration_profile,
)
from .integration_runtime import MembraneIntegrationRuntime
from .module_adapters import (
    AdapterResult,
    AlphaSystemMembraneAdapter,
    LiveBirthMembraneAdapter,
    LiveCognitionMembraneAdapter,
    LiveObservationMembraneAdapter,
    LiveOntogenesisMembraneAdapter,
    LiveSemiogenesisMembraneAdapter,
    ResearchCycleMembraneAdapter,
    ScientificClaimsMembraneAdapter,
)
from .pipeline_audit import (
    MembranePipelineAudit,
    PipelineAuditResult,
    PipelineAuditStage,
    PipelineAuditStatus,
)
from .reports import MembraneIntegrationReportBuilder
from .safety import HARD_RULES, MembraneIntegrationSafetyValidator

__all__ = [
    "HARD_RULES", "MembraneIntegrationSafetyValidator",
    "MembraneIntegrationProfile", "MembraneIntegrationMode",
    "MembraneIntegrationConstraint", "default_integration_profile",
    "get_integration_profile", "available_profiles", "DEFAULT_PROFILE_ID",
    "SensoryImpressionLoader", "LoadedSensoryImpression", "ImpressionLoadResult",
    "MembraneAncestryRef", "MembraneAncestryChain", "AncestryValidationResult",
    "MembraneAncestryBuilder",
    "MembraneDownstreamContract", "DownstreamContractStatus",
    "DownstreamContractRequirement", "evaluate_contracts",
    "MembraneBypassDetector", "MembraneBypassFinding", "MembraneBypassSeverity",
    "AdapterResult", "LiveBirthMembraneAdapter",
    "LiveObservationMembraneAdapter", "LiveOntogenesisMembraneAdapter",
    "LiveSemiogenesisMembraneAdapter", "LiveCognitionMembraneAdapter",
    "ScientificClaimsMembraneAdapter", "ResearchCycleMembraneAdapter",
    "AlphaSystemMembraneAdapter",
    "MembranePipelineAudit", "PipelineAuditResult", "PipelineAuditStage",
    "PipelineAuditStatus",
    "MembraneIntegrationRuntime", "MembraneIntegrationReportBuilder",
]

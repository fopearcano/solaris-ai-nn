"""Cross-run developmental replication and falsification lab.

Prompt 54 produced a month-scale developmental soak protocol; one soak is not
evidence enough. This package tests *replication*:

    register runs -> build experimental lineages -> align run structures ->
    structural similarity -> divergence -> environmental dependency ->
    bounded falsification tests -> replication matrix -> conservative reports

The central question is: *do independent Solaris runs produce comparable
structural development under comparable sensorium conditions, and meaningfully
different development under different sensorium conditions?* -- not "did it
become conscious / alive / understand / become an agent?".

It compares and falsifies the soak/developmental evidence; it does not duplicate
that logic. A "developmental lineage" is experimental provenance, NOT biological
ancestry. Everything is bounded: it compares existing artifacts by default,
launches no unbounded soak, starts no feeders, controls no hardware, touches no
network/shell/browser/OS, modifies no source artifact, uses no human teaching
loop, and makes no claim of biological life, consciousness, sentience,
personhood, agency, free will, emotion, feeling, understanding, or subjective
experience. Diverged, falsified, and inconclusive evidence is always preserved.
"""

from __future__ import annotations

from .cross_run_alignment import (
    AlignmentResult,
    AlignmentStatus,
    AlignmentTarget,
    CrossRunAlignment,
)
from .divergence import (
    DevelopmentalDivergence,
    DivergenceDetector,
    DivergenceReason,
)
from .environmental_dependency import (
    DependencyFactor,
    DependencyStrength,
    EnvironmentalDependency,
    EnvironmentalDependencyAnalyzer,
)
from .falsification import (
    FalsificationFinding,
    FalsificationOutcome,
    FalsificationResult,
    FalsificationTest,
    FalsificationTestType,
)
from .lineage import (
    DevelopmentalLineage,
    LineageComparison,
    LineageNode,
    LineageRelation,
)
from .replication_matrix import (
    ReplicationCellStatus,
    ReplicationMatrix,
    ReplicationMatrixBuilder,
    ReplicationMatrixCell,
)
from .replication_plan import (
    ReplicationArm,
    ReplicationCondition,
    ReplicationConstraint,
    ReplicationPlan,
)
from .replication_runtime import DevelopmentalReplicationRuntime
from .reports import DevelopmentalReplicationReportBuilder
from .run_registry import (
    DevelopmentalRunRegistry,
    RegisteredDevelopmentalRun,
    RunArtifactIndex,
)
from .safety import HARD_RULES, DevelopmentalReplicationSafetyValidator
from .structural_similarity import (
    StructuralSimilarity,
    StructuralSimilarityMetric,
    StructuralSimilarityResult,
)

__all__ = [
    "ReplicationPlan", "ReplicationArm", "ReplicationCondition",
    "ReplicationConstraint",
    "DevelopmentalRunRegistry", "RegisteredDevelopmentalRun", "RunArtifactIndex",
    "DevelopmentalLineage", "LineageNode", "LineageRelation",
    "LineageComparison",
    "CrossRunAlignment", "AlignmentTarget", "AlignmentResult", "AlignmentStatus",
    "StructuralSimilarity", "StructuralSimilarityMetric",
    "StructuralSimilarityResult",
    "DevelopmentalDivergence", "DivergenceDetector", "DivergenceReason",
    "EnvironmentalDependency", "EnvironmentalDependencyAnalyzer",
    "DependencyStrength", "DependencyFactor",
    "FalsificationTest", "FalsificationResult", "FalsificationFinding",
    "FalsificationTestType", "FalsificationOutcome",
    "ReplicationMatrix", "ReplicationMatrixCell", "ReplicationMatrixBuilder",
    "ReplicationCellStatus",
    "DevelopmentalReplicationRuntime",
    "DevelopmentalReplicationReportBuilder",
    "HARD_RULES", "DevelopmentalReplicationSafetyValidator",
]

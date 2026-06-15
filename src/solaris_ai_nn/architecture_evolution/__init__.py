"""Architecture evolution -- evidence-based governance, not self-programming.

Prompt 37 built the research lab that tests modules, baselines, ablations, and
null models. This package turns that evidence into *disciplined architecture
decisions*: research results -> module effect analysis -> architecture decision
record -> pruning / promotion / quarantine proposal -> impact analysis ->
migration plan -> roadmap -> operator review.

This is not self-programming, recursive self-improvement, or automatic
refactoring. Every output is a planning artifact (an inventory, a lifecycle
assessment, an ADR, a pruning *proposal*, an impact analysis, a migration *plan*,
a design-debt item, a compiled roadmap, an architecture snapshot, a review
report, a changelog *plan*). Nothing here modifies source code, edits imports,
runs Git, or deletes a module; safety-critical modules cannot be pruned on
performance evidence alone; operator approval is recorded, never executed
automatically; and no consciousness, life, sentience, personhood, free-will, or
agency claim is made.
"""

from __future__ import annotations

from .architecture_snapshot import (
    ArchitectureDiff,
    ArchitectureSnapshot,
    ArchitectureSnapshotBuilder,
)
from .changelog_plan import ChangelogImpact, ChangelogItem, ChangelogPlan
from .decision_record import (
    ADRStore,
    ArchitectureDecisionRecord,
    DecisionRationale,
    DecisionStatus,
    DecisionType,
)
from .design_debt import (
    DEBT_CATEGORIES,
    DesignDebtItem,
    DesignDebtRegistry,
    DesignDebtSeverity,
)
from .evidence_mapper import (
    ArchitectureEvidenceMap,
    EvidenceLink,
    EvidenceStrength,
    action_reaction_revision_proposals,
    cognition_revision_proposals,
    desire_revision_proposals,
    ontogenesis_revision_proposals,
    self_boundary_revision_proposals,
    semiogenesis_revision_proposals,
)
from .impact_analysis import (
    ArchitectureImpactAnalysis,
    ImpactAnalyzer,
    ImpactArea,
    ImpactSeverity,
)
from .migration_plan import (
    MigrationPlan,
    MigrationRisk,
    MigrationStatus,
    MigrationStep,
    build_migration_plan,
)
from .module_inventory import (
    ModuleDependencyRecord,
    ModuleInventory,
    ModuleInventoryEntry,
)
from .module_lifecycle import (
    ModuleLifecycleAssessment,
    ModuleLifecycleClass,
    ModuleLifecycleClassifier,
)
from .promotion import (
    DemotionProposal,
    ModuleRoleChangePlan,
    PromotionProposal,
)
from .pruning import (
    PruningImplementationStatus,
    PruningPlan,
    PruningProposal,
    PruningProposalBuilder,
    PruningRisk,
)
from .review_report import (
    ArchitectureReviewReport,
    ArchitectureReviewReportBuilder,
)
from .roadmap_compiler import (
    RoadmapCompiler,
    RoadmapHorizon,
    RoadmapItem,
    RoadmapItemType,
    RoadmapPriority,
)
from .safety import (
    ArchitectureEvolutionSafetyValidator,
    ArchitectureSafetyReport,
    HARD_RULES,
)

__all__ = [
    # inventory / lifecycle / decision / evidence
    "ModuleInventory", "ModuleInventoryEntry", "ModuleDependencyRecord",
    "ModuleLifecycleClass", "ModuleLifecycleAssessment",
    "ModuleLifecycleClassifier", "ArchitectureDecisionRecord", "DecisionType",
    "DecisionStatus", "DecisionRationale", "ADRStore",
    "ArchitectureEvidenceMap", "EvidenceLink", "EvidenceStrength",
    "ontogenesis_revision_proposals", "semiogenesis_revision_proposals",
    "cognition_revision_proposals", "self_boundary_revision_proposals",
    "desire_revision_proposals", "action_reaction_revision_proposals",
    # pruning / promotion / impact / migration
    "PruningProposal", "PruningProposalBuilder", "PruningPlan", "PruningRisk",
    "PruningImplementationStatus", "PromotionProposal", "DemotionProposal",
    "ModuleRoleChangePlan", "ArchitectureImpactAnalysis", "ImpactAnalyzer",
    "ImpactArea", "ImpactSeverity", "MigrationPlan", "MigrationStep",
    "MigrationRisk", "MigrationStatus", "build_migration_plan",
    # debt / roadmap / snapshot / review / changelog / safety
    "DesignDebtItem", "DesignDebtRegistry", "DesignDebtSeverity",
    "DEBT_CATEGORIES", "RoadmapCompiler", "RoadmapItem", "RoadmapItemType",
    "RoadmapPriority", "RoadmapHorizon", "ArchitectureSnapshot",
    "ArchitectureSnapshotBuilder", "ArchitectureDiff",
    "ArchitectureReviewReport", "ArchitectureReviewReportBuilder",
    "ChangelogPlan", "ChangelogItem", "ChangelogImpact",
    "ArchitectureEvolutionSafetyValidator", "ArchitectureSafetyReport",
    "HARD_RULES",
]

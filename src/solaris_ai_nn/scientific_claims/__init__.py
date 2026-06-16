"""Scientific claim discipline -- map evidence to claims; block hype drift.

Prompts 41-61 built an experimental research architecture and a closed evidence
cycle. Prompt 62 adds the scientific claim discipline layer. It answers: *what can
we safely claim from the evidence, what is merely suggested, what is unsupported,
what is falsified, what is forbidden to claim, what evidence supports or
contradicts each claim, what further experiment is needed, and what may appear in
a paper / README / internal note?*

It is a scientific claim registry and publication evidence compiler -- not a
marketing generator, not hype production, and not a consciousness-declaration
system. It registers supported, weak, inconclusive, unsupported, contradicted,
falsified, and forbidden claims; maps evidence and counterevidence; maintains a
theory ledger; builds limitations, safe abstracts, and a draft publication
dossier; bridges ClaimGuard; and reads local artifacts and writes reports only. It
proves nothing about consciousness, sentience, biological life, personhood,
agency, free will, emotion, feeling, understanding, self-awareness, autonomous
self-improvement, or subjective experience.
"""

from __future__ import annotations

from .abstract_builder import (
    AbstractSafetyResult,
    AbstractVariant,
    ScientificAbstractBuilder,
)
from .claim_guard_bridge import ClaimGuardBridge, ClaimGuardBridgeResult
from .claim_registry import (
    ClaimCategory,
    ClaimRegistry,
    ClaimStatus,
    ScientificClaim,
)
from .claim_runtime import ScientificClaimRuntime
from .claim_strength import (
    ClaimStrength,
    ClaimStrengthEvaluator,
    ClaimStrengthReason,
    ClaimStrengthScore,
)
from .counterevidence import (
    CounterEvidenceAnalyzer,
    CounterEvidenceRecord,
    CounterEvidenceType,
)
from .evidence_mapping import EvidenceMap, EvidenceRole, MappedEvidence
from .forbidden_claims import (
    ForbiddenClaim,
    ForbiddenClaimDetector,
    ForbiddenClaimPolicy,
)
from .limitations_builder import (
    LimitationCategory,
    LimitationStatement,
    LimitationsBuilder,
)
from .publication_dossier import (
    PublicationDossier,
    PublicationDossierBuilder,
    PublicationReadinessStatus,
)
from .reports import ScientificClaimReportBuilder
from .safety import HARD_RULES, ScientificClaimSafetyValidator
from .theory_ledger import (
    THEORY_AREAS,
    TheoryLedger,
    TheoryRevision,
    TheoryStatement,
    TheoryStatus,
)

__all__ = [
    "ScientificClaim", "ClaimCategory", "ClaimStatus", "ClaimRegistry",
    "TheoryLedger", "TheoryStatement", "TheoryStatus", "TheoryRevision",
    "THEORY_AREAS",
    "EvidenceMap", "MappedEvidence", "EvidenceRole",
    "ClaimStrengthEvaluator", "ClaimStrengthScore", "ClaimStrengthReason",
    "ClaimStrength",
    "CounterEvidenceRecord", "CounterEvidenceType", "CounterEvidenceAnalyzer",
    "ForbiddenClaim", "ForbiddenClaimDetector", "ForbiddenClaimPolicy",
    "PublicationDossier", "PublicationDossierBuilder",
    "PublicationReadinessStatus",
    "ScientificAbstractBuilder", "AbstractVariant", "AbstractSafetyResult",
    "LimitationsBuilder", "LimitationStatement", "LimitationCategory",
    "ClaimGuardBridge", "ClaimGuardBridgeResult",
    "ScientificClaimRuntime",
    "ScientificClaimReportBuilder",
    "HARD_RULES", "ScientificClaimSafetyValidator",
]

"""Post-pilot developmental evidence ledger -- every claim needs evidence.

The :class:`DevelopmentalEvidenceLedger` records :class:`DevelopmentalClaim`s,
each of which must carry evidence references. A *strong* claim requires
multiple artifact types or stable persistence; a claim with no refs is
``unsupported``; and contradicted claims are highlighted. This is the audit
trail that keeps the post-pilot conclusions honest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ClaimType:
    CONTINUITY_SURVIVED = "continuity_survived"
    RESTART_IDENTITY_RECOVERED = "restart_identity_recovered"
    MEMORY_CONSOLIDATED = "memory_consolidated"
    HABIT_FORMED = "habit_formed"
    WORLD_MODEL_CHANGED = "world_model_changed"
    PROTO_SYMBOL_STABILIZED = "proto_symbol_stabilized"
    HYPOTHESIS_TESTED = "hypothesis_tested"
    LOGOS_TENSION_RESOLVED = "LOGOS_tension_resolved"
    DEGRADATION_REPAIRED = "degradation_repaired"
    ACTIVE_PERCEPTION_USEFUL = "active_perception_useful"
    MYSTERIUM_REORGANIZED = "Mysterium_reorganized"
    DEVELOPMENTAL_EPOCH_CHANGED = "developmental_epoch_changed"
    STRUCTURAL_GROWTH_DETECTED = "structural_growth_detected"
    MOSTLY_ACCUMULATION_DETECTED = "mostly_accumulation_detected"
    REGRESSION_DETECTED = "regression_detected"

    ALL = (CONTINUITY_SURVIVED, RESTART_IDENTITY_RECOVERED,
           MEMORY_CONSOLIDATED, HABIT_FORMED, WORLD_MODEL_CHANGED,
           PROTO_SYMBOL_STABILIZED, HYPOTHESIS_TESTED, LOGOS_TENSION_RESOLVED,
           DEGRADATION_REPAIRED, ACTIVE_PERCEPTION_USEFUL,
           MYSTERIUM_REORGANIZED, DEVELOPMENTAL_EPOCH_CHANGED,
           STRUCTURAL_GROWTH_DETECTED, MOSTLY_ACCUMULATION_DETECTED,
           REGRESSION_DETECTED)


class EvidenceStrength:
    UNSUPPORTED = "unsupported"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"

    ALL = (UNSUPPORTED, WEAK, MODERATE, STRONG, CONTRADICTED, INCONCLUSIVE)


@dataclass
class DevelopmentalClaim:
    """One developmental claim with its evidence and graded strength."""

    claim_type: str
    statement: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    artifact_types: List[str] = field(default_factory=list)
    persistent: bool = False
    contradicted: bool = False
    strength: str = EvidenceStrength.UNSUPPORTED
    notes: List[str] = field(default_factory=list)

    def grade(self) -> str:
        """Grade strength conservatively from refs/artifacts/persistence."""
        if self.contradicted:
            self.strength = EvidenceStrength.CONTRADICTED
        elif not self.evidence_refs:
            self.strength = EvidenceStrength.UNSUPPORTED
        elif len(set(self.artifact_types)) >= 2 or self.persistent:
            self.strength = EvidenceStrength.STRONG
        elif len(self.evidence_refs) >= 2:
            self.strength = EvidenceStrength.MODERATE
        else:
            self.strength = EvidenceStrength.WEAK
        return self.strength

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DevelopmentalEvidenceLedger:
    """Holds graded developmental claims; highlights contradicted ones."""

    claims: List[DevelopmentalClaim] = field(default_factory=list)

    def add(self, claim_type: str, statement: str = "",
            evidence_refs: Optional[List[str]] = None,
            artifact_types: Optional[List[str]] = None,
            persistent: bool = False,
            contradicted: bool = False,
            notes: Optional[List[str]] = None) -> DevelopmentalClaim:
        if claim_type not in ClaimType.ALL:
            raise ValueError(f"unknown claim type {claim_type!r}")
        claim = DevelopmentalClaim(
            claim_type=claim_type, statement=statement,
            evidence_refs=list(evidence_refs or []),
            artifact_types=list(artifact_types or []),
            persistent=persistent, contradicted=contradicted,
            notes=list(notes or []))
        claim.grade()
        self.claims.append(claim)
        return claim

    def from_structural_evidence(self, evidence: List[Any],
                                 ) -> List[DevelopmentalClaim]:
        """Derive ledger claims from structural-change evidence records."""
        out: List[DevelopmentalClaim] = []
        mapping = {
            "memory_reorganization": ClaimType.MEMORY_CONSOLIDATED,
            "stable_habit_formation": ClaimType.HABIT_FORMED,
            "world_model_pruning": ClaimType.WORLD_MODEL_CHANGED,
            "world_model_schema_emergence": ClaimType.WORLD_MODEL_CHANGED,
            "proto_symbol_stabilization": ClaimType.PROTO_SYMBOL_STABILIZED,
            "proto_symbol_emergence": ClaimType.PROTO_SYMBOL_STABILIZED,
            "hypothesis_to_world_model_update": ClaimType.HYPOTHESIS_TESTED,
            "LOGOS_tension_resolution": ClaimType.LOGOS_TENSION_RESOLVED,
            "auto_regeneration_repair_effect": ClaimType.DEGRADATION_REPAIRED,
            "developmental_epoch_transition":
                ClaimType.DEVELOPMENTAL_EPOCH_CHANGED,
            "identity_restart_continuity": ClaimType.CONTINUITY_SURVIVED,
            "unknown_pressure_reorganization": ClaimType.MYSTERIUM_REORGANIZED,
            "active_sampling_policy_shift": ClaimType.ACTIVE_PERCEPTION_USEFUL,
        }
        for e in evidence:
            ctype = mapping.get(getattr(e, "category", ""))
            if ctype is None:
                continue
            out.append(self.add(
                ctype,
                statement=f"{e.category} delta={getattr(e, 'metric_delta', 0)}",
                evidence_refs=[getattr(e, "evidence_id", "")]
                + list(getattr(e, "supporting_artifacts", [])),
                artifact_types=list(getattr(e, "supporting_artifacts", [])),
                persistent=getattr(e, "stability", "") == "persistent",
                notes=list(getattr(e, "limitations", []))))
        return out

    def contradicted_claims(self) -> List[DevelopmentalClaim]:
        return [c for c in self.claims if c.contradicted]

    def strength_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {s: 0 for s in EvidenceStrength.ALL}
        for c in self.claims:
            dist[c.strength] = dist.get(c.strength, 0) + 1
        return dist

    def snapshot(self) -> Dict[str, Any]:
        return {
            "claim_count": len(self.claims),
            "strength_distribution": self.strength_distribution(),
            "contradicted": [c.claim_type for c in self.contradicted_claims()],
            "claims": [c.to_dict() for c in self.claims],
        }

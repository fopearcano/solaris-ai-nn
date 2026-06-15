"""Evidence mapper -- every recommendation must cite its evidence.

The :class:`ArchitectureEvidenceMap` links modules to evidence (research reports,
ablations, null models, pilot/post-pilot reports, safety invariants, ops
incidents, ...) with a graded strength. Contradictory evidence is retained;
missing artifacts weaken (never strengthen) confidence; and nothing is
fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EvidenceStrength:
    UNSUPPORTED = "unsupported"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"

    ALL = (UNSUPPORTED, WEAK, MODERATE, STRONG, CONTRADICTED, INCONCLUSIVE)
    _RANK = {UNSUPPORTED: 0, INCONCLUSIVE: 1, WEAK: 2, MODERATE: 3, STRONG: 4}


EVIDENCE_SOURCES = (
    "research_lab_report", "ablation_result", "baseline_comparison",
    "null_model_result", "post_pilot_analysis", "pilot1_report",
    "pilot2_report", "pilot3_report", "safety_invariant_report",
    "assurance_case", "ops_incident", "auto_regeneration_repair",
    "inner_map_snapshot", "perceptual_ontogenesis_report",
)


def ontogenesis_revision_proposals(ont_status: Dict[str, Any],
                                   ) -> List[Dict[str, Any]]:
    """Turn a perceptual-ontogenesis status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code, edits imports, or
    actuates anything. They suggest sensorium/receptor/metabolism/proto-language/
    world-model schema revisions, contamination mitigation, or concept-explosion
    controls based on the observed ontogenesis.
    """
    proposals: List[Dict[str, Any]] = []
    contamination = float(ont_status.get(
        "human_label_contamination_score", 0.0) or 0.0)
    if contamination >= 0.5:
        proposals.append({
            "target": "sensorium_profile",
            "proposal": "reduce human-label dominance in the source diet",
            "reason": f"human-label contamination {contamination}",
            "advisory_only": True})
        proposals.append({
            "target": "contamination_mitigation",
            "proposal": "mark/down-weight label-grounded concepts",
            "reason": "feature-grounded concepts under-represented",
            "advisory_only": True})
    if int(ont_status.get("concept_explosion_warning_count", 0) or 0) > 0:
        proposals.append({
            "target": "concept_explosion_controls",
            "proposal": "tighten max_concepts_per_tick / birth thresholds",
            "reason": "concept-explosion warnings observed",
            "advisory_only": True})
    if float(ont_status.get("modality_native_concept_ratio", 0.0) or 0.0) < 0.3:
        proposals.append({
            "target": "receptor_profile",
            "proposal": "strengthen non-human modality receptors",
            "reason": "few modality-native concepts formed",
            "advisory_only": True})
    if float(ont_status.get("world_formation_density", 0.0) or 0.0) < 0.2:
        proposals.append({
            "target": "world_model_schema",
            "proposal": "review concept-relation growth thresholds",
            "reason": "sparse world formation",
            "advisory_only": True})
    return proposals


@dataclass
class EvidenceLink:
    """One piece of evidence for/against a module recommendation."""

    module_name: str
    source: str
    strength: str = EvidenceStrength.INCONCLUSIVE
    supports: bool = True
    ref: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ArchitectureEvidenceMap:
    """Maps modules to graded evidence; retains contradictions; never fabricates."""

    links: List[EvidenceLink] = field(default_factory=list)
    missing_artifacts: List[str] = field(default_factory=list)

    def add(self, module_name: str, source: str, strength: str,
            *, supports: bool = True, ref: str = "",
            summary: str = "") -> EvidenceLink:
        if strength not in EvidenceStrength.ALL:
            strength = EvidenceStrength.INCONCLUSIVE
        link = EvidenceLink(module_name=module_name, source=source,
                            strength=strength, supports=supports,
                            ref=ref or f"{source}:{module_name}",
                            summary=summary)
        self.links.append(link)
        return link

    def note_missing(self, artifact: str) -> None:
        self.missing_artifacts.append(artifact)

    def for_module(self, module_name: str) -> List[EvidenceLink]:
        return [l for l in self.links if l.module_name == module_name]

    def contradictions(self, module_name: str) -> List[EvidenceLink]:
        return [l for l in self.for_module(module_name)
                if l.strength == EvidenceStrength.CONTRADICTED
                or not l.supports]

    def confidence_for(self, module_name: str) -> str:
        """The graded confidence for a module's recommendation."""
        links = self.for_module(module_name)
        if not links:
            return EvidenceStrength.INCONCLUSIVE
        if any(l.strength == EvidenceStrength.CONTRADICTED for l in links):
            return EvidenceStrength.CONTRADICTED
        best = max(EvidenceStrength._RANK.get(l.strength, 0)
                   for l in links if l.supports) if any(
                       l.supports for l in links) else 0
        # Missing artifacts weaken confidence by one rank (floor at weak).
        if self.missing_artifacts and best > 2:
            best -= 1
        inv = {v: k for k, v in EvidenceStrength._RANK.items()}
        return inv.get(best, EvidenceStrength.INCONCLUSIVE)

    def refs_for(self, module_name: str) -> List[str]:
        return [l.ref for l in self.for_module(module_name)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_count": len(self.links),
            "missing_artifacts": list(self.missing_artifacts),
            "modules": sorted({l.module_name for l in self.links}),
            "links": [l.to_dict() for l in self.links],
            "sources": list(EVIDENCE_SOURCES),
        }

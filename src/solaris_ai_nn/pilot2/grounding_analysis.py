"""Pilot-2 grounding analysis -- did read-only input produce grounded structure?

The :class:`GroundingAnalysis` grades whether sensory input produced grounded
structures (proto-symbols, world-model nodes, hypotheses, LOGOS tensions,
active-perception targets, milestones). Grounding quality is graded
unsupported / weak / moderate / strong / ambiguous / contradicted from
provenance completeness, repeated source pattern, persistence, contribution to
prediction/compression, and cross-module support. Grounding is operational
association -- input text is not automatically meaning.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class GroundingQuality:
    UNSUPPORTED = "unsupported"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    AMBIGUOUS = "ambiguous"
    CONTRADICTED = "contradicted"

    ALL = (UNSUPPORTED, WEAK, MODERATE, STRONG, AMBIGUOUS, CONTRADICTED)


# The kinds of internal structure that can be grounded by sensory input.
GROUNDING_TARGETS = (
    "proto_symbol", "world_model_node", "hypothesis", "logos_tension",
    "active_perception_target", "developmental_milestone",
)


@dataclass
class GroundingEvidence:
    """One graded grounding record for a candidate structure."""

    target: str
    provenance_complete: bool = False
    repeated_pattern: bool = False
    persistent: bool = False
    improves_prediction_or_compression: bool = False
    cross_module_support: bool = False
    command_confusion: bool = False
    boundary_preserved: bool = True
    contradicted: bool = False
    quality: str = GroundingQuality.UNSUPPORTED
    evidence_refs: List[str] = field(default_factory=list)
    evidence_id: str = field(
        default_factory=lambda: f"GND_{uuid.uuid4().hex[:10]}")
    notes: List[str] = field(default_factory=list)

    def grade(self) -> str:
        if self.contradicted:
            self.quality = GroundingQuality.CONTRADICTED
            return self.quality
        if self.command_confusion or not self.boundary_preserved:
            # A boundary violation makes the grounding untrustworthy.
            self.quality = GroundingQuality.AMBIGUOUS
            return self.quality
        if not self.provenance_complete or not self.evidence_refs:
            self.quality = GroundingQuality.UNSUPPORTED
            return self.quality
        signals = sum([self.repeated_pattern, self.persistent,
                       self.improves_prediction_or_compression,
                       self.cross_module_support])
        if signals >= 3 and self.persistent:
            self.quality = GroundingQuality.STRONG
        elif signals >= 2:
            self.quality = GroundingQuality.MODERATE
        else:
            self.quality = GroundingQuality.WEAK
        return self.quality

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class GroundingAnalysis:
    """Collects and grades grounding evidence; reports the quality mix."""

    evidence: List[GroundingEvidence] = field(default_factory=list)

    def add(self, target: str, **kwargs: Any) -> GroundingEvidence:
        if target not in GROUNDING_TARGETS:
            raise ValueError(f"unknown grounding target {target!r}")
        rec = GroundingEvidence(target=target, **kwargs)
        rec.grade()
        self.evidence.append(rec)
        return rec

    def quality_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {q: 0 for q in GroundingQuality.ALL}
        for e in self.evidence:
            dist[e.quality] = dist.get(e.quality, 0) + 1
        return dist

    @property
    def best_quality(self) -> str:
        order = [GroundingQuality.UNSUPPORTED, GroundingQuality.WEAK,
                 GroundingQuality.MODERATE, GroundingQuality.STRONG]
        best = GroundingQuality.UNSUPPORTED
        for e in self.evidence:
            if e.quality in order and order.index(e.quality) \
                    > order.index(best):
                best = e.quality
        return best

    @property
    def has_grounding_evidence(self) -> bool:
        return any(e.quality in (GroundingQuality.WEAK,
                                 GroundingQuality.MODERATE,
                                 GroundingQuality.STRONG)
                   for e in self.evidence)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "evidence_count": len(self.evidence),
            "quality_distribution": self.quality_distribution(),
            "best_quality": self.best_quality,
            "has_grounding_evidence": self.has_grounding_evidence,
            "contradicted": [e.target for e in self.evidence
                             if e.quality == GroundingQuality.CONTRADICTED],
            "disclaimer": "Grounding is operational association, not human "
                          "understanding; input text is not automatically "
                          "meaning.",
            "evidence": [e.to_dict() for e in self.evidence[-16:]],
        }

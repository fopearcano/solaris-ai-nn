"""Private syntax -- internal sign-relation structure, not human grammar.

A :class:`PrivateSyntaxPattern` captures a recurring relation between internal
signs (sequence, co-occurrence, absence timing, prediction, contradiction). This
is NOT grammar in a human language: there is no subject/verb/object, no
natural-language syntax is forced, and the structure is purely an internal account
of how signs relate.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .signs import InternalSign, SignKind


class SyntaxRelation:
    SEQUENCE = "sequence"
    CO_OCCURRENCE = "co_occurrence"
    BEFORE_ABSENCE = "before_absence"
    AFTER_ABSENCE = "after_absence"
    PREDICTS = "predicts"
    INHIBITS = "inhibits"
    AMPLIFIES = "amplifies"
    CONTRADICTS = "contradicts"
    UNIFIES = "unifies"
    SPLITS = "splits"
    REPLACES = "replaces"
    UNCERTAIN = "uncertain_relation"

    ALL = (SEQUENCE, CO_OCCURRENCE, BEFORE_ABSENCE, AFTER_ABSENCE, PREDICTS,
           INHIBITS, AMPLIFIES, CONTRADICTS, UNIFIES, SPLITS, REPLACES,
           UNCERTAIN)


@dataclass
class PrivateSyntaxPattern:
    """One recurring internal sign-relation pattern (not a human sentence)."""

    relation: str
    signs: List[str] = field(default_factory=list)
    pattern_id: str = field(
        default_factory=lambda: f"SYN_{uuid.uuid4().hex[:8]}")
    support: int = 1
    strength: float = 0.0
    uncertainty: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "relation": self.relation,
            "signs": list(self.signs),
            "support": self.support,
            "strength": round(self.strength, 4),
            "uncertainty": round(self.uncertainty, 4),
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
            "note": "internal sign-relation structure, not human grammar "
                    "(no subject/verb/object is implied)",
        }


@dataclass
class SyntaxPatternBuilder:
    """Builds private syntax patterns from sign families and relations."""

    patterns: Dict[str, PrivateSyntaxPattern] = field(default_factory=dict)

    def build(self, signs: List[InternalSign], *,
              concept_relations: List[Dict[str, Any]] = None,
              ) -> List[PrivateSyntaxPattern]:
        """Derive patterns from sign co-occurrence, absence, and relations."""
        self.patterns = {}
        by_concept: Dict[str, str] = {}
        for s in signs:
            for ref in s.proto_concept_refs:
                by_concept[ref] = s.sign_id

        # 1. Concept relations -> sign-to-sign relations (predicts / sequence).
        for rel in (concept_relations or []):
            a = by_concept.get(rel.get("source_concept", ""))
            b = by_concept.get(rel.get("target_concept", ""))
            if a and b and a != b:
                rtype = self._map_relation(rel.get("relation_type", ""))
                self._add(rtype, [a, b], strength=float(rel.get("strength",
                                                                0.0)),
                          evidence=[rel.get("relation_type", "")])

        # 2. Absence signs precede/follow other signs in the same modality.
        absence = [s for s in signs if s.kind == SignKind.ABSENCE]
        others = [s for s in signs if s.kind != SignKind.ABSENCE]
        for a in absence:
            for o in others:
                if set(a.modality_distribution) & set(o.modality_distribution):
                    self._add(SyntaxRelation.AFTER_ABSENCE, [a.sign_id,
                                                             o.sign_id],
                              strength=0.4, evidence=["shared_modality"])
                    break

        # 3. Co-occurring signs that share a source.
        n = len(signs)
        for i in range(n):
            for j in range(i + 1, n):
                shared = (set(signs[i].source_distribution)
                          & set(signs[j].source_distribution))
                if shared:
                    self._add(SyntaxRelation.CO_OCCURRENCE,
                              [signs[i].sign_id, signs[j].sign_id],
                              strength=0.3,
                              evidence=[f"source:{s}" for s in sorted(shared)])
        return list(self.patterns.values())

    @staticmethod
    def _map_relation(concept_relation: str) -> str:
        mapping = {
            "predicts": SyntaxRelation.PREDICTS,
            "precedes": SyntaxRelation.SEQUENCE,
            "follows": SyntaxRelation.SEQUENCE,
            "co_occurs": SyntaxRelation.CO_OCCURRENCE,
            "inhibits": SyntaxRelation.INHIBITS,
            "amplifies": SyntaxRelation.AMPLIFIES,
            "replaces": SyntaxRelation.REPLACES,
            "appears_after_absence": SyntaxRelation.AFTER_ABSENCE,
            "disappears_after": SyntaxRelation.BEFORE_ABSENCE,
        }
        return mapping.get(concept_relation, SyntaxRelation.UNCERTAIN)

    def _add(self, relation: str, signs: List[str], *, strength: float,
             evidence: List[str]) -> None:
        key = f"{relation}:{'|'.join(signs)}"
        pat = self.patterns.get(key)
        if pat is None:
            pat = PrivateSyntaxPattern(
                relation=relation, signs=list(signs), support=1,
                strength=min(1.0, strength),
                uncertainty=round(1.0 - min(1.0, strength), 4),
                evidence_refs=list(evidence))
            self.patterns[key] = pat
        else:
            pat.support += 1
            pat.strength = min(1.0, pat.strength + 0.1)
            pat.uncertainty = round(max(0.0, pat.uncertainty - 0.1), 4)

    def density(self, sign_count: int) -> float:
        if sign_count < 2:
            return 0.0
        max_edges = sign_count * (sign_count - 1) / 2
        return round(min(1.0, len(self.patterns) / max_edges), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {"pattern_count": len(self.patterns),
                "patterns": [p.to_dict() for p in self.patterns.values()]}

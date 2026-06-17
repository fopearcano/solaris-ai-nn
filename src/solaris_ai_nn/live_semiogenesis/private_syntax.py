"""Live private syntax -- operational relation structure, not language grammar.

:class:`PrivateSyntaxGraph` records relations between private signs (co-occurrence,
contrast, precedence, rhythm/absence/source/modality linkage, etc.). This is
operational relation structure: it is **not** grammar, **not** semantics, and makes
no claim of language. Relations require evidence, weak relations are marked weak or
uncertain, and contaminated relations are blocked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class PrivateSyntaxRelationType:
    CO_OCCURS_WITH = "co_occurs_with"
    CONTRASTS_WITH = "contrasts_with"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    RHYTHMICALLY_LINKED = "rhythmically_linked"
    ABSENCE_LINKED = "absence_linked"
    SOURCE_LINKED = "source_linked"
    MODALITY_LINKED = "modality_linked"
    OVERLOAD_LINKED = "overload_linked"
    DEPRIVATION_LINKED = "deprivation_linked"
    UNCERTAIN_RELATION = "uncertain_relation"
    BLOCKED_RELATION = "blocked_relation"

    ALL = (CO_OCCURS_WITH, CONTRASTS_WITH, PRECEDES, FOLLOWS,
           RHYTHMICALLY_LINKED, ABSENCE_LINKED, SOURCE_LINKED, MODALITY_LINKED,
           OVERLOAD_LINKED, DEPRIVATION_LINKED, UNCERTAIN_RELATION,
           BLOCKED_RELATION)


@dataclass
class LivePrivateSyntaxRelation:
    """One operational relation between two private signs (with evidence)."""

    source_sign: str
    target_sign: str
    relation_type: str = PrivateSyntaxRelationType.UNCERTAIN_RELATION
    strength: str = "weak"  # strong / weak / uncertain
    evidence: List[str] = field(default_factory=list)
    blocked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_sign": self.source_sign, "target_sign": self.target_sign,
            "relation_type": self.relation_type, "strength": self.strength,
            "evidence": list(self.evidence), "blocked": self.blocked,
            "is_language_grammar": False, "is_semantics": False,
        }


@dataclass
class PrivateSyntaxGraph:
    """A small graph of operational relations between private signs."""

    relations: List[LivePrivateSyntaxRelation] = field(default_factory=list)

    def add(self, relation: LivePrivateSyntaxRelation) -> None:
        self.relations.append(relation)

    @property
    def relation_count(self) -> int:
        return len(self.relations)

    def to_dict(self) -> Dict[str, Any]:
        def count(rt):
            return sum(1 for r in self.relations if r.relation_type == rt)
        return {
            "live_private_syntax_relation_count": self.relation_count,
            "blocked_relation_count": sum(1 for r in self.relations
                                          if r.blocked),
            "co_occurs_count": count(PrivateSyntaxRelationType.CO_OCCURS_WITH),
            "contrasts_count": count(PrivateSyntaxRelationType.CONTRASTS_WITH),
            "absence_linked_count": count(
                PrivateSyntaxRelationType.ABSENCE_LINKED),
            "relations": [r.to_dict() for r in self.relations],
            "note": "private syntax is operational relation structure, not "
                    "language grammar or semantics; relations require evidence; "
                    "weak relations are marked weak/uncertain; contaminated "
                    "relations are blocked",
        }


@dataclass
class PrivateSyntaxBuilder:
    """Builds an operational private-syntax graph from sign candidates."""

    def build(self, candidates: List[Any]) -> PrivateSyntaxGraph:
        graph = PrivateSyntaxGraph()
        # Relate signs that share a source or modality, or that link absence.
        usable = [c for c in candidates
                  if not getattr(c, "contamination_findings", [])]
        for i, a in enumerate(usable):
            for b in usable[i + 1:]:
                rel = self._relate(a, b)
                if rel is not None:
                    graph.add(rel)
        # A contaminated candidate yields an explicit blocked relation (visible).
        for c in candidates:
            if getattr(c, "contamination_findings", []):
                graph.add(LivePrivateSyntaxRelation(
                    source_sign=c.private_token, target_sign="(none)",
                    relation_type=PrivateSyntaxRelationType.BLOCKED_RELATION,
                    strength="uncertain", blocked=True,
                    evidence=["contaminated candidate; relation blocked"]))
        return graph

    def _relate(self, a: Any, b: Any):
        shared_sources = set(a.source_distribution) & set(b.source_distribution)
        shared_modalities = (set(a.modality_distribution)
                             & set(b.modality_distribution))
        a_absence = any("absence" in s for s in a.feature_signature_refs)
        b_absence = any("absence" in s for s in b.feature_signature_refs)
        if a_absence and b_absence:
            return LivePrivateSyntaxRelation(
                source_sign=a.private_token, target_sign=b.private_token,
                relation_type=PrivateSyntaxRelationType.ABSENCE_LINKED,
                strength="weak", evidence=["both link absence signals"])
        if shared_sources:
            return LivePrivateSyntaxRelation(
                source_sign=a.private_token, target_sign=b.private_token,
                relation_type=PrivateSyntaxRelationType.SOURCE_LINKED,
                strength="weak",
                evidence=[f"shared source(s): {sorted(shared_sources)}"])
        if shared_modalities:
            return LivePrivateSyntaxRelation(
                source_sign=a.private_token, target_sign=b.private_token,
                relation_type=PrivateSyntaxRelationType.MODALITY_LINKED,
                strength="uncertain",
                evidence=[f"shared modality: {sorted(shared_modalities)}"])
        return None

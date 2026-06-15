"""Synthesis -- combine/split signs while preserving fragments and contradiction.

The :class:`SynthesisEngine` performs cognitive synthesis operations (merge, split,
resolve weak contradiction, preserve contradiction as a LOGOS tension, compress a
repeated relation, create a higher-order relation, mark unresolved unknown).
Synthesis is not proof of understanding, preserves original evidence, never deletes
the synthesized fragments, and keeps irreducible contradiction visible.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class SynthesisOp:
    MERGE_CROSS_MODAL = "merge_into_cross_modal_structure"
    SPLIT_AMBIGUOUS = "split_ambiguous_sign"
    RESOLVE_WEAK_CONTRADICTION = "resolve_weak_contradiction"
    PRESERVE_CONTRADICTION = "preserve_contradiction_as_logos_tension"
    COMPRESS_RELATION = "compress_repeated_relation"
    HIGHER_ORDER_RELATION = "create_higher_order_relation"
    MARK_UNKNOWN = "mark_unresolved_unknown"

    ALL = (MERGE_CROSS_MODAL, SPLIT_AMBIGUOUS, RESOLVE_WEAK_CONTRADICTION,
           PRESERVE_CONTRADICTION, COMPRESS_RELATION, HIGHER_ORDER_RELATION,
           MARK_UNKNOWN)


@dataclass
class SynthesisResult:
    """One synthesis event (fragments preserved; contradiction kept visible)."""

    op: str
    fragment_refs: List[str] = field(default_factory=list)
    synthesis_id: str = field(default_factory=lambda: f"SYN_{uuid.uuid4().hex[:8]}")
    result_ref: str = ""
    preserved_contradiction: bool = False
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "synthesis_id": self.synthesis_id,
            "op": self.op,
            "fragment_refs": list(self.fragment_refs),
            "result_ref": self.result_ref,
            "preserved_contradiction": self.preserved_contradiction,
            "evidence_refs": list(self.evidence_refs),
            "note": "synthesis is not proof of understanding; fragments are "
                    "preserved and irreducible contradiction stays visible",
        }


@dataclass
class CognitiveSynthesis:
    """A view over the synthesis events produced this tick."""

    results: List[SynthesisResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"synthesis_count": len(self.results),
                "preserved_contradictions": sum(
                    1 for r in self.results if r.preserved_contradiction),
                "results": [r.to_dict() for r in self.results]}


@dataclass
class SynthesisEngine:
    """Synthesizes signs while preserving fragments and visible contradiction."""

    def synthesize(self, signs: List[Any], inferences: List[Any],
                   ) -> CognitiveSynthesis:
        out = CognitiveSynthesis()
        # Cross-modal merge candidates: two stable signs of different modalities
        # linked by a cross-modal inference.
        cross_inf = [i for i in inferences
                     if getattr(i, "inference_type", "") == "cross_modal_unity"]
        for inf in cross_inf:
            refs = list(getattr(inf, "sign_refs", []))
            if len(refs) >= 2:
                out.results.append(SynthesisResult(
                    op=SynthesisOp.MERGE_CROSS_MODAL, fragment_refs=refs,
                    result_ref=f"xmod_struct_{refs[0]}",
                    evidence_refs=[getattr(inf, "inference_id", "")]))
        # Ambiguous signs -> split (fragments preserved).
        for s in signs:
            if getattr(s, "is_ambiguous", False):
                out.results.append(SynthesisResult(
                    op=SynthesisOp.SPLIT_AMBIGUOUS,
                    fragment_refs=[getattr(s, "sign_id", "")],
                    result_ref="", evidence_refs=["ambiguity"]))
        # Contradiction inferences -> preserve as LOGOS tension (kept visible).
        for inf in inferences:
            if getattr(inf, "inference_type", "") == "contradiction":
                out.results.append(SynthesisResult(
                    op=SynthesisOp.PRESERVE_CONTRADICTION,
                    fragment_refs=list(getattr(inf, "sign_refs", [])),
                    preserved_contradiction=True,
                    evidence_refs=[getattr(inf, "inference_id", "")]))
        return out

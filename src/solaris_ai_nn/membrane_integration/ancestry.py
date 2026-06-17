"""Membrane ancestry tracking -- cognition -> sign -> concept -> impression -> event.

:class:`MembraneAncestryChain` records the lineage of a downstream artifact back
through private sign, proto-concept, sensory impression, receptor, and source event
to the source/feeder id. Partial chains are supported. Missing ancestry must be
visible, and contaminated ancestry must downgrade or block promotion gates.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MembraneAncestryRef:
    """One link in an ancestry chain."""

    ref_type: str  # cognition_trace / private_sign / proto_concept / impression / receptor / source_event / source
    ref_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {"ref_type": self.ref_type, "ref_id": self.ref_id}


@dataclass
class MembraneAncestryChain:
    """The ancestry chain for one downstream artifact."""

    artifact_id: str
    artifact_type: str  # proto_concept / private_sign / cognition_trace
    impression_ids: List[str] = field(default_factory=list)
    receptor_ids: List[str] = field(default_factory=list)
    source_event_ids: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    contamination_score: float = 0.0
    source_pressure_status: str = "unknown"
    permeability_decisions: List[str] = field(default_factory=list)
    blocked_ancestry: bool = False
    fallback_raw_event: bool = False
    limitations: List[str] = field(default_factory=list)

    @property
    def has_impression_ancestry(self) -> bool:
        return bool(self.impression_ids)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "impression_ids": self.impression_ids[:50],
            "receptor_ids": list(dict.fromkeys(self.receptor_ids))[:50],
            "source_event_ids": self.source_event_ids[:50],
            "source_ids": list(dict.fromkeys(self.source_ids))[:50],
            "contamination_score": round(self.contamination_score, 3),
            "source_pressure_status": self.source_pressure_status,
            "permeability_decisions": list(dict.fromkeys(
                self.permeability_decisions))[:50],
            "has_impression_ancestry": self.has_impression_ancestry,
            "blocked_ancestry": self.blocked_ancestry,
            "fallback_raw_event": self.fallback_raw_event,
            "limitations": list(self.limitations),
        }


@dataclass
class AncestryValidationResult:
    """The aggregate ancestry-validation result over downstream artifacts."""

    chains: List[MembraneAncestryChain] = field(default_factory=list)
    membrane_available: bool = False

    @property
    def with_impression_ancestry(self) -> int:
        return sum(1 for c in self.chains if c.has_impression_ancestry)

    @property
    def missing_ancestry(self) -> int:
        return sum(1 for c in self.chains if not c.has_impression_ancestry)

    @property
    def contaminated_ancestry(self) -> int:
        return sum(1 for c in self.chains if c.contamination_score >= 0.5)

    def to_dict(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for c in self.chains:
            by_type[c.artifact_type] = by_type.get(c.artifact_type, 0) + 1
        return {
            "membrane_available": self.membrane_available,
            "ancestry_chain_count": len(self.chains),
            "with_impression_ancestry": self.with_impression_ancestry,
            "missing_ancestry": self.missing_ancestry,
            "contaminated_ancestry": self.contaminated_ancestry,
            "by_artifact_type": by_type,
            "chains": [c.to_dict() for c in self.chains],
            "note": "every born proto-concept/sign and promoted cognition trace "
                    "should have impression ancestry when the membrane is "
                    "available; missing ancestry is visible; contaminated "
                    "ancestry downgrades or blocks promotion gates",
        }

    def write(self, state_dir: str) -> Dict[str, str]:
        base = os.path.join(state_dir, "membrane", "integration")
        os.makedirs(base, exist_ok=True)
        json_path = os.path.join(base, "MEMBRANE_ANCESTRY_INDEX.json")
        md_path = os.path.join(base, "MEMBRANE_ANCESTRY_INDEX.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_md())
        return {"json": json_path, "md": md_path}

    def _render_md(self) -> str:
        d = self.to_dict()
        lines = ["# Membrane Ancestry Index", "",
                 f"- membrane available: {d['membrane_available']}",
                 f"- ancestry chains: {d['ancestry_chain_count']}",
                 f"- with impression ancestry: {d['with_impression_ancestry']}",
                 f"- missing ancestry: {d['missing_ancestry']}",
                 f"- contaminated ancestry: {d['contaminated_ancestry']}", "",
                 "| artifact | type | impressions | contamination | blocked |",
                 "| --- | --- | --- | --- | --- |"]
        for c in self.chains[:200]:
            lines.append(f"| {c.artifact_id} | {c.artifact_type} | "
                         f"{len(c.impression_ids)} | "
                         f"{c.contamination_score:.2f} | {c.blocked_ancestry} |")
        lines += ["", "_Ancestry runs cognition_trace -> private_sign -> "
                  "proto_concept -> sensory_impression -> receptor -> "
                  "source_event -> source. Missing ancestry is visible; "
                  "contaminated ancestry downgrades or blocks promotion._"]
        return "\n".join(lines) + "\n"


@dataclass
class MembraneAncestryBuilder:
    """Builds ancestry chains from downstream memory + loaded impressions."""

    def build(self, *, impressions: List[Any],
              concept_records: Optional[List[Dict[str, Any]]] = None,
              sign_records: Optional[List[Dict[str, Any]]] = None,
              cognition_records: Optional[List[Dict[str, Any]]] = None,
              membrane_available: bool = False,
              source_pressure_status: str = "unknown",
              ) -> AncestryValidationResult:
        result = AncestryValidationResult(membrane_available=membrane_available)
        # Index impressions by source-event id (the link concept supporting_refs
        # carry) and by impression id.
        by_event: Dict[str, List[Any]] = {}
        for imp in impressions:
            by_event.setdefault(imp.source_event_id, []).append(imp)

        concept_chain: Dict[str, MembraneAncestryChain] = {}
        for rec in concept_records or []:
            chain = self._concept_chain(rec, by_event, source_pressure_status)
            result.chains.append(chain)
            concept_chain[rec.get("concept_id", "")] = chain

        for rec in sign_records or []:
            chain = self._sign_chain(rec, concept_chain, source_pressure_status)
            result.chains.append(chain)
            # index by sign id for cognition linkage
            concept_chain[rec.get("sign_id", "")] = chain

        for rec in cognition_records or []:
            result.chains.append(
                self._cognition_chain(rec, concept_chain,
                                      source_pressure_status))
        return result

    def _concept_chain(self, rec, by_event, sp_status) -> MembraneAncestryChain:
        c = MembraneAncestryChain(
            artifact_id=rec.get("concept_id", ""),
            artifact_type="proto_concept",
            source_pressure_status=sp_status)
        refs = rec.get("supporting_event_ids", []) or rec.get(
            "supporting_refs", []) or []
        for ref in refs:
            c.source_event_ids.append(ref)
            for imp in by_event.get(ref, []):
                c.impression_ids.append(imp.impression_id)
                c.receptor_ids.append(imp.receptor_id)
                c.source_ids.append(imp.source_id)
                c.permeability_decisions.append(imp.permeability_status)
                c.contamination_score = max(c.contamination_score,
                                            imp.contamination)
                if imp.blocked:
                    c.blocked_ancestry = True
        if not c.impression_ids:
            c.fallback_raw_event = True
            c.limitations.append("no impression ancestry; raw-event fallback")
        return c

    def _sign_chain(self, rec, concept_chain, sp_status) -> MembraneAncestryChain:
        c = MembraneAncestryChain(
            artifact_id=rec.get("sign_id", ""), artifact_type="private_sign",
            source_pressure_status=sp_status)
        for cid in rec.get("linked_concept_ids", []) or []:
            parent = concept_chain.get(cid)
            if parent is not None:
                c.impression_ids.extend(parent.impression_ids)
                c.receptor_ids.extend(parent.receptor_ids)
                c.source_event_ids.extend(parent.source_event_ids)
                c.source_ids.extend(parent.source_ids)
                c.permeability_decisions.extend(parent.permeability_decisions)
                c.contamination_score = max(c.contamination_score,
                                            parent.contamination_score)
                c.blocked_ancestry = c.blocked_ancestry or parent.blocked_ancestry
        if not c.impression_ids:
            c.fallback_raw_event = True
            c.limitations.append("no concept->impression ancestry")
        return c

    def _cognition_chain(self, rec, chain_index, sp_status,
                         ) -> MembraneAncestryChain:
        c = MembraneAncestryChain(
            artifact_id=rec.get("trace_id", ""),
            artifact_type="cognition_trace", source_pressure_status=sp_status)
        for sid in rec.get("linked_sign_ids", []) or []:
            parent = chain_index.get(sid)
            if parent is not None:
                c.impression_ids.extend(parent.impression_ids)
                c.receptor_ids.extend(parent.receptor_ids)
                c.source_event_ids.extend(parent.source_event_ids)
                c.source_ids.extend(parent.source_ids)
                c.contamination_score = max(c.contamination_score,
                                            parent.contamination_score)
                c.blocked_ancestry = c.blocked_ancestry or parent.blocked_ancestry
        if not c.impression_ids:
            c.fallback_raw_event = True
            c.limitations.append("no sign->concept->impression ancestry")
        return c

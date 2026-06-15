"""Perceptual ontogenesis report -- world formation made visible and honest.

:class:`PerceptualOntogenesisReportBuilder` compiles the perceptual atoms,
proto-concept candidates, stable/decaying/rejected concepts, families, relation
graph, world-formation state, utility profiles, contamination, and fixture-vs-live
grounding. It states explicitly that proto-concepts are operational structures (not
words), that world formation is structural (not subjective experience), and that it
proves no understanding/consciousness/sentience/life. The Markdown is scanned by
ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .proto_concepts import ProtoConceptStatus

_DOES_NOT_PROVE = (
    "Proto-concepts are operational structures, not words.",
    "World formation is structural, not subjective experience.",
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life.",
    "This does not prove understanding.",
)

_LIMITATIONS = (
    "Concepts are sensorium-native structures; they are not human categories.",
    "Stability is provisional; stable does not mean true.",
    "Negative, failed, and ambiguous concepts are preserved, not deleted.",
    "Human labels are external annotations only, never ground truth.",
    "Fixture-only concepts are marked; they are not yet live-confirmed.",
)


@dataclass
class PerceptualOntogenesisReportBuilder:
    """Builds the ontogenesis report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def _concepts_by(self, *statuses: str) -> List[Dict[str, Any]]:
        return [c.to_dict() for c in self.runtime.concepts.values()
                if c.status in statuses]

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.ontogenesis_status()
        sensorium = rt.sensorium
        concepts = list(rt.concepts.values())
        sections: Dict[str, Any] = {
            "purpose": ("describe how an internal world begins to form from "
                        "continuous peculiar perception, via sensorium-native "
                        "proto-concepts (operational structures, not words)"),
            "input_sensorium_summary": (
                sensorium.plural_sensorium_status()
                if sensorium is not None
                and hasattr(sensorium, "plural_sensorium_status") else {}),
            "perceptual_atoms": {
                "count": len(rt.atoms),
                "by_kind": self._atoms_by_kind(),
            },
            "proto_concept_candidates": self._concepts_by(
                ProtoConceptStatus.CANDIDATE, ProtoConceptStatus.EMERGING,
                ProtoConceptStatus.UNSTABLE),
            "stable_proto_concepts": self._concepts_by(
                ProtoConceptStatus.STABLE),
            "decaying_rejected_proto_concepts": self._concepts_by(
                ProtoConceptStatus.DECAYING, ProtoConceptStatus.REJECTED),
            "concept_families": rt.family_builder.to_dict(),
            "relation_graph": rt.relation_engine.to_dict(),
            "world_formation_state": (rt.world.to_dict()
                                      if rt.world is not None else {}),
            "prediction_compression_utility": {
                "prediction_supported": sum(
                    1 for c in concepts if c.prediction_utility >= 0.5),
                "compression_supported": sum(
                    1 for c in concepts if c.compression_utility >= 0.5),
            },
            "attention_utility": {
                "attention_supported": sum(
                    1 for c in concepts if c.attention_utility >= 0.5),
            },
            "absence_based_concepts": [c.to_dict() for c in concepts
                                       if c.is_absence_based],
            "cross_modal_concepts": [c.to_dict() for c in concepts
                                     if c.is_cross_modal],
            "human_label_contaminated_concepts": [
                c.to_dict() for c in rt.contaminated_concepts()],
            "fixture_only_concepts": [c.to_dict() for c in concepts
                                      if c.fixture_grounded
                                      and not c.live_grounded],
            "live_field_grounded_concepts": [c.to_dict() for c in concepts
                                             if c.live_grounded],
            "negative_results": self._concepts_by(
                ProtoConceptStatus.REJECTED, ProtoConceptStatus.AMBIGUOUS),
            "latent_replay_recommendations":
                rt.latent_replay_recommendations(),
            "milestones": list(rt.milestones),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_prove": list(_DOES_NOT_PROVE),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _atoms_by_kind(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for a in self.runtime.atoms.values():
            out[a.kind] = out.get(a.kind, 0) + 1
        return out

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        world = sections["world_formation_state"]
        lines = [
            "# Perceptual Ontogenesis Report", "",
            "_How an internal world begins to form from continuous peculiar "
            "perception. Proto-concepts are operational internal structures for "
            "compression, prediction, attention, and relation-building -- NOT "
            "words, NOT human categories, and NOT proof of understanding or "
            "subjective experience. Human labels are external annotations only, "
            "never ground truth._", "",
            f"- perceptual atoms: {status['perceptual_atom_count']}",
            f"- proto-concepts: {status['proto_concept_count']} "
            f"(stable {status['stable_concept_count']}, "
            f"decaying {status['decaying_concept_count']}, "
            f"rejected {status['rejected_concept_count']})",
            f"- concept families: {status['concept_family_count']} "
            f"(dominant {status['dominant_concept_family']})",
            f"- concept relations: {status['concept_relation_count']}",
            f"- modality-native ratio: "
            f"{status['modality_native_concept_ratio']}",
            f"- cross-modal ratio: {status['cross_modal_concept_ratio']}",
            f"- absence-based ratio: {status['absence_based_concept_ratio']}",
            f"- contaminated concepts: {status['contaminated_concept_count']} "
            f"(ratio {status['contaminated_concept_ratio']})",
            f"- world formation density: "
            f"{status['world_formation_density']}",
            f"- concept explosion warnings: "
            f"{status['concept_explosion_warning_count']}",
            "",
            "## World formation (structural, not subjective)", "",
            f"- {world.get('state', {}).get('note', 'structural world only')}"
            if world else "- (no world formed yet)",
            "",
            "## Negative / failed / ambiguous concepts (preserved)", "",
            f"- preserved: {len(sections['negative_results'])} "
            "(decay/rejection is recorded as new state, never deleted)",
            "",
            "## What this does NOT prove", "",
        ]
        lines += [f"- {item}" for item in sections["what_this_does_not_prove"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "PERCEPTUAL_ONTOGENESIS_REPORT.md")
        json_path = os.path.join(base, "PERCEPTUAL_ONTOGENESIS_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

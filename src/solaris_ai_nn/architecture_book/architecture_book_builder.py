"""Architecture book builder -- the long, structured architecture book.

:class:`ArchitectureBookBuilder` expands the outline into a structured book. Each
chapter carries purpose, role, inputs, outputs, artifacts, safety constraints,
integration points, failure modes, limitations, implementation status, and future
work. Planned/missing modules are marked honestly; "organismic" stays a metaphor;
no forbidden claim is asserted.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .chapter_model import (
    ArchitectureChapter,
    ChapterEvidenceRef,
    ChapterStatus,
)
from .diagram_builder import DiagramBuilder, DiagramKind
from .outline_builder import SolarisArchitectureOutlineBuilder

_PACKAGE_ROOT = "solaris_ai_nn"

# module key -> (purpose, role, inputs, outputs, artifacts, safety, integration,
#                failure modes, limitations, future)
_MODULE_NOTES: Dict[str, Dict[str, str]] = {
    "plural_sensorium": {
        "purpose": "Convert heterogeneous read-only inputs into bounded internal "
                   "signals across multiple sensory channels.",
        "role": "The intake surface of the organismic substrate.",
        "inputs": "Synthetic or read-only field signals via the sensory membrane.",
        "outputs": "Bounded per-channel internal signal vectors.",
        "safety": "Read-only; sensory text is never an operator command; no "
                  "feeder is started or controlled.",
    },
    "perceptual_metabolism": {
        "purpose": "Regulate representational load (intake, consolidation, decay) "
                   "homeostatically.",
        "role": "Keeps the substrate bounded over long runtimes.",
        "safety": "A control mechanism, not digestion or life.",
    },
    "semiogenesis": {
        "purpose": "Form internal private signs that index recurring regularities.",
        "role": "Provides internal labels usable downstream.",
        "safety": "Not language and not meaning; a sign is useful only if it has "
                  "downstream effect.",
    },
    "scientific_claims": {
        "purpose": "Map evidence to claims, grade strength, preserve "
                   "counterevidence, and block forbidden claims.",
        "role": "The claim-discipline source of truth.",
        "outputs": "Claim registry, theory ledger, counterevidence, limitations, "
                   "publication dossier (draft).",
        "safety": "Blocks unsupported consciousness/life/agency claims; ClaimGuard "
                  "scans generated text.",
    },
    "alpha_system": {
        "purpose": "Assemble all modules into one bounded, fixture-only "
                   "end-to-end local run behind a unified CLI.",
        "role": "The operator entry point.",
        "outputs": "Alpha report, artifact index, operator runbook, cycle status.",
        "safety": "Local-only, bounded, fixture-only; no Git/GitHub/publish/"
                  "feeders/hardware.",
    },
}


@dataclass
class ArchitectureBookBuilder:
    """Builds the architecture book chapters from the outline + module notes."""

    def build_chapters(self) -> List[ArchitectureChapter]:
        outline = SolarisArchitectureOutlineBuilder().build()
        chapters: List[ArchitectureChapter] = []
        for oc in outline:
            chapters.append(self._chapter(oc))
        return chapters

    def _chapter(self, oc) -> ArchitectureChapter:
        implemented = oc.implemented
        notes = _MODULE_NOTES.get(oc.module_key, {})
        ch = ArchitectureChapter(
            number=str(oc.number), title=oc.title, part=oc.part,
            implementation_status=("implemented" if implemented
                                   else "planned_or_missing"),
            status=(ChapterStatus.COMPLETE if implemented
                    else ChapterStatus.MISSING_SOURCES))
        if oc.module_key:
            ch.evidence_refs.append(ChapterEvidenceRef(
                kind="package", ref=f"{_PACKAGE_ROOT}.{oc.module_key}",
                present=implemented))
        else:
            ch.reconstructed_from_spec = True
        ch.add_section("Purpose", notes.get(
            "purpose", f"{oc.title}: see the module map and prompt specification "
            "for the implementing package and its role."))
        ch.add_section("Role in architecture", notes.get(
            "role", "Part of the bounded, layered Solaris-AI-NN stack."))
        ch.add_section("Inputs", notes.get(
            "inputs", "Local artifacts/state from upstream modules (read-only)."))
        ch.add_section("Outputs", notes.get(
            "outputs", "Local artifacts/reports consumed by downstream modules."))
        ch.add_section("Artifacts", notes.get(
            "artifacts", "Local JSON/Markdown artifacts under the module's state "
            "directory; missing artifacts are reported, not faked."))
        ch.add_section("Safety constraints", notes.get(
            "safety", "Local-only and bounded; no actuation, hardware/feeder "
            "control, network, Git/GitHub, or publishing; no forbidden "
            "inner-state claim."))
        ch.add_section("Integration points",
                       "Feeds and is fed by adjacent modules in the system map; "
                       "exposed to Inner MAP and Evaluation where available.")
        ch.add_section("Failure modes",
                       "If the module is absent it is marked missing and skipped; "
                       "if evidence is missing the dependent claims are downgraded "
                       "rather than asserted.")
        ch.implementation_status = ("implemented" if implemented
                                    else "planned_or_missing")
        if not implemented and oc.module_key:
            ch.limitations.append(
                f"module {oc.module_key!r} is not present locally; this chapter "
                "is reconstructed from the prompt specification")
            ch.reconstructed_from_spec = True
        ch.add_section("Future work",
                       "Strengthen evidence, controls, and replication; close any "
                       "documented gaps via the experiment compiler.")
        return ch

    def build(self) -> str:
        chapters = self.build_chapters()
        diagrams = DiagramBuilder()
        lines = ["# Solaris-AI-NN: Architecture Book", "",
                 "_A structured, module-by-module reconstruction of the "
                 "Solaris-AI-NN architecture. 'Organismic', 'life', 'desire', and "
                 "'cognition' are architectural metaphors; the system makes no "
                 "claim of consciousness, sentience, biological life, personhood, "
                 "agency, free will, emotion, feeling, understanding, "
                 "self-awareness, or subjective experience. Planned or missing "
                 "modules are marked honestly._", ""]
        lines.append(SolarisArchitectureOutlineBuilder().render_md())
        lines.append("")
        # Key diagrams up front.
        lines.append(diagrams.build(DiagramKind.SYSTEM_MAP).render_md())
        lines.append(diagrams.build(DiagramKind.CORE_LOOP).render_md())
        lines.append(diagrams.build(DiagramKind.RESEARCH_CYCLE).render_md())
        current_part = None
        for ch in chapters:
            if ch.part != current_part:
                current_part = ch.part
                lines.append(f"## {current_part}")
                lines.append("")
            lines.append(ch.render_md(level=3))
        lines.append("---")
        lines.append("_Local Markdown documentation. No publication or upload "
                     "occurred, no Git/GitHub operation occurred, no experiments "
                     "were executed, and no consciousness/life/agency claim is "
                     "made._")
        return "\n".join(lines) + "\n"

    def summary(self) -> Dict[str, Any]:
        chapters = self.build_chapters()
        return {
            "generated_chapter_count": len(chapters),
            "complete_chapter_count": sum(
                1 for c in chapters if c.status == ChapterStatus.COMPLETE),
            "skipped_chapter_count": sum(
                1 for c in chapters
                if c.status == ChapterStatus.MISSING_SOURCES),
            "chapters": [c.to_dict() for c in chapters],
            "note": "planned/missing modules are marked honestly; no chapter "
                    "asserts a forbidden claim",
        }

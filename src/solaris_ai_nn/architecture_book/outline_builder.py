"""Outline builder -- the architecture book's Part I-VII chapter outline.

:class:`SolarisArchitectureOutlineBuilder` builds the full architecture-book
outline (Parts I-VII, chapters 1-41). The outline distinguishes implemented modules
from planned/stub ones by checking import-spec availability, uses "organismic" only
as architecture/metaphor language, and never claims biological life.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# (part title, [(chapter number, chapter title, optional module key)])
_OUTLINE: Tuple[Tuple[str, Tuple[Tuple[int, str, str], ...]], ...] = (
    ("Part I -- Project Frame", (
        (1, "What Solaris-AI-NN Is", ""),
        (2, "What Solaris-AI-NN Is Not", ""),
        (3, "Research Motivation", ""),
        (4, "From Solaris_Ai to Solaris-AI-NN", ""),
        (5, "Alpha Research System Overview", "alpha_system"))),
    ("Part II -- Organismic Substrate", (
        (6, "Plural Sensorium", "plural_sensorium"),
        (7, "Read-Only Field and Feeder SDK", "feeder_sdk"),
        (8, "Perceptual Metabolism", "perceptual_metabolism"),
        (9, "Sensorium-Native Ontogenesis", "perceptual_ontogenesis"),
        (10, "Semiogenesis and Private Signs", "semiogenesis"),
        (11, "Sensorium-Native Cognition", "sensorium_cognition"),
        (12, "Self-Boundary and Continuity", "self_boundary"),
        (13, "Valence, Desire, and Internal Pressure", "desire_formation"),
        (14, "Action-Reaction and Consequence Learning", "action_reaction"),
        (15, "Long-Horizon Development", "developmental_life"))),
    ("Part III -- Scientific Testing", (
        (16, "Developmental Soak Protocol", "developmental_soak"),
        (17, "Evidence Dossiers and Post-Run Autopsy", "developmental_soak"),
        (18, "Cross-Run Replication", "developmental_replication"),
        (19, "Falsification Lab", "developmental_replication"),
        (20, "Controls and Ablations", "developmental_replication"))),
    ("Part IV -- Architecture Governance", (
        (21, "Architecture Evolution Lab", "architecture_evolution"),
        (22, "Experiment Compiler", "experiment_compiler"),
        (23, "Implementation Intake and PR Diff Audit", "implementation_intake"),
        (24, "Post-Merge Assimilation", "post_merge_assimilation"),
        (25, "Versioned Research Baseline", "research_baseline"),
        (26, "Closed Research Cycle", "research_cycle"))),
    ("Part V -- Claim and Review Governance", (
        (27, "Scientific Claim Registry", "scientific_claims"),
        (28, "Theory Ledger", "scientific_claims"),
        (29, "Independent Review Pack", "independent_review"),
        (30, "Reviewer Feedback Assimilation", "review_assimilation"),
        (31, "Publication Discipline and Forbidden Claims", "scientific_claims"))),
    ("Part VI -- Alpha Operation", (
        (32, "Unified CLI", "alpha_system"),
        (33, "Alpha State Layout", "alpha_system"),
        (34, "End-to-End Fixture Demo", "alpha_system"),
        (35, "Operator Runbook", "alpha_system"),
        (36, "Troubleshooting and Missing Modules", "alpha_system"))),
    ("Part VII -- Safety, Limits, and Future Work", (
        (37, "Safety Boundaries", ""),
        (38, "Known Limitations", ""),
        (39, "Open Research Questions", ""),
        (40, "Roadmap After Alpha", ""),
        (41, "Appendices", ""))),
)

_PACKAGE_ROOT = "solaris_ai_nn"


@dataclass
class OutlineChapter:
    """One outline entry with its implementation status."""

    number: int
    title: str
    part: str
    module_key: str = ""
    implemented: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"number": self.number, "title": self.title, "part": self.part,
                "module_key": self.module_key, "implemented": self.implemented,
                "implementation_status": ("implemented" if self.implemented
                                          else "planned_or_missing")}


@dataclass
class SolarisArchitectureOutlineBuilder:
    """Builds the architecture-book outline with honest implementation status."""

    def build(self) -> List[OutlineChapter]:
        out: List[OutlineChapter] = []
        for part, chapters in _OUTLINE:
            for number, title, module_key in chapters:
                implemented = (not module_key) or self._available(module_key)
                out.append(OutlineChapter(
                    number=number, title=title, part=part,
                    module_key=module_key, implemented=implemented))
        return out

    @staticmethod
    def _available(module_key: str) -> bool:
        try:
            return importlib.util.find_spec(
                f"{_PACKAGE_ROOT}.{module_key}") is not None
        except Exception:
            return False

    def parts(self) -> List[str]:
        return [part for part, _ in _OUTLINE]

    def summary(self) -> Dict[str, Any]:
        chapters = self.build()
        return {
            "outline_part_count": len(_OUTLINE),
            "outline_chapter_count": len(chapters),
            "implemented_chapter_count": sum(1 for c in chapters
                                             if c.implemented),
            "planned_chapter_count": sum(1 for c in chapters
                                         if not c.implemented),
            "parts": self.parts(),
            "chapters": [c.to_dict() for c in chapters],
            "note": "'organismic' is architecture/metaphor language only; no "
                    "biological life is claimed; planned/missing modules are "
                    "marked honestly",
        }

    def render_md(self) -> str:
        lines = ["## Architecture Book Outline", ""]
        for part, chapters in _OUTLINE:
            lines.append(f"### {part}")
            lines.append("")
            for number, title, module_key in chapters:
                implemented = (not module_key) or self._available(module_key)
                tag = "" if implemented else " _(planned/missing)_"
                lines.append(f"{number}. {title}{tag}")
            lines.append("")
        lines.append("_'Organismic' is an architectural metaphor; the system "
                     "makes no claim of biological life._")
        return "\n".join(lines)

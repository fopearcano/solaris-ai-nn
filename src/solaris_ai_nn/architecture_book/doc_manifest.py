"""Documentation manifest -- indexes the local sources the book is built from.

:class:`DocumentationManifest` indexes the local documentation/artifact sources the
whitepaper and architecture book are reconstructed from. It indexes local sources
only, lists missing and contradictory sources explicitly, marks stale sources when
detectable, and never pretends missing source material exists.

This module also holds :data:`PROMPTS` -- the static Prompt 41-66 metadata table
(prompt number, module key, label, package path, required/optional) reused by the
outline, module-map, and appendix builders.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# (prompt number, module key, label, package path, required-for-alpha)
PROMPTS: Tuple[Tuple[int, str, str, str, bool], ...] = (
    (41, "plural_sensorium", "Plural Sensorium",
     "solaris_ai_nn.plural_sensorium", False),
    (42, "organismic_demo", "Minimal Field Organism Demo",
     "solaris_ai_nn.organismic_demo", False),
    (43, "live_field", "Real Read-Only Environmental Feeder Pack / Live Field",
     "solaris_ai_nn.live_field", False),
    (44, "sensorium_lab", "Sensorium Differentiation Lab",
     "solaris_ai_nn.sensorium_lab", False),
    (45, "feeder_sdk", "External Feeder SDK", "solaris_ai_nn.feeder_sdk", False),
    (46, "perceptual_metabolism", "Perceptual Metabolism",
     "solaris_ai_nn.perceptual_metabolism", False),
    (47, "perceptual_ontogenesis", "Sensorium-Native Ontogenesis",
     "solaris_ai_nn.perceptual_ontogenesis", False),
    (48, "semiogenesis", "Sensorium-Native Semiogenesis",
     "solaris_ai_nn.semiogenesis", False),
    (49, "sensorium_cognition", "Sensorium-Native Cognition",
     "solaris_ai_nn.sensorium_cognition", False),
    (50, "self_boundary", "Sensorium-Native Self-Boundary",
     "solaris_ai_nn.self_boundary", False),
    (51, "desire_formation", "Valence / Desire Formation",
     "solaris_ai_nn.desire_formation", False),
    (52, "action_reaction", "Action-Reaction / Consequence Learning",
     "solaris_ai_nn.action_reaction", False),
    (53, "developmental_life", "Long-Horizon Developmental Runtime",
     "solaris_ai_nn.developmental_life", False),
    (54, "developmental_soak", "Month-Scale Developmental Soak Protocol",
     "solaris_ai_nn.developmental_soak", False),
    (55, "developmental_replication", "Cross-Run Replication and Falsification Lab",
     "solaris_ai_nn.developmental_replication", False),
    (56, "architecture_evolution", "Architecture Evolution Lab",
     "solaris_ai_nn.architecture_evolution", False),
    (57, "experiment_compiler", "Experiment Compiler",
     "solaris_ai_nn.experiment_compiler", False),
    (58, "implementation_intake", "Implementation Intake",
     "solaris_ai_nn.implementation_intake", False),
    (59, "post_merge_assimilation", "Post-Merge Assimilation",
     "solaris_ai_nn.post_merge_assimilation", False),
    (60, "research_baseline", "Versioned Research Baseline",
     "solaris_ai_nn.research_baseline", False),
    (61, "research_cycle", "Closed Research Cycle Orchestrator",
     "solaris_ai_nn.research_cycle", False),
    (62, "scientific_claims", "Scientific Claim Registry",
     "solaris_ai_nn.scientific_claims", False),
    (63, "independent_review", "Independent Reproducibility Review",
     "solaris_ai_nn.independent_review", False),
    (64, "review_assimilation", "Reviewer Feedback Assimilation",
     "solaris_ai_nn.review_assimilation", False),
    (65, "alpha_system", "Alpha Research System Assembly and Unified CLI",
     "solaris_ai_nn.alpha_system", True),
    (66, "architecture_book", "Technical Whitepaper and Architecture Book",
     "solaris_ai_nn.architecture_book", True),
)


class DocumentationBuildStatus:
    OK = "ok"
    OK_WITH_WARNINGS = "ok_with_warnings"
    MISSING_SOURCES = "missing_sources"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (OK, OK_WITH_WARNINGS, MISSING_SOURCES, BLOCKED, UNKNOWN)


class DocumentationSourceCategory:
    ORIGINAL_WHITEPAPER = "original_solaris_ai_whitepaper"
    README = "readme"
    DOCS = "docs"
    ARCHITECTURE_NOTES = "architecture_notes"
    MODULE_REPORTS = "module_reports"
    PROMPT_SPEC = "prompt_derived_specification"
    ALPHA_REPORTS = "alpha_system_reports"
    CLAIM_REPORTS = "scientific_claim_reports"
    SAFETY_REPORTS = "safety_reports"
    BASELINE_REPORTS = "research_baseline_reports"
    REVIEW_REPORTS = "independent_review_reports"
    MISSING_SOURCE_MARKER = "missing_source_marker"

    ALL = (ORIGINAL_WHITEPAPER, README, DOCS, ARCHITECTURE_NOTES, MODULE_REPORTS,
           PROMPT_SPEC, ALPHA_REPORTS, CLAIM_REPORTS, SAFETY_REPORTS,
           BASELINE_REPORTS, REVIEW_REPORTS, MISSING_SOURCE_MARKER)


@dataclass
class DocumentationSource:
    """One indexed local source (ref/path only; not copied verbatim)."""

    category: str
    ref: str = ""
    present: bool = True
    stale: bool = False
    contradictory: bool = False
    detail: str = ""

    def __post_init__(self) -> None:
        if self.category not in DocumentationSourceCategory.ALL:
            self.category = DocumentationSourceCategory.MISSING_SOURCE_MARKER
        if self.category == DocumentationSourceCategory.MISSING_SOURCE_MARKER:
            self.present = False

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "ref": self.ref,
                "present": self.present, "stale": self.stale,
                "contradictory": self.contradictory, "detail": self.detail}


@dataclass
class DocumentationArtifact:
    """One generated documentation artifact."""

    name: str
    path: str
    generated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "path": self.path,
                "generated": self.generated}


@dataclass
class DocumentationManifest:
    """Indexes local sources + generated artifacts (missing stays visible)."""

    state_dir: str = ".solaris_ai_nn_docs"
    persist: bool = True
    sources: List[DocumentationSource] = field(default_factory=list, init=False)
    artifacts: List[DocumentationArtifact] = field(default_factory=list,
                                                   init=False)
    status: str = DocumentationBuildStatus.UNKNOWN
    created_ts: float = field(default_factory=time.time, init=False)

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.state_dir, "DOC_MANIFEST.json")

    def add_source(self, source: DocumentationSource) -> DocumentationSource:
        self.sources.append(source)
        return source

    def add_missing(self, ref: str, detail: str = "") -> DocumentationSource:
        return self.add_source(DocumentationSource(
            category=DocumentationSourceCategory.MISSING_SOURCE_MARKER,
            ref=ref, present=False,
            detail=detail or "source not present locally"))

    def add_artifact(self, name: str, path: str) -> DocumentationArtifact:
        art = DocumentationArtifact(name=name, path=path)
        self.artifacts.append(art)
        return art

    def present(self) -> List[DocumentationSource]:
        return [s for s in self.sources if s.present]

    def missing(self) -> List[DocumentationSource]:
        return [s for s in self.sources if not s.present]

    def contradictory(self) -> List[DocumentationSource]:
        return [s for s in self.sources if s.contradictory]

    def stale(self) -> List[DocumentationSource]:
        return [s for s in self.sources if s.stale]

    def index(self) -> Dict[str, Any]:
        return {
            "documentation_source_count": len(self.sources),
            "present_source_count": len(self.present()),
            "missing_documentation_source_count": len(self.missing()),
            "contradictory_source_count": len(self.contradictory()),
            "stale_source_count": len(self.stale()),
            "generated_document_count": len(self.artifacts),
            "status": self.status,
        }

    def persist_manifest(self) -> str:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        return self.manifest_path

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["sources"] = [s.to_dict() for s in self.sources]
        d["artifacts"] = [a.to_dict() for a in self.artifacts]
        d["note"] = ("indexes local sources only; missing and contradictory "
                     "sources are listed explicitly; missing source material is "
                     "never pretended to exist")
        return d

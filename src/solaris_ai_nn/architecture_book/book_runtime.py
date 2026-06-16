"""Architecture book runtime -- the bounded, local documentation generator.

:class:`ArchitectureBookRuntime` collects local sources, builds the documentation
manifest, outline, diagrams, glossary, technical overview, whitepaper, architecture
book, module map, research roadmap, safety-boundaries document, appendices, and
documentation index, runs the documentation safety validator and a ClaimGuard scan,
and produces a build report. It writes documentation only: it publishes nothing,
uploads nothing, calls no Git/GitHub, runs no Git, runs no external agent, executes
no experiment, controls no hardware/feeders/network/shell, and generates no
unsupported claim.
"""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .appendix_builder import ArchitectureAppendixBuilder
from .architecture_book_builder import ArchitectureBookBuilder
from .diagram_builder import DiagramBuilder
from .doc_index import DocumentationIndexBuilder
from .doc_manifest import (
    PROMPTS,
    DocumentationBuildStatus,
    DocumentationManifest,
    DocumentationSource,
    DocumentationSourceCategory,
)
from .glossary_builder import GlossaryBuilder
from .outline_builder import SolarisArchitectureOutlineBuilder
from .safety import ArchitectureBookSafetyValidator
from .source_collector import ArchitectureSourceCollector
from .whitepaper_builder import TechnicalWhitepaperBuilder

_PACKAGE_ROOT = "solaris_ai_nn"

# Generated documents under docs_dir: (attribute, filename).
_DOC_FILES = (
    ("overview", "SOLARIS_AI_NN_TECHNICAL_OVERVIEW.md"),
    ("whitepaper", "SOLARIS_AI_NN_WHITEPAPER.md"),
    ("book", "SOLARIS_AI_NN_ARCHITECTURE_BOOK.md"),
    ("module_map", "SOLARIS_AI_NN_MODULE_MAP.md"),
    ("roadmap", "SOLARIS_AI_NN_RESEARCH_ROADMAP.md"),
    ("safety_boundaries", "SOLARIS_AI_NN_SAFETY_BOUNDARIES.md"),
    ("glossary", "SOLARIS_AI_NN_GLOSSARY.md"),
    ("appendices", "SOLARIS_AI_NN_APPENDICES.md"),
    ("doc_index", "SOLARIS_AI_NN_DOCUMENTATION_INDEX.md"),
)


@dataclass
class ArchitectureBookRuntime:
    """Bounded, local documentation generator for the whitepaper + book."""

    state_dir: str = ".solaris_ai_nn_docs"
    docs_dir: str = "docs/whitepaper"
    source_roots: List[str] = field(default_factory=list)
    include_prompt_roadmap: bool = True
    include_mermaid: bool = True
    report_only: bool = False
    dry_run: bool = False
    max_runtime_s: float = 60.0
    require_claimguard: bool = False
    strict: bool = False

    safety: ArchitectureBookSafetyValidator = field(
        default_factory=ArchitectureBookSafetyValidator, init=False)
    manifest: Any = field(default=None, init=False)
    collection: Dict[str, Any] = field(default_factory=dict, init=False)
    outline: Dict[str, Any] = field(default_factory=dict, init=False)
    diagrams: Dict[str, Any] = field(default_factory=dict, init=False)
    glossary: Dict[str, Any] = field(default_factory=dict, init=False)
    book: Dict[str, Any] = field(default_factory=dict, init=False)
    appendices: Dict[str, Any] = field(default_factory=dict, init=False)
    doc_index_summary: Dict[str, Any] = field(default_factory=dict, init=False)
    documents: Dict[str, str] = field(default_factory=dict, init=False)
    claim_guard_block_count: int = field(default=0, init=False)
    claimguard_available: bool = field(default=False, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.manifest = DocumentationManifest(state_dir=self.state_dir,
                                              persist=not self.dry_run)
        if not self.max_runtime_s:
            self._refused = True

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}

        # 1. Collect local sources (read-only).
        collector = ArchitectureSourceCollector(source_roots=self.source_roots)
        result = collector.collect()
        self.collection = result.to_dict()
        self._build_manifest(result)

        # 2. Build the document bodies.
        self.outline = SolarisArchitectureOutlineBuilder().summary()
        diagram_builder = DiagramBuilder()
        self.diagrams = diagram_builder.summary()
        glossary_builder = GlossaryBuilder()
        self.glossary = glossary_builder.summary()
        wp = TechnicalWhitepaperBuilder()
        book_builder = ArchitectureBookBuilder()
        self.book = book_builder.summary()
        appendix_builder = ArchitectureAppendixBuilder()
        self.appendices = appendix_builder.summary()

        bodies = {
            "overview": wp.build_overview(),
            "whitepaper": wp.build_whitepaper(),
            "book": book_builder.build(),
            "module_map": self._module_map_md(),
            "roadmap": self._roadmap_md(),
            "safety_boundaries": self._safety_boundaries_md(),
            "glossary": glossary_builder.render_md(),
            "appendices": appendix_builder.build(),
        }
        if not self.include_mermaid:
            bodies["book"] = bodies["book"]  # diagrams already embedded as text

        # 3. ClaimGuard / safety scan over generated text.
        self._scan(bodies)

        # 4. Write documents (unless dry-run).
        if not self.dry_run:
            self._write_docs(bodies)
            self._build_doc_index()
            self.manifest.persist_manifest()
        else:
            self.doc_index_summary = DocumentationIndexBuilder(
                docs_dir=self.docs_dir).build().to_dict()

        self.manifest.status = (
            DocumentationBuildStatus.OK_WITH_WARNINGS
            if self.manifest.missing() else DocumentationBuildStatus.OK)
        return {"refused": False,
                "generated_document_count": len(self.documents),
                "missing_source_count":
                    self.manifest.index()["missing_documentation_source_count"],
                "claimguard_block_count": self.claim_guard_block_count}

    # -- helpers ------------------------------------------------------------

    def _build_manifest(self, result) -> None:
        cat = DocumentationSourceCategory
        # README + docs.
        for src in result.sources:
            present = src.present
            if src.label == "readme":
                category = cat.README
            elif src.label == "docs":
                category = cat.DOCS
            elif src.label == "examples":
                category = cat.ARCHITECTURE_NOTES
            elif src.label.startswith("state:alpha"):
                category = cat.ALPHA_REPORTS
            elif src.label.startswith("state:claims"):
                category = cat.CLAIM_REPORTS
            elif src.label.startswith("state:research_baseline"):
                category = cat.BASELINE_REPORTS
            elif src.label.startswith("state:review"):
                category = cat.REVIEW_REPORTS
            else:
                category = cat.MODULE_REPORTS
            if present:
                self.manifest.add_source(DocumentationSource(
                    category=category, ref=src.path, present=True,
                    detail=f"{src.file_count} file(s)"))
            else:
                self.manifest.add_missing(src.path, "source directory absent")
        # Original Solaris_Ai whitepaper (reference repo; not local by default).
        self.manifest.add_missing(
            "fopearcano/solaris-ai whitepaper",
            "original Solaris_Ai whitepaper not present in this local checkout")
        # Prompt-derived specs are always available as a category.
        self.manifest.add_source(DocumentationSource(
            category=cat.PROMPT_SPEC, ref="prompts_41_66",
            present=True, detail=f"{len(PROMPTS)} prompt specifications"))

    def _scan(self, bodies: Dict[str, str]) -> None:
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            self.claimguard_available = True
        except Exception:
            guard = None
            self.claimguard_available = False
        for name, text in bodies.items():
            # Documentation safety validator (forbidden claims / marketing).
            report = self.safety.validate_doc_text(text)
            if not report.safe:
                self.claim_guard_block_count += 1
            if guard is not None and not guard.scan_text(text).safe:
                self.claim_guard_block_count += 1

    def _write_docs(self, bodies: Dict[str, str]) -> None:
        os.makedirs(self.docs_dir, exist_ok=True)
        for attr, filename in _DOC_FILES:
            if attr == "doc_index":
                continue  # written by _build_doc_index
            body = bodies.get(attr, "")
            body = self._guard(body)
            path = os.path.join(self.docs_dir, filename)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            self.documents[attr] = path
            self.manifest.add_artifact(filename, path)

    def _build_doc_index(self) -> None:
        builder = DocumentationIndexBuilder(docs_dir=self.docs_dir)
        index = builder.build()
        self.doc_index_summary = index.to_dict()
        path = os.path.join(self.docs_dir, "SOLARIS_AI_NN_DOCUMENTATION_INDEX.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(index.render_md())
        self.documents["doc_index"] = path
        self.manifest.add_artifact("SOLARIS_AI_NN_DOCUMENTATION_INDEX.md", path)
        # Mirror a short index into the state dir.
        os.makedirs(self.state_dir, exist_ok=True)
        with open(os.path.join(self.state_dir, "DOC_INDEX.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(index.render_md())

    @staticmethod
    def _guard(text: str) -> str:
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                return guard.rewrite(text)
        except Exception:
            pass
        return text

    def _available(self, pkg: str) -> bool:
        try:
            return importlib.util.find_spec(pkg) is not None
        except Exception:
            return False

    def _module_map_md(self) -> str:
        lines = ["# Solaris-AI-NN Module Map", "",
                 "| prompt | module | package | required | status |",
                 "| --- | --- | --- | --- | --- |"]
        for num, key, _label, pkg, req in PROMPTS:
            status = "implemented" if self._available(pkg) else "planned/missing"
            lines.append(f"| {num} | {key} | `{pkg}` | {req} | {status} |")
        lines += ["", "_Each module is a bounded local software component. "
                  "'Organismic' terms are metaphors; no biological life is "
                  "claimed. Missing modules are shown honestly._"]
        return "\n".join(lines) + "\n"

    def _roadmap_md(self) -> str:
        phases = [
            ("Phase 1: Organismic Core", "plural_sensorium",
             "sensorium -> metabolism -> cognition -> action core loop"),
            ("Phase 2: Long-Horizon Development", "developmental_life",
             "bounded long-runtime developmental tracking"),
            ("Phase 3: Soak / Replication / Falsification", "developmental_soak",
             "evidence dossiers, replication, falsification, controls"),
            ("Phase 4: Architecture Evolution", "architecture_evolution",
             "evidence-driven variant proposals (proposal-only)"),
            ("Phase 5: Implementation Governance", "implementation_intake",
             "experiment compiler + intake audit + post-merge assimilation"),
            ("Phase 6: Research Baseline and Cycle", "research_cycle",
             "versioned baseline + closed cycle orchestration"),
            ("Phase 7: Claim Governance", "scientific_claims",
             "claim registry, theory ledger, forbidden-claim discipline"),
            ("Phase 8: Independent Review", "independent_review",
             "local reviewer pack + reproducibility + assimilation"),
            ("Phase 9: Alpha System", "alpha_system",
             "unified local CLI + bounded fixture end-to-end demo"),
            ("Phase 10: Documentation / Whitepaper", "architecture_book",
             "technical whitepaper + architecture book reconstruction"),
        ]
        lines = ["# Solaris-AI-NN Research Roadmap", ""]
        for title, key, desc in phases:
            implemented = self._available(f"{_PACKAGE_ROOT}.{key}")
            lines.append(f"## {title}")
            lines.append("")
            lines.append(f"- current status: "
                         f"{'implemented' if implemented else 'planned/missing'}")
            lines.append(f"- scope: {desc}")
            lines.append("- next recommended work: strengthen evidence, controls, "
                         "and replication; close documented gaps")
            lines.append("- blockers: none beyond evidence and operator decision")
            lines.append("- evidence needed: replication across seeds, controls, "
                         "and (eventually) governed live read-only data")
            lines.append("")
        lines.append("_The roadmap is planning only; nothing is executed and no "
                     "claim of consciousness/life/agency is made._")
        return "\n".join(lines) + "\n"

    def _safety_boundaries_md(self) -> str:
        return (
            "# Solaris-AI-NN Safety Boundaries\n\n"
            "## Hard prohibitions\n\n"
            "- no real-world actuation; no hardware control\n"
            "- no feeder control or auto-start (feeders are operator-run)\n"
            "- no network/shell/browser/OS access from the runtime\n"
            "- no Git/GitHub call; no Git command; no branch/tag/release/PR\n"
            "- no upload; no publishing; no external agent execution\n"
            "- no source self-rewrite; the human merges code outside the system\n"
            "- no Human Feedback / Teaching Loop; reviewer feedback is evidence, "
            "not training\n"
            "- no forbidden scientific claims (consciousness, sentience, "
            "biological life, personhood, agency, free will, emotion, feeling, "
            "understanding, self-awareness, subjective experience)\n\n"
            "## Local-only default\n\n"
            "All runtimes default to local-only, bounded operation. The alpha "
            "profile is fixture-only by default.\n\n"
            "## Read-only feeder policy\n\n"
            "Feeders are external and operator-run; Solaris reads their output "
            "only and never starts or controls them.\n\n"
            "## No hardware / real-world actuation\n\n"
            "No module actuates anything in the world or controls any device.\n\n"
            "## No source self-rewrite\n\n"
            "The architecture proposes changes; a human implements and merges "
            "them outside the system.\n\n"
            "## No Git/GitHub automation\n\n"
            "No runtime calls Git or GitHub or creates branches/tags/releases/"
            "PRs.\n\n"
            "## No publication automation\n\n"
            "Documentation and reports are local; nothing is published or "
            "uploaded.\n\n"
            "## No Human Feedback / Teaching Loop\n\n"
            "Reviewer feedback is assimilated as research evidence; the model is "
            "never trained from it.\n\n"
            "## No forbidden scientific claims\n\n"
            "ClaimGuard scans generated text; forbidden inner-state claims are "
            "blocked, not asserted.\n\n"
            "## Operator authority\n\n"
            "The human operator decides; the system proposes and reports.\n\n"
            "## Audit and evidence preservation\n\n"
            "Negative, falsified, and inconclusive evidence is preserved; missing "
            "modules, evidence, and limitations are shown, never hidden.\n\n"
            "_This document is local Markdown; no publication or upload occurred "
            "and no consciousness/life/agency claim is made._\n")

    # -- integration views --------------------------------------------------

    def documentation_status(self) -> Dict[str, Any]:
        mi = self.manifest.index()
        return {
            "architecture_book_enabled": True,
            "documentation_source_count": mi["documentation_source_count"],
            "missing_documentation_source_count":
                mi["missing_documentation_source_count"],
            "generated_document_count": len(self.documents),
            "generated_chapter_count": self.book.get(
                "generated_chapter_count", 0),
            "skipped_chapter_count": self.book.get("skipped_chapter_count", 0),
            "generated_diagram_count": self.diagrams.get(
                "generated_diagram_count", 0),
            "glossary_entry_count": self.glossary.get("glossary_entry_count", 0),
            "documentation_safety_block_count": self.safety.rejected_count,
            "claimguard_documentation_block_count": self.claim_guard_block_count,
            "claimguard_available": self.claimguard_available,
            "latest_whitepaper_path": self.documents.get("whitepaper"),
            "latest_architecture_book_path": self.documents.get("book"),
            "published": False, "uploaded": False, "runs_git": False,
            "calls_github": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.documentation_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import ArchitectureBookReportBuilder

        return ArchitectureBookReportBuilder(self).write()

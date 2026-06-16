"""Technical whitepaper and architecture book -- documentation reconstruction.

Prompts 41-65 created a large research architecture. Prompt 66 turns the whole
project into a coherent technical whitepaper and architecture book: a short
technical overview, a full whitepaper, a longer architecture book, Mermaid
diagrams, a glossary, a module map, a research roadmap, a safety-boundary chapter,
appendices, and a local documentation index.

This is documentation reconstruction, not marketing, not a consciousness manifesto,
not a public release, and not proof of intelligence. The generator reads local
sources and writes local Markdown only: it publishes nothing, uploads nothing,
calls no Git/GitHub, runs no Git, runs no external agent, executes no experiment,
controls no hardware/feeders/network/shell, and makes no claim of consciousness,
sentience, biological life, personhood, agency, free will, emotion, feeling,
understanding, self-awareness, or subjective experience. "Organismic" is an
architectural metaphor throughout.
"""

from __future__ import annotations

from .appendix_builder import ArchitectureAppendixBuilder
from .architecture_book_builder import ArchitectureBookBuilder
from .book_runtime import ArchitectureBookRuntime
from .chapter_model import (
    ArchitectureChapter,
    ChapterEvidenceRef,
    ChapterSection,
    ChapterStatus,
)
from .diagram_builder import (
    ArchitectureDiagram,
    DiagramBuilder,
    DiagramKind,
)
from .doc_index import DocumentationIndex, DocumentationIndexBuilder
from .doc_manifest import (
    PROMPTS,
    DocumentationArtifact,
    DocumentationBuildStatus,
    DocumentationManifest,
    DocumentationSource,
    DocumentationSourceCategory,
)
from .glossary_builder import GlossaryBuilder, GlossaryEntry
from .outline_builder import (
    OutlineChapter,
    SolarisArchitectureOutlineBuilder,
)
from .reports import ArchitectureBookReportBuilder
from .safety import HARD_RULES, ArchitectureBookSafetyValidator
from .source_collector import (
    ArchitectureSourceCollector,
    CollectedSource,
    SourceCollectionResult,
)
from .whitepaper_builder import TechnicalWhitepaperBuilder

__all__ = [
    "DocumentationManifest", "DocumentationSource", "DocumentationArtifact",
    "DocumentationBuildStatus", "DocumentationSourceCategory", "PROMPTS",
    "ArchitectureSourceCollector", "CollectedSource", "SourceCollectionResult",
    "ArchitectureChapter", "ChapterSection", "ChapterStatus",
    "ChapterEvidenceRef",
    "SolarisArchitectureOutlineBuilder", "OutlineChapter",
    "DiagramBuilder", "ArchitectureDiagram", "DiagramKind",
    "GlossaryBuilder", "GlossaryEntry",
    "TechnicalWhitepaperBuilder",
    "ArchitectureBookBuilder",
    "ArchitectureAppendixBuilder",
    "DocumentationIndex", "DocumentationIndexBuilder",
    "ArchitectureBookRuntime",
    "ArchitectureBookReportBuilder",
    "HARD_RULES", "ArchitectureBookSafetyValidator",
]

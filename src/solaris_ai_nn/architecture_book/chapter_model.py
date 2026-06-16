"""Chapter model -- the structured unit of the architecture book.

:class:`ArchitectureChapter` is one chapter with its sections, status, and
evidence refs. Every major chapter must carry source/evidence refs or an explicit
note that it is reconstructed from prompt specifications; chapters include
limitations where relevant; and a chapter that would assert a forbidden claim is
marked ``blocked_by_claim_safety`` rather than emitted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ChapterStatus:
    DRAFT = "draft"
    COMPLETE = "complete"
    COMPLETE_WITH_WARNINGS = "complete_with_warnings"
    MISSING_SOURCES = "missing_sources"
    BLOCKED_BY_CLAIM_SAFETY = "blocked_by_claim_safety"
    UNKNOWN = "unknown"

    ALL = (DRAFT, COMPLETE, COMPLETE_WITH_WARNINGS, MISSING_SOURCES,
           BLOCKED_BY_CLAIM_SAFETY, UNKNOWN)


@dataclass
class ChapterEvidenceRef:
    """A reference to a source/evidence artifact backing a chapter."""

    kind: str
    ref: str
    present: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "present": self.present}


@dataclass
class ChapterSection:
    """One titled section of a chapter."""

    title: str
    body: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "body": self.body}

    def render_md(self, level: int = 3) -> str:
        return f"{'#' * level} {self.title}\n\n{self.body}\n"


@dataclass
class ArchitectureChapter:
    """One architecture-book chapter."""

    number: str
    title: str
    part: str = ""
    sections: List[ChapterSection] = field(default_factory=list)
    evidence_refs: List[ChapterEvidenceRef] = field(default_factory=list)
    reconstructed_from_spec: bool = False
    limitations: List[str] = field(default_factory=list)
    status: str = ChapterStatus.DRAFT
    implementation_status: str = "implemented"

    def __post_init__(self) -> None:
        if self.status not in ChapterStatus.ALL:
            self.status = ChapterStatus.UNKNOWN

    @property
    def has_evidence_basis(self) -> bool:
        return bool(self.evidence_refs) or self.reconstructed_from_spec

    def add_section(self, title: str, body: str) -> ChapterSection:
        s = ChapterSection(title=title, body=body)
        self.sections.append(s)
        return s

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number, "title": self.title, "part": self.part,
            "section_count": len(self.sections),
            "sections": [s.to_dict() for s in self.sections],
            "evidence_refs": [e.to_dict() for e in self.evidence_refs],
            "reconstructed_from_spec": self.reconstructed_from_spec,
            "has_evidence_basis": self.has_evidence_basis,
            "limitations": list(self.limitations),
            "status": self.status,
            "implementation_status": self.implementation_status,
        }

    def render_md(self, level: int = 2) -> str:
        lines = [f"{'#' * level} {self.number}. {self.title}", ""]
        if self.reconstructed_from_spec and not self.evidence_refs:
            lines.append("> _Reconstructed from prompt specifications; see the "
                         "module map for the implementing package._")
            lines.append("")
        lines.append(f"_Implementation status: {self.implementation_status}._")
        lines.append("")
        for s in self.sections:
            lines.append(s.render_md(level=level + 1))
        if self.limitations:
            lines.append(f"{'#' * (level + 1)} Limitations")
            lines.append("")
            lines += [f"- {l}" for l in self.limitations]
            lines.append("")
        return "\n".join(lines)

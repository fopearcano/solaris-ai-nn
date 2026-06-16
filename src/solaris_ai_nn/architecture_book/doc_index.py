"""Documentation index -- lists the generated docs and the missing ones.

:class:`DocumentationIndexBuilder` builds the documentation index that points to
the overview, whitepaper, architecture book, module map, roadmap, safety
boundaries, glossary, appendices, and (when present) the alpha / scientific-claim /
independent-review reports. Missing documents are listed explicitly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# (label, filename relative to docs_dir, optional)
_WHITEPAPER_DOCS = (
    ("Technical Overview", "SOLARIS_AI_NN_TECHNICAL_OVERVIEW.md", False),
    ("Technical Whitepaper", "SOLARIS_AI_NN_WHITEPAPER.md", False),
    ("Architecture Book", "SOLARIS_AI_NN_ARCHITECTURE_BOOK.md", False),
    ("Module Map", "SOLARIS_AI_NN_MODULE_MAP.md", False),
    ("Research Roadmap", "SOLARIS_AI_NN_RESEARCH_ROADMAP.md", False),
    ("Safety Boundaries", "SOLARIS_AI_NN_SAFETY_BOUNDARIES.md", False),
    ("Glossary", "SOLARIS_AI_NN_GLOSSARY.md", False),
    ("Appendices", "SOLARIS_AI_NN_APPENDICES.md", False),
    ("Documentation Index", "SOLARIS_AI_NN_DOCUMENTATION_INDEX.md", False),
)
# (label, repo-relative report path)
_EXTERNAL_REPORTS = (
    ("Alpha Report",
     ".solaris_ai_nn_alpha/reports/ALPHA_RESEARCH_SYSTEM_REPORT.md"),
    ("Scientific Claim Report",
     ".solaris_ai_nn_claims/SCIENTIFIC_CLAIM_REPORT.md"),
    ("Independent Review Report",
     ".solaris_ai_nn_review/INDEPENDENT_REVIEW_REPORT.md"),
)


@dataclass
class DocumentationIndex:
    """The documentation index records (present + missing)."""

    docs_dir: str
    repo_root: str
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def present(self) -> List[Dict[str, Any]]:
        return [e for e in self.entries if e["present"]]

    def missing(self) -> List[Dict[str, Any]]:
        return [e for e in self.entries if not e["present"]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "docs_dir": self.docs_dir,
            "documentation_index_entry_count": len(self.entries),
            "present_document_count": len(self.present()),
            "missing_document_count": len(self.missing()),
            "entries": list(self.entries),
            "note": "lists generated docs and missing docs explicitly; missing "
                    "documents are never hidden",
        }

    def render_md(self) -> str:
        lines = ["# Solaris-AI-NN Documentation Index", "",
                 "| document | present | path |", "| --- | --- | --- |"]
        for e in self.entries:
            lines.append(f"| {e['label']} | {e['present']} | `{e['path']}` |")
        lines += ["", "## Missing documents", ""]
        miss = self.missing()
        lines += [f"- {e['label']} (`{e['path']}`)" for e in miss] or ["- none"]
        lines += ["", "_Local documentation index; no publication or upload "
                  "occurred._"]
        return "\n".join(lines) + "\n"


@dataclass
class DocumentationIndexBuilder:
    """Builds the documentation index from the docs dir + local reports."""

    docs_dir: str = "docs/whitepaper"
    repo_root: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.repo_root:
            here = os.path.dirname(os.path.abspath(__file__))
            self.repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))

    def build(self) -> DocumentationIndex:
        idx = DocumentationIndex(docs_dir=self.docs_dir, repo_root=self.repo_root)
        for label, fn, _opt in _WHITEPAPER_DOCS:
            path = os.path.join(self.docs_dir, fn)
            idx.entries.append({"label": label, "path": path,
                                "present": os.path.isfile(path),
                                "optional": False})
        for label, rel in _EXTERNAL_REPORTS:
            path = os.path.join(self.repo_root, rel)
            idx.entries.append({"label": label, "path": rel,
                                "present": os.path.isfile(path),
                                "optional": True})
        return idx

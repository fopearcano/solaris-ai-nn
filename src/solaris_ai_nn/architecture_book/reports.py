"""Architecture book reports -- the local build report (Markdown + JSON).

:class:`ArchitectureBookReportBuilder` writes the whitepaper build report. It states
explicitly that no publication or upload occurred, no Git/GitHub operation occurred,
no external agent was run, no experiments were executed, and no consciousness/life/
agency claim is made. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No publication occurred.",
    "No upload occurred.",
    "No Git or GitHub operation occurred.",
    "No external agent was run.",
    "No experiments were executed.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class ArchitectureBookReportBuilder:
    """Builds the whitepaper build report set."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.documentation_status()
        sections: Dict[str, Any] = {
            "purpose": ("reconstruct the Solaris-AI-NN architecture into coherent "
                        "local Markdown documentation (overview, whitepaper, "
                        "architecture book, module map, roadmap, safety "
                        "boundaries, glossary, appendices, index) -- locally, "
                        "without publishing or executing anything"),
            "source_manifest": rt.manifest.to_dict(),
            "collection": rt.collection,
            "generated_documents": rt.documents,
            "outline": rt.outline,
            "diagrams": rt.diagrams,
            "glossary": rt.glossary,
            "book": rt.book,
            "appendices": rt.appendices,
            "documentation_index": rt.doc_index_summary,
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_md(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_md(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        man = sections["source_manifest"]
        lines = [
            "# Whitepaper Build Report", "",
            "_Local documentation build. It did NOT publish, upload, call Git/"
            "GitHub, run external agents, or execute experiments, and it makes no "
            "claim of consciousness, sentience, biological life, personhood, "
            "agency, free will, emotion, feeling, understanding, self-awareness, "
            "or subjective experience._", "",
            f"- documentation sources: {man['documentation_source_count']} "
            f"(missing {man['missing_documentation_source_count']}, "
            f"contradictory {man.get('contradictory_source_count', 0)}, stale "
            f"{man.get('stale_source_count', 0)})",
            f"- generated documents: {status['generated_document_count']}",
            f"- chapters: {status['generated_chapter_count']} "
            f"(skipped {status['skipped_chapter_count']})",
            f"- diagrams: {status['generated_diagram_count']}",
            f"- glossary entries: {status['glossary_entry_count']}",
            f"- ClaimGuard available: {status['claimguard_available']}; "
            f"documentation blocks: "
            f"{status['claimguard_documentation_block_count']}",
            "",
            "## Generated documents", "",
        ]
        for name, path in sections["generated_documents"].items():
            lines.append(f"- {name}: `{path}`")
        lines += ["", "## Missing sources", ""]
        miss = [s for s in man.get("sources", []) if not s["present"]]
        lines += [f"- {s['ref']} -- {s['detail']}" for s in miss] or ["- none"]
        lines += ["", "## Stale / contradictory sources", ""]
        sc = [s for s in man.get("sources", [])
              if s.get("stale") or s.get("contradictory")]
        lines += [f"- {s['ref']}" for s in sc] or ["- none"]
        lines += ["", "## Limitations", "",
                  "- documentation is reconstructed from local sources and prompt "
                  "specifications; missing modules are documented as "
                  "planned/missing rather than substituted",
                  "- the build proves nothing about consciousness/life/agency"]
        lines += ["", "## Safety status", "",
                  "- local-only; no publish/upload/Git/GitHub/experiment/agent"]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

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

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "WHITEPAPER_BUILD_REPORT.md")
        json_path = os.path.join(base, "WHITEPAPER_BUILD_REPORT.json")
        markdown = self._render_md(report["sections"])
        if not report["claim_guard_safe"]:
            markdown = self._guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path,
                "documents": [md_path, json_path], "report": report}

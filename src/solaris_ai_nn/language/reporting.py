"""Session/experiment reports -- dict, JSON, and Markdown. Nothing fancier.

`ExperimentReportBuilder` assembles the standard sections (metadata, runtime,
signals, substrate, actions, reactions, habits, synthesis, plasticity, memory,
Inner MAP, embodiment, integration, safety) plus the mandatory
limitations/unknowns section, and renders deterministically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schemas import ExperimentReport
from .summarizer import STANDARD_LIMITATIONS

SECTION_ORDER = [
    "metadata", "runtime", "signals", "substrate", "actions", "reactions",
    "habits", "synthesis", "plasticity", "memory", "inner_map", "embodiment",
    "integration", "safety", "explanations",
]


@dataclass
class SessionReport:
    """A finished report: structured data + renderers."""

    report: ExperimentReport

    def to_dict(self) -> Dict[str, Any]:
        return self.report.to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        r = self.report
        lines = [f"# {r.title}", ""]
        meta = r.metadata
        if meta:
            lines.append("## Metadata")
            for key, value in meta.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        for name in SECTION_ORDER:
            if name == "metadata" or name not in r.sections:
                continue
            section = r.sections[name]
            lines.append(f"## {name.replace('_', ' ').title()}")
            lines.extend(_render_value(section))
            lines.append("")
        # Remaining sections not in the canonical order.
        for name, section in r.sections.items():
            if name in SECTION_ORDER:
                continue
            lines.append(f"## {name.replace('_', ' ').title()}")
            lines.extend(_render_value(section))
            lines.append("")
        lines.append("## Limitations and Unknowns")
        for item in r.limitations:
            lines.append(f"- {item}")
        lines.append("")
        return "\n".join(lines)


def _render_value(value: Any, indent: int = 0) -> List[str]:
    pad = "  " * indent
    if isinstance(value, dict):
        out: List[str] = []
        for key, sub in value.items():
            if isinstance(sub, (dict, list)):
                out.append(f"{pad}- **{key}**:")
                out.extend(_render_value(sub, indent + 1))
            else:
                out.append(f"{pad}- **{key}**: {sub}")
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, (dict, list)):
                out.extend(_render_value(item, indent))
            else:
                out.append(f"{pad}- {item}")
        return out
    return [f"{pad}{value}"]


@dataclass
class ExperimentReportBuilder:
    """Accumulates sections, then builds a SessionReport."""

    title: str = "Solaris-AI-NN session report"
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, Any] = field(default_factory=dict)
    extra_limitations: List[str] = field(default_factory=list)

    def add_metadata(self, **fields: Any) -> "ExperimentReportBuilder":
        self.metadata.update(fields)
        return self

    def add_section(self, name: str, data: Any) -> "ExperimentReportBuilder":
        if data is not None:
            self.sections[name] = data
        return self

    def add_limitation(self, text: str) -> "ExperimentReportBuilder":
        self.extra_limitations.append(text)
        return self

    def build(self) -> SessionReport:
        report = ExperimentReport(
            title=self.title,
            metadata=dict(self.metadata),
            sections=dict(self.sections),
            limitations=STANDARD_LIMITATIONS + list(self.extra_limitations),
        )
        return SessionReport(report=report)

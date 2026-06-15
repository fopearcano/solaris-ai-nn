"""Self-boundary report -- the operational self/world boundary made visible.

:class:`SelfBoundaryReportBuilder` compiles the boundary state, ownership
attribution, perspective frame, body schema, continuity anchors/breaks, source
attribution, simulation-boundary status, identity trace, and boundary tensions. It
states explicitly that self-boundary is operational (not subjective selfhood), that
the body schema is receptor/sensorium structure (not a biological body), and that
identity trace is continuity metadata (not personhood). The Markdown is scanned by
ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DOES_NOT_PROVE = (
    "Self-boundary is operational, not subjective selfhood.",
    "Body schema is receptor/sensorium structure, not a biological body.",
    "Identity trace is continuity metadata, not personhood.",
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life.",
    "This does not prove subjective experience.",
)

_LIMITATIONS = (
    "Boundary assignments are operational and may be uncertain.",
    "Processed sensory data is not collapsed into 'internal self'.",
    "Simulations/counterfactuals/debug never become observation or evidence.",
    "Continuity is trace continuity, not biological life; breaks are retained.",
    "Operator annotation and human gloss are never ground truth.",
)


@dataclass
class SelfBoundaryReportBuilder:
    """Builds the self-boundary report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.self_boundary_status()
        sections: Dict[str, Any] = {
            "purpose": ("track the operational boundary between internal state, "
                        "receptor body, external flux/feeders/sources, memory, "
                        "prediction, and simulation -- not a subjective self"),
            "boundary_state": rt.boundary.to_dict(),
            "ownership_attribution_summary": rt.ownership.to_dict(),
            "perspective_frame": rt.perspective.to_dict(),
            "sensorium_body_schema": rt.body_schema.to_dict(),
            "continuity": rt.continuity.to_dict(),
            "continuity_breaks": [b.to_dict() for b in rt.continuity.breaks],
            "source_attribution": rt.source_attribution.to_dict(),
            "internal_external_classification": rt.classifier.to_dict(),
            "simulation_boundary_status": rt.sim_boundary.to_dict(),
            "identity_trace": rt.identity.snapshot(),
            "boundary_tensions": rt.tension_detector.to_dict(),
            "unresolved_unknown_origins": [
                t.to_dict() for t in rt.tension_detector.tensions
                if t.tension_type == "unknown_origin"],
            "milestones": list(rt.milestones),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_prove": list(_DOES_NOT_PROVE),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Self-Boundary Report", "",
            "_How Solaris tracks the operational boundary between its internal "
            "state, its receptor body, and the external world that touches it. "
            "Self-boundary is operational, NOT subjective selfhood; the body "
            "schema is receptor/sensorium structure, NOT a biological body; the "
            "identity trace is continuity metadata, NOT personhood._", "",
            f"- boundary events: {status['boundary_event_count']} "
            f"(confidence {status['boundary_confidence_score']})",
            f"- ownership attributions: "
            f"{status['ownership_attribution_count']} "
            f"(ambiguous {status['ambiguous_ownership_count']})",
            f"- receptor body parts: {status['receptor_body_schema_count']} "
            f"(stability {status['body_schema_stability']})",
            f"- perspective shifts: {status['perspective_shift_count']}",
            f"- continuity anchors: {status['continuity_anchor_count']} "
            f"(breaks {status['continuity_break_count']})",
            f"- simulation boundary warnings: "
            f"{status['simulation_boundary_warning_count']} "
            f"(integrity {status['simulation_boundary_integrity']})",
            f"- source attribution uncertainty: "
            f"{status['source_attribution_uncertainty_score']}",
            f"- boundary tensions: {status['boundary_tension_count']}",
            f"- identity trace events: {status['identity_trace_event_count']}",
            "",
            "## Continuity breaks (retained)", "",
            f"- retained: {len(sections['continuity_breaks'])} "
            "(breaks are logged and kept even after recovery)",
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
        md_path = os.path.join(base, "SELF_BOUNDARY_REPORT.md")
        json_path = os.path.join(base, "SELF_BOUNDARY_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

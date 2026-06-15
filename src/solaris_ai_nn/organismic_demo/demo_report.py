"""Minimal field organism demo report -- what changed, and what it does not prove.

:class:`MinimalFieldOrganismDemoReportBuilder` compiles the demo's sensorium
configuration, feeders, receptors, field evolution, detected structure, the
changed-perception probe, the baseline comparison, negative results, and the
safety status into a Markdown + JSON report. It states explicitly that the demo
does not prove consciousness, sentience, life, or understanding -- only whether
continuous sensorium exposure changed internal response structure. The Markdown
is scanned by ClaimGuard before it is written.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DOES_NOT_PROVE = (
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life.",
    "This does not prove understanding.",
    "It only tests whether continuous sensorium exposure changes internal "
    "response structure.",
)

_LIMITATIONS = (
    "Fixtures are a controlled rehearsal, not real-world feeder data.",
    "Patterns observed in fixtures may not generalise to real read-only streams.",
    "Human labels are kept as non-ground-truth and never drive grounding.",
    "No hardware is accessed; the debug-truth file is excluded from perception.",
)


@dataclass
class MinimalFieldOrganismDemoReportBuilder:
    """Builds the demo report from a completed runner."""

    runner: Any
    comparison: Any = None

    def build(self) -> Dict[str, Any]:
        runner = self.runner
        rt = runner.runtime
        probe = runner.probe_result
        status = runner.demo_status()
        sections: Dict[str, Any] = {
            "demo_purpose": (
                "the first observable organismic-perception demo: what does "
                "Solaris do when continuously exposed to a peculiar sensorium?"),
            "sensorium_configuration": {
                "ticks": runner.config.ticks,
                "max_events_total": runner.config.max_events_total,
                "fixture_mode": runner.config.fixture_mode,
                "enabled_modalities": rt.active_modalities() if rt else []},
            "feeder_streams": [f.to_dict() for f in (rt.feeders if rt else [])],
            "receptor_summary": [r.to_dict()
                                 for r in (rt.receptors.values() if rt else [])],
            "sensory_field_evolution": rt.sensory_field.to_dict() if rt else {},
            "baseline_shifts": list(rt.baseline_shifts) if rt else [],
            "absence_events": [e.to_dict()
                               for e in (rt.absence.events if rt else [])],
            "rhythm_signatures": [s.to_dict() for s in (
                rt.rhythm.signatures.values() if rt else [])],
            "invariant_candidates": [c.to_dict() for c in (
                rt.invariants.candidates.values() if rt else [])],
            "cross_modal_relations": [r.to_dict() for r in (
                rt.cross_modal.all_relations() if rt else [])],
            "attention_shifts": [s.to_dict()
                                 for s in (rt.attention.history if rt else [])],
            "proto_symbol_candidates": list(
                rt.proto_symbol_candidates) if rt else [],
            "world_model_changes": (rt.world_model_structures[:100]
                                    if rt else []),
            "hypotheses_seeded": list(rt.hypotheses) if rt else [],
            "logos_tensions": list(rt.logos_tensions) if rt else [],
            "changed_perception_probe": (probe.to_dict() if probe else None),
            "comparison": (self.comparison.to_dict() if self.comparison
                           else None),
            "negative_results": self._negatives(runner, probe),
            "human_label_contamination": (
                rt.human_label_contamination_score() if rt else 0.0),
            "safety_status": runner.safety.snapshot(),
            "trace_summary": runner.trace.counts_by_type(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_demo_proves": (
                "that continuous exposure through a peculiar sensorium can "
                "change Solaris's internal response structure (receptors, "
                "baselines, attention, invariants, proto-symbols)"),
            "what_this_demo_does_not_prove": list(_DOES_NOT_PROVE),
            "next_recommended_real_environment_feeder_test": (
                "replay a real read-only RF/echo/vibration feeder (governance "
                "approved) and re-run the changed-perception probe"),
        }
        markdown = self._render_markdown(sections)
        claim_guard_safe = self._claim_guard_safe(markdown)
        return {"sections": sections, "claim_guard_safe": claim_guard_safe}

    def _negatives(self, runner: Any, probe: Any) -> Dict[str, Any]:
        negatives = []
        if probe is not None and not probe.changed:
            negatives.append("changed-perception probe detected no change")
        if self.comparison is not None and self.comparison.negative_result:
            negatives.append("full sensorium did not beat the passive parser")
        return {"count": len(negatives), "items": negatives}

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        probe = sections.get("changed_perception_probe") or {}
        lines = [
            "# Minimal Field Organism Demo Report", "",
            "_The first observable organismic-perception demo. Solaris is "
            "exposed to continuous environmental flux through external read-only "
            "feeders and its internal response structure is measured before and "
            "after. This is operational perception only._", "",
            f"- ticks: {sections['sensorium_configuration']['ticks']}",
            f"- enabled modalities: "
            f"{sections['sensorium_configuration']['enabled_modalities']}",
            f"- active receptors: {len(sections['receptor_summary'])}",
            f"- baseline shifts: {len(sections['baseline_shifts'])}",
            f"- absence events: {len(sections['absence_events'])}",
            f"- rhythm signatures: {len(sections['rhythm_signatures'])}",
            f"- invariant candidates: {len(sections['invariant_candidates'])}",
            f"- cross-modal relations: "
            f"{len(sections['cross_modal_relations'])}",
            f"- proto-symbol candidates: "
            f"{len(sections['proto_symbol_candidates'])}",
            f"- changed-perception score: "
            f"{probe.get('changed_perception_score', 0.0)}",
            f"- changed: {probe.get('changed', False)}",
            f"- human-label contamination: "
            f"{sections['human_label_contamination']}",
            f"- negative results: {sections['negative_results']['count']}",
            "",
            "## What this demo proves", "",
            f"- {sections['what_this_demo_proves']}",
            "",
            "## What this demo does NOT prove", "",
        ]
        lines += [f"- {item}" for item in
                  sections["what_this_demo_does_not_prove"]]
        lines += ["", "## Negative results", ""]
        lines += ([f"- {n}" for n in sections["negative_results"]["items"]]
                  or ["- (none)"])
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Next recommended real-environment feeder test", "",
                  f"- {sections['next_recommended_real_environment_feeder_test']}"]
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
        base = state_dir or self.runner.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "MINIMAL_FIELD_ORGANISM_REPORT.md")
        json_path = os.path.join(base, "MINIMAL_FIELD_ORGANISM_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

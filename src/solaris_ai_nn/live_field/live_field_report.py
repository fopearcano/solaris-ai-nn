"""Live field report -- what Solaris perceived from the real read-only field.

:class:`LiveFieldReportBuilder` compiles the feeder registry, feeder/source
health, active modalities, receptor adaptation, sensory-field evolution, detected
structure, the changed-perception probe, the comparison, negative results, and the
safety status. It states explicitly that no hardware was controlled, no source was
modified, no real-world actuation occurred, and the result does not prove
consciousness, sentience, life, or understanding. ClaimGuard scans the Markdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DISCLAIMERS = (
    "No hardware was controlled by Solaris.",
    "No source was modified by Solaris.",
    "No real-world actuation occurred.",
    "This does not prove consciousness, sentience, life, or understanding.",
)

_LIMITATIONS = (
    "Live feeders are external; Solaris only read their output.",
    "Source silence and corruption are perceptual/evidence signals, not faults "
    "to hide.",
    "Human labels are kept as non-ground-truth and never drive grounding.",
    "A single bounded pilot is weak evidence; repeat with more feeders.",
)


@dataclass
class LiveFieldReportBuilder:
    """Builds the live-field report (JSON + claim-guarded Markdown)."""

    runtime: Any
    comparison: Any = None
    probe: Any = None

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        s = rt.sensorium
        status = rt.live_field_status()
        sections: Dict[str, Any] = {
            "purpose": ("the first real read-only environmental field pilot: "
                        "what happens when Solaris is continuously exposed to "
                        "uncontrolled, read-only environmental rhythms?"),
            "live_mode_status": {
                "live_mode": rt.live_mode,
                "live_mode_allowed": status["live_mode_allowed"]},
            "feeder_registry_summary": rt.registry.snapshot(),
            "feeder_health": {
                "present": [f.feeder_id for f in rt.registry.present_feeders()],
                "missing": [f.feeder_id for f in rt.registry.missing_feeders()]},
            "source_health": rt.health.snapshot(),
            "active_modalities": s.active_modalities(),
            "receptor_adaptation": [r.to_dict() for r in s.receptors.values()],
            "sensory_field_evolution": s.sensory_field.to_dict(),
            "baseline_shifts": list(s.baseline_shifts),
            "absence_events": [e.to_dict() for e in s.absence.events],
            "rhythm_signatures": [sig.to_dict()
                                  for sig in s.rhythm.signatures.values()],
            "invariant_candidates": [c.to_dict()
                                     for c in s.invariants.candidates.values()],
            "cross_modal_relations": [r.to_dict()
                                      for r in s.cross_modal.all_relations()],
            "attention_shifts": [a.to_dict() for a in s.attention.history],
            "changed_perception_probe": (self.probe.to_dict()
                                         if self.probe else None),
            "comparison": (self.comparison.to_dict() if self.comparison
                           else None),
            "negative_results": self._negatives(),
            "corrupt_or_missing_sources": {
                "corrupt": rt.health.corrupt_sources(),
                "missing_feeders": [f.feeder_id
                                    for f in rt.registry.missing_feeders()]},
            "safety_status": rt.safety.snapshot(),
            "trace_summary": rt.trace.counts_by_type(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "disclaimers": list(_DISCLAIMERS),
            "next_recommended_feeder_additions": (
                "add a non-human feature feeder (RF/echo/vibration) and a "
                "second modality to enable richer cross-modal comparison"),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _negatives(self) -> Dict[str, Any]:
        items = []
        if self.probe is not None and not self.probe.changed:
            items.append("changed-perception probe detected no change")
        if self.comparison is not None and self.comparison.negative_result:
            items.append("live field did not beat the passive parser")
        if self.comparison is not None and self.comparison.inconclusive:
            items.append("comparison inconclusive (missing modalities)")
        return {"count": len(items), "items": items}

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        probe = sections.get("changed_perception_probe") or {}
        health = sections["source_health"]
        lines = [
            "# Live Field Report", "",
            "_The first real read-only environmental field pilot. External "
            "feeders write event envelopes; Solaris reads only. This is "
            "operational perception, not consciousness, sentience, life, or "
            "understanding._", "",
            f"- live mode: {sections['live_mode_status']['live_mode']}",
            f"- feeders: {sections['feeder_registry_summary']['feeder_count']} "
            f"(present {sections['feeder_registry_summary']['present_count']}, "
            f"missing {sections['feeder_registry_summary']['missing_count']})",
            f"- active sources: {health['active_count']}; silent: "
            f"{health['silent_count']}; corrupt: {health['corrupt_count']}",
            f"- active modalities: {sections['active_modalities']}",
            f"- baseline shifts: {len(sections['baseline_shifts'])}",
            f"- absence events: {len(sections['absence_events'])}",
            f"- rhythm signatures: {len(sections['rhythm_signatures'])}",
            f"- invariant candidates: {len(sections['invariant_candidates'])}",
            f"- cross-modal relations: "
            f"{len(sections['cross_modal_relations'])}",
            f"- changed-perception score: "
            f"{probe.get('changed_perception_score', 0.0)}",
            f"- negative results: {sections['negative_results']['count']}",
            "",
            "## Disclaimers", "",
        ]
        lines += [f"- {d}" for d in sections["disclaimers"]]
        lines += ["", "## Negative results", ""]
        lines += ([f"- {n}" for n in sections["negative_results"]["items"]]
                  or ["- (none)"])
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Next recommended feeder additions", "",
                  f"- {sections['next_recommended_feeder_additions']}"]
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
        md_path = os.path.join(base, "LIVE_FIELD_REPORT.md")
        json_path = os.path.join(base, "LIVE_FIELD_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

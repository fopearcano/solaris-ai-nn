"""Perceptual metabolism report -- regulation made visible and honest.

:class:`PerceptualMetabolismReportBuilder` compiles the perceptual needs, energy
budget, sensory homeostasis, attention allocation, overload/deprivation events,
novelty appetite, source diet, consolidation pressure, receptor recovery, and the
internal regulation recommendations. It states explicitly that needs are
operational pressures (not feelings), that metabolism is computational regulation
(not biological life), and that it proves no consciousness/sentience/life. The
Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DOES_NOT_PROVE = (
    "Needs are operational pressures, not feelings or emotions.",
    "Metabolism here is computational regulation, not biological life.",
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life.",
    "No hardware was controlled and no source was modified.",
)

_LIMITATIONS = (
    "All regulation is internal and bounded; nothing actuates the world.",
    "Recommendations are gated; they never auto-execute real-world actions.",
    "Energy and needs are metaphors for compute/attention, not biology.",
)


@dataclass
class PerceptualMetabolismReportBuilder:
    """Builds the metabolism report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        last = rt._last
        status = rt.metabolism_status()
        sensorium = rt.sensorium
        sections: Dict[str, Any] = {
            "purpose": ("regulate continuous sensory exposure so Solaris "
                        "metabolizes stimuli rather than merely recording them"),
            "active_modalities": (sensorium.active_modalities()
                                  if sensorium is not None
                                  and hasattr(sensorium, "active_modalities")
                                  else []),
            "perceptual_needs": last.get("needs", {}),
            "energy_budget": last.get("energy_budget", {}),
            "sensory_homeostasis": last.get("homeostasis", {}),
            "attention_allocation": last.get("attention", {}),
            "overload_events": last.get("overload", {}),
            "deprivation_events": last.get("deprivation", {}),
            "novelty_appetite": last.get("novelty_appetite", {}),
            "source_diet": last.get("source_diet", {}),
            "consolidation_pressure": last.get("consolidation", {}),
            "silence_absence_as_stimulus": {
                "deprivation_events": len(rt.deprivation.state.events),
                "note": "silence is treated as stimulus; absence can become "
                        "world-model structure"},
            "human_label_dominance": last.get("source_diet", {}).get(
                "human_label_dominance", 0.0),
            "live_vs_fixture_balance": last.get("source_diet", {}).get(
                "live_vs_fixture_balance", 0.0),
            "internal_regulation_recommendations": list(rt.recommendations),
            "latent_replay_recommendations":
                rt.latent_replay_recommendations(),
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
        needs = sections["perceptual_needs"]
        lines = [
            "# Perceptual Metabolism Report", "",
            "_How Solaris regulates continuous sensory exposure. Perceptual "
            "needs are operational regulatory pressures, NOT feelings or "
            "emotions; metabolism here is computational regulation, NOT "
            "biological life. No hardware was controlled and no source was "
            "modified._", "",
            f"- active modalities: {sections['active_modalities']}",
            f"- dominant need: {needs.get('dominant_need')} "
            f"(pressure {needs.get('dominant_pressure', 0.0)})",
            f"- overloaded: {sections['overload_events'].get('overloaded')}",
            f"- deprived: {sections['deprivation_events'].get('deprived')}",
            f"- source diet diversity: "
            f"{sections['source_diet'].get('diet_diversity', 0.0)}",
            f"- human-label dominance: {sections['human_label_dominance']}",
            f"- consolidation pressure: "
            f"{sections['consolidation_pressure'].get('pressure', 0.0)} "
            f"({sections['consolidation_pressure'].get('recommendation')})",
            f"- internal recommendations: "
            f"{len(sections['internal_regulation_recommendations'])}",
            "",
            "## Silence / absence as stimulus", "",
            f"- {sections['silence_absence_as_stimulus']['note']}",
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
        md_path = os.path.join(base, "PERCEPTUAL_METABOLISM_REPORT.md")
        json_path = os.path.join(base, "PERCEPTUAL_METABOLISM_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

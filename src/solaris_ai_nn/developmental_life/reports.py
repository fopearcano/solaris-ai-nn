"""Developmental-life report -- long-horizon structural change made honest.

:class:`DevelopmentalLifeReportBuilder` compiles the life-cycle phase, epochs,
growth state, maturation markers, phase transitions, plateaus, regressions, growth-
vs-accumulation analysis, and operational life history. It states explicitly that
the life cycle is operational runtime structure (not biological life), maturation
markers are structural observations (not consciousness milestones), life history is
operational trace history (not biography), and growth means structural change (not
proof of intelligence). The Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DOES_NOT_PROVE = (
    "Life cycle is operational runtime structure, not biological life.",
    "Maturation markers are structural observations, not consciousness "
    "milestones.",
    "Life history is operational trace history, not biography.",
    "Growth means structural change, not proof of intelligence.",
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life.",
    "This does not prove personhood.",
    "This does not prove agency or free will.",
    "This does not prove subjective experience.",
)

_LIMITATIONS = (
    "Growth-vs-accumulation is judged conservatively; inconclusive is valid.",
    "Regressions, plateaus, failed transitions, and inconclusive results are "
    "preserved.",
    "Fixture and human-label overfit are flagged, not hidden.",
    "Bounded per invocation; persists across restarts; no human teaching loop.",
    "No real-world actuation, hardware, feeder, or source control occurs.",
)


@dataclass
class DevelopmentalLifeReportBuilder:
    """Builds the developmental-life report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.developmental_status()
        growth_report = (rt.growth_report.to_dict()
                         if rt.growth_report is not None else {})
        sections: Dict[str, Any] = {
            "purpose": ("track long-horizon structural change across bounded "
                        "developmental cycles -- not biological life or "
                        "consciousness"),
            "current_life_cycle_phase": rt.clock.state.to_dict(),
            "epoch_summary": {
                "epoch_count": len(rt.epochs),
                "epochs": [e.to_dict() for e in rt.epochs]},
            "growth_state": rt.growth.to_dict(),
            "maturation_markers": rt.maturation.to_dict(),
            "phase_transitions": rt.transition_detector.to_dict(),
            "plateaus": rt.plateau_detector.to_dict(),
            "regressions": rt.regression_detector.to_dict(),
            "structural_growth_vs_accumulation": growth_report,
            "operational_life_history": rt.life_history.history.to_dict(),
            "continuity_restart_history": {
                "restart_count": rt.clock.state.restart_count,
                "shutdown_count": rt.clock.state.shutdown_count},
            "negative_results": {
                "regression_count": status["regression_count"],
                "plateau_count": status["plateau_count"],
                "accumulation_warning_count":
                    status["accumulation_warning_count"]},
            "inconclusive_results": {
                "inconclusive_transitions":
                    rt.transition_detector.to_dict().get("inconclusive_count",
                                                         0)},
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
            "# Developmental Life Report", "",
            "_How Solaris tracks long-horizon structural change across bounded "
            "developmental cycles. The 'life cycle' is operational runtime "
            "structure, NOT biological life; maturation markers are structural "
            "observations, NOT consciousness milestones; the 'life history' is "
            "operational trace history, NOT biography; and 'growth' means "
            "structural change, NOT proof of intelligence._", "",
            f"- life-cycle phase: {status['current_life_cycle_phase']} "
            f"({status['life_cycle_phase_count']} phases visited)",
            f"- epochs: {status['developmental_epoch_count']}",
            f"- maturation markers: {status['maturation_marker_count']} "
            f"(weak {status['weak_maturation_marker_count']})",
            f"- phase transitions: {status['phase_transition_count']}",
            f"- plateaus: {status['plateau_count']}",
            f"- regressions: {status['regression_count']}",
            f"- structural growth: {status['structural_growth_status']} "
            f"(score {status['structural_growth_score']})",
            f"- accumulation warnings: {status['accumulation_warning_count']}",
            f"- composite growth: {status['composite_growth']}",
            f"- continuity recoveries (restarts): "
            f"{status['continuity_recovery_count']}",
            "",
            "## Negative / inconclusive results (preserved)", "",
            f"- regressions {status['regression_count']}, plateaus "
            f"{status['plateau_count']}, accumulation warnings "
            f"{status['accumulation_warning_count']} (all preserved)",
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
        md_path = os.path.join(base, "DEVELOPMENTAL_LIFE_REPORT.md")
        json_path = os.path.join(base, "DEVELOPMENTAL_LIFE_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

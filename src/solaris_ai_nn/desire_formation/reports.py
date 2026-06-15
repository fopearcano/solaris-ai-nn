"""Desire-formation report -- operational desire made visible and honest.

:class:`DesireFormationReportBuilder` compiles valence gradients, pushes, desire
candidates, the motivation field, conflicts, readiness gates, arbitration decisions,
selected internal actions, inhibited/deferred/failed desires, safety/governance
blocks, outcome traces, and no-op decisions. It states explicitly that desire is
operational pressure toward internal action readiness, valence is operational
priority (not feeling), internal actions do not affect the external world, and it
proves no emotion/will/agency/consciousness. The Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .desire import DesireStatus

_DOES_NOT_PROVE = (
    "Desire is operational pressure toward internal action readiness.",
    "Valence is operational priority, not feeling.",
    "Internal actions do not affect the external world.",
    "This does not prove emotion.",
    "This does not prove will.",
    "This does not prove agency.",
    "This does not prove consciousness, sentience, life, or subjective "
    "experience.",
)

_LIMITATIONS = (
    "Desire candidates lead only to internal actions or safe simulations.",
    "Safety and governance can veto any desire; failures/blocks are evidence.",
    "No-op is a valid outcome (organismic inhibition), preserved as a trace.",
    "Desire cannot command hardware/feeders or modify source files.",
    "Valence and motivation are operational dynamics, not human wanting.",
)


@dataclass
class DesireFormationReportBuilder:
    """Builds the desire-formation report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def _by_status(self, *statuses: str):
        return [d.to_dict() for d in self.runtime.desires
                if d.status in statuses]

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.desire_status()
        sections: Dict[str, Any] = {
            "purpose": ("transform sensorium/metabolism/cognition/boundary "
                        "pressures into operational valence, pushes, desire "
                        "candidates, and safe internal-action readiness"),
            "valence_gradients": rt.valence_assessor.gradient.to_dict(),
            "pushes": rt.push_engine.to_dict(),
            "desire_candidates": [d.to_dict() for d in rt.desires],
            "motivation_field": rt.motivation.state.to_dict(),
            "conflicts": rt.conflict_detector.to_dict(),
            "readiness_gates": {
                "min_confidence": rt.readiness_gate.min_confidence},
            "arbitration_decisions": rt.arbitrator.to_dict(),
            "selected_internal_actions": rt.executor.to_dict(),
            "inhibited_desires": self._by_status(DesireStatus.INHIBITED),
            "deferred_desires": self._by_status(DesireStatus.DEFERRED),
            "failed_desires": self._by_status(DesireStatus.FAILED),
            "safety_governance_blocks": self._by_status(
                DesireStatus.BLOCKED_BY_SAFETY),
            "outcome_traces": rt.outcomes.to_dict(),
            "no_op_decisions": {
                "no_op_count": rt.executor.no_op_count,
                "operator_review_items": rt.executor.operator_review_items},
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
        status = sections["status"]
        lines = [
            "# Desire Formation Report", "",
            "_How Solaris transforms sensorium, metabolism, cognition, and "
            "self-boundary pressures into operational valence, pushes, and "
            "desire candidates that lead only to safe internal actions. Desire "
            "is operational pressure toward internal action readiness, NOT "
            "emotion, human wanting, conscious intention, or free will; valence "
            "is operational priority, NOT feeling; internal actions do not "
            "affect the external world._", "",
            f"- valence gradients: {status['valence_gradient_count']} "
            f"(dominant {status['dominant_valence_direction']})",
            f"- pushes: {status['push_count']}",
            f"- desire candidates: {status['desire_candidate_count']} "
            f"(active {status['active_desire_count']}, inhibited "
            f"{status['inhibited_desire_count']}, deferred "
            f"{status['deferred_desire_count']})",
            f"- internal actions: {status['internal_action_count']} "
            f"(no-op {status['no_op_count']})",
            f"- conflicts: {status['desire_conflict_count']}",
            f"- safety-blocked desires: {status['safety_blocked_desire_count']}",
            f"- governance-blocked desires: "
            f"{status['governance_blocked_desire_count']}",
            f"- outcome success rate: {status['desire_outcome_success_rate']}",
            "",
            "## No-op decisions (valid; preserved)", "",
            f"- no-op count: {status['no_op_count']} (no-op is a valid "
            "organismic inhibition outcome, preserved as a trace)",
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
        md_path = os.path.join(base, "DESIRE_FORMATION_REPORT.md")
        json_path = os.path.join(base, "DESIRE_FORMATION_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

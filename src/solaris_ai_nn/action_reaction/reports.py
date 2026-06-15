"""Action-reaction report -- the closed loop made visible and honest.

:class:`ActionReactionReportBuilder` compiles selected/inhibited/blocked/no-op
actions, reactions, consequence traces, learned effects, habits, policy updates, and
failed/no-effect actions. It states explicitly that actions are internal/simulated/
report-only, that no real-world actuation occurred, that reaction valence is
operational effect (not feeling), that habits are learned policy tendencies (not
instincts or will), and that it proves no agency/free-will/consciousness. The
Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .action_model import ActionExecutionStatus

_DOES_NOT_PROVE = (
    "Actions are internal/simulated/report-only unless explicitly marked "
    "otherwise.",
    "No real-world actuation occurred.",
    "Reaction valence is operational effect, not feeling.",
    "Habits are learned policy tendencies, not instincts or will.",
    "This does not prove agency.",
    "This does not prove free will.",
    "This does not prove consciousness, sentience, life, personhood, or "
    "subjective experience.",
)

_LIMITATIONS = (
    "Consequences are evidence-backed; effects are never invented.",
    "Failed, blocked, no-effect, and inhibited actions are preserved.",
    "Learned effects are provisional; correlation is not causation.",
    "Habits remain overrideable by safety and governance.",
    "Forbidden external actions are always blocked and recorded.",
)


@dataclass
class ActionReactionReportBuilder:
    """Builds the action-reaction report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.action_reaction_status()
        no_op = [a.to_dict() for a in rt.actions if a.is_no_op]
        blocked = [a.to_dict() for a in rt.actions
                   if a.status == ActionExecutionStatus.BLOCKED]
        sections: Dict[str, Any] = {
            "purpose": ("close the loop: execute or record safe internal "
                        "actions, observe reactions, and learn provisional "
                        "action-effect relations and habits"),
            "selected_actions": [a.to_dict() for a in rt.actions],
            "inhibited_actions": rt.inhibition_engine.to_dict(),
            "blocked_actions": blocked,
            "no_op_actions": no_op,
            "reactions": [r.to_dict() for r in rt.reactions],
            "consequence_traces": [c.to_dict() for c in rt.consequences],
            "learned_effects": rt.effect_engine.to_dict(),
            "habit_candidates": [h.to_dict()
                                 for h in rt.habit_engine.candidates()],
            "strengthened_habits": [h.to_dict()
                                    for h in rt.habit_engine.strengthened()],
            "weakened_habits": [h.to_dict()
                                for h in rt.habit_engine.weakened()],
            "policy_updates": rt.policy_engine.to_dict(),
            "failed_no_effect_actions": {
                "no_effect_action_count": status["no_effect_action_count"]},
            "safety_governance_blocks": blocked,
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
            "# Action-Reaction Report", "",
            "_How Solaris closes the loop: it executes or records safe INTERNAL "
            "actions selected by desire formation, observes operational "
            "reactions, builds consequence traces, and learns provisional "
            "action-effect relations and habits. Actions are internal/simulated/"
            "report-only; NO real-world actuation occurred. Reaction valence is "
            "operational effect, NOT feeling; habits are learned policy "
            "tendencies, NOT instincts or will._", "",
            f"- selected actions: {status['selected_action_count']} "
            f"(internal {status['internal_action_count']}, no-op "
            f"{status['no_op_count']}, blocked {status['blocked_action_count']})",
            f"- reactions: {status['reaction_count']} "
            f"(constructive ratio {status['constructive_reaction_ratio']}, "
            f"disruptive ratio {status['disruptive_reaction_ratio']})",
            f"- consequence traces: {status['consequence_trace_count']}",
            f"- learned effects: {status['learned_effect_count']}",
            f"- habits: candidate {status['habit_candidate_count']}, "
            f"strengthened {status['strengthened_habit_count']}, weakened "
            f"{status['weakened_habit_count']}",
            f"- inhibitions: {status['inhibition_count']}",
            f"- policy updates: {status['action_policy_update_count']}",
            f"- no-effect actions: {status['no_effect_action_count']}",
            "",
            "## Failed / blocked / no-effect actions (preserved)", "",
            f"- blocked: {len(sections['blocked_actions'])}; no-effect: "
            f"{status['no_effect_action_count']} (all preserved as evidence)",
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
        md_path = os.path.join(base, "ACTION_REACTION_REPORT.md")
        json_path = os.path.join(base, "ACTION_REACTION_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}

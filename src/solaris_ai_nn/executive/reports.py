"""Executive reports and queries -- careful words for arbitration numbers.

The report covers mode, focus, queue, candidates, inhibitions, the full
score table, the selection, plans, prospection, and safety decisions, with
mandatory limitations. Queries answer in safe vocabulary: "the arbitrator
selected…", "the candidate was inhibited because…" -- never "the system
decided freely". ClaimGuard re-scans at save time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

from ..language.query import normalize
from ..language.reporting import ExperimentReportBuilder, SessionReport
from ..language.schemas import QueryResult

EXECUTIVE_LIMITATIONS = [
    "The executive layer ranks and suggests; it never executes real-world "
    "actions and never commits Solaris Actions.",
    "Arbitration scores are deterministic functions of recorded pressure, "
    "evidence, and penalties -- not decisions made freely.",
    "Prospection results are bounded simulated estimates with confidence, "
    "never facts about what will happen.",
    "Plans are short, suggestion-only sequences; long-horizon autonomous "
    "planning is structurally refused.",
    "No claim of intention, agency, will, or consciousness is made or "
    "supported.",
]


class ExecutiveReportBuilder:
    """Builds the report from an ExecutiveLayer."""

    def __init__(self, layer: Any) -> None:
        self.layer = layer

    def build(self) -> SessionReport:
        layer = self.layer
        snap = layer.snapshot()
        result = layer.last_result
        report = (
            ExperimentReportBuilder(title="Executive report")
            .add_metadata(mode=snap["summary"]["mode"],
                          decisions=snap["summary"]["decisions"],
                          selected=snap["summary"][
                              "selected_action_suggestion"])
            .add_section("executive_mode", snap["policy"])
            .add_section("active_focus", snap["attention"]["recent_focus"]
                         [-1:] or ["no focus selected yet"])
            .add_section("desire_queue", snap["queue"])
            .add_section("action_candidates",
                         [s.to_dict() for s in (result.scores
                                                if result else [])]
                         or ["no arbitration has run"])
            .add_section("inhibited_candidates",
                         snap["inhibition"]["recent"]
                         or ["nothing inhibited"])
            .add_section("arbitration",
                         {"reason": result.reason,
                          "fallback_used": result.fallback_used}
                         if result else None)
            .add_section("selected_action_suggestion",
                         (result.selected.to_dict()
                          if result and result.selected else
                          {"none": "no decision yet"}))
            .add_section("current_plan",
                         (layer.last_plan.to_dict()
                          if layer.last_plan else None))
            .add_section("prospection_summary", snap["prospection"])
            .add_section("safety_governance_decisions", snap["safety"])
            .add_section("decision_trace_summary", snap["decision_trace"])
        )
        for limitation in EXECUTIVE_LIMITATIONS:
            report.add_limitation(limitation)
        return report.build()

    def to_dict(self) -> Dict[str, Any]:
        return self.build().to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        return self.build().to_markdown()

    def save(self, json_path: Union[str, Path],
             md_path: Union[str, Path]) -> Dict[str, Any]:
        """Persist via the language layer (ClaimGuard scans the Markdown)."""
        from ..language.serialization import save_report

        scan = save_report(self.build(), json_path, md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}


class ExecutiveQueryInterface:
    """Seven fixed queries answered in safe vocabulary."""

    def __init__(self, layer: Any) -> None:
        self.layer = layer
        self._handlers: Dict[str, Callable[[], "tuple[str, float]"]] = {
            "why was this action selected": self._why_selected,
            "what candidates were rejected": self._rejected,
            "what was inhibited": self._inhibited,
            "what is the current plan": self._plan,
            "why no action": self._why_no_action,
            "what is the executive focus": self._focus,
            "what score won arbitration": self._winning_score,
        }

    def supported_queries(self) -> List[str]:
        return sorted(self._handlers)

    def answer(self, query: str) -> QueryResult:
        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence = handler()
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, confidence=confidence)

    # -- handlers ---------------------------------------------------------------

    def _why_selected(self) -> "tuple[str, float]":
        result = self.layer.last_result
        if result is None or result.selected is None:
            return ("No arbitration has produced a selection yet.", 0.3)
        return (f"The arbitrator selected {result.selected.label!r} "
                f"because: {result.reason}. The selection is a suggestion "
                "with no execution authority of its own.", 0.9)

    def _rejected(self) -> "tuple[str, float]":
        result = self.layer.last_result
        if result is None:
            return ("No arbitration has run yet.", 0.3)
        rejected = [s for s in result.scores
                    if result.selected is None
                    or s.candidate.label != result.selected.label]
        if not rejected:
            return ("No candidates were rejected; the field had one "
                    "entry.", 0.6)
        parts = [f"{s.candidate.label!r} (total {s.total:.2f}"
                 + (", blocked" if s.blocked else "") + ")"
                 for s in rejected[:5]]
        return ("The rejected candidates were: " + "; ".join(parts)
                + ". Blocked entries carry dominating "
                "safety/governance/inhibition penalties.", 0.85)

    def _inhibited(self) -> "tuple[str, float]":
        recent = self.layer.inhibition.history[-5:]
        if not recent:
            return ("Nothing has been inhibited in this run.", 0.6)
        parts = [f"{row['label']!r} ({row['family']}: {row['reason']})"
                 for row in recent]
        return ("The candidate(s) inhibited most recently: "
                + "; ".join(parts) + ".", 0.9)

    def _plan(self) -> "tuple[str, float]":
        plan = self.layer.last_plan
        if plan is None:
            return ("No plan is active; the executive is not in short_plan "
                    "mode or selected no plannable action.", 0.6)
        if plan.rejected:
            return (f"The planner proposed a plan toward {plan.goal!r} but "
                    f"rejected it: {plan.rejected_reason}.", 0.85)
        steps = " -> ".join(s.label for s in plan.live_steps())
        blocked = "; ".join(f"{s.label!r} ({s.blocked_reason})"
                            for s in plan.blocked_steps())
        return (f"The planner proposed a short simulated plan toward "
                f"{plan.goal!r}: {steps}."
                + (f" Blocked steps: {blocked}." if blocked else "")
                + " Plans are suggestions only.", 0.9)

    def _why_no_action(self) -> "tuple[str, float]":
        result = self.layer.last_result
        if result is None or result.selected is None \
                or result.selected.label != "no_action":
            return ("The last selection was not no_action.", 0.5)
        return (f"no_action was selected because: {result.reason}. "
                "Declining to act is a valid, safe outcome of "
                "arbitration.", 0.9)

    def _focus(self) -> "tuple[str, float]":
        focus = self.layer.last_focus
        if focus is None:
            return ("No focus has been selected yet.", 0.3)
        return (f"The attention selector prioritized {focus.target!r} "
                f"because: {focus.reason}. Attention here is a "
                "prioritization mechanism, not awareness.", 0.85)

    def _winning_score(self) -> "tuple[str, float]":
        result = self.layer.last_result
        if result is None or not result.scores:
            return ("No arbitration scores exist yet.", 0.3)
        best = result.scores[0]
        top = sorted(((k, v) for k, v in best.components.items()
                      if v > 0), key=lambda kv: -kv[1])[:3]
        parts = [f"{k}={v:.2f}" for k, v in top]
        return (f"The winning score belonged to {best.candidate.label!r} "
                f"(total {best.total:.3f}); the strongest components were "
                + ", ".join(parts or ["none positive"])
                + ". All fourteen components are recorded in the decision "
                "trace.", 0.9)

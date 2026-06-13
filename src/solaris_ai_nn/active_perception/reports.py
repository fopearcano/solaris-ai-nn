"""Active-perception reports -- what did the system sample, and why?

The report describes the current sampling policy, the salience map, the
uncertainty state, curiosity pressure, the selected and blocked sampling
actions, expected vs observed information gain, the exploration memory
summary, stagnation status, attention focus history, and the safety /
governance decisions -- with mandatory limitations and a ClaimGuard pass
before any Markdown is written.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport

ACTIVE_PERCEPTION_LIMITATIONS = [
    "Active perception is self-directed sampling inside bounded simulation, "
    "internal memory, or read-only streams; it is never real-world "
    "autonomy, robotics, browser/OS automation, or an external API call.",
    "Curiosity is an intrinsic sampling-pressure metric (a drive to reduce "
    "uncertainty), not a desire, feeling, or personality in the human "
    "sense.",
    "Information gain is a low-compute heuristic with explicit confidence "
    "and uncertainty; observed gain is a proxy measured after the fact, "
    "not proof of understanding.",
    "Every sampling action is a suggestion until safety, governance, ego "
    "boundaries, and executive inhibition validate it; none of them can be "
    "overridden by curiosity.",
    "Stagnation status is cautious: a stable phase with little change may "
    "be acceptable, and 'unknown' is reported when evidence is "
    "insufficient.",
]


class ActivePerceptionReportBuilder:
    """Builds the active perception report from a controller snapshot."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller

    def build(self) -> SessionReport:
        snap = self.controller.snapshot()
        policy = snap.get("policy") or {}
        last_decision = policy.get("last_decision") or {}
        builder = (
            ExperimentReportBuilder(title="Active perception report")
            .add_metadata(
                sampling_policy_mode=policy.get("mode"),
                curiosity_pressure=(snap.get("curiosity") or {}).get(
                    "pressure"),
                stagnation_status=(snap.get("stagnation") or {}).get(
                    "status"))
            .add_section("current_sampling_policy", policy)
            .add_section("salience_map", snap.get("salience"))
            .add_section("uncertainty_state", snap.get("uncertainty"))
            .add_section("curiosity_pressure", snap.get("curiosity"))
            .add_section("selected_sampling_actions", {
                "last_decision": last_decision,
                "alternatives": last_decision.get("alternatives", [])})
            .add_section("blocked_sampling_actions", {
                "blocked_count": snap.get("blocked_count"),
                "last_result": snap.get("last_result")})
            .add_section("expected_vs_observed_information_gain",
                         snap.get("information_gain"))
            .add_section("exploration_memory_summary",
                         snap.get("exploration_memory"))
            .add_section("stagnation_status", snap.get("stagnation"))
            .add_section("attention_focus_history", snap.get("attention"))
            .add_section("safety_governance_decisions", snap.get("safety"))
        )
        for limitation in ACTIVE_PERCEPTION_LIMITATIONS:
            builder.add_limitation(limitation)
        return builder.build()

    # -- outputs ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return self.build().to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        return self.build().to_markdown()

    def save(self, json_path: Union[str, Any],
             md_path: Union[str, Any]) -> Dict[str, Any]:
        from ..language.serialization import save_report

        scan = save_report(self.build(), json_path, md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}


class ActivePerceptionQueryInterface:
    """Fixed queries about sampling, answered in safe, grounded vocabulary.

    Curiosity is described as an intrinsic pressure metric, never a desire;
    every answer is grounded in the controller snapshot, and the system says
    so plainly when it cannot answer.
    """

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self._handlers = {
            "what is the system sampling": self._sampling,
            "why did it look there": self._why,
            "what is the current attention focus": self._focus,
            "what uncertainty is highest": self._uncertainty,
            "what sampling actions were blocked": self._blocked,
            "did sampling improve prediction": self._improved,
            "is curiosity overriding safety": self._override,
        }

    def supported_queries(self):
        return sorted(self._handlers)

    def answer(self, query: str):
        from ..language.query import normalize
        from ..language.schemas import QueryResult

        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence, refs = handler()
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, data={"evidence_refs": refs},
                           confidence=confidence)

    # -- handlers (each returns text, confidence, evidence refs) ------------------

    def _snap(self):
        return self.controller.snapshot()

    def _sampling(self):
        snap = self._snap()
        policy = snap.get("policy") or {}
        decision = (policy.get("last_decision") or {}).get("action") or {}
        action = decision.get("action_type", "no_sampling_action")
        return (f"The sampling policy selected {action!r} under "
                f"{policy.get('mode')} mode.", 0.8,
                ["field:policy.last_decision"])

    def _why(self):
        snap = self._snap()
        decision = (snap.get("policy") or {}).get("last_decision") or {}
        action = decision.get("action") or {}
        return (f"The action was proposed because uncertainty/salience was "
                f"high for {action.get('source_pressure', 'no pressure')}: "
                f"{decision.get('reason', 'no decision recorded')}.", 0.7,
                ["field:policy.last_decision.reason"])

    def _focus(self):
        snap = self._snap()
        focus = (snap.get("attention") or {}).get("current") or {}
        target = focus.get("target_ref", "none")
        return (f"The current attention focus is {target!r} "
                f"(attention is resource allocation, not awareness).", 0.7,
                ["field:attention.current"])

    def _uncertainty(self):
        snap = self._snap()
        top = (snap.get("uncertainty") or {}).get("top_targets") or []
        if not top:
            return ("No uncertainty target is recorded yet.", 0.4,
                    ["field:uncertainty"])
        t = top[0]
        return (f"The highest uncertainty is {t.get('target_ref')!r} "
                f"({t.get('uncertainty')}) from {t.get('source')}.", 0.8,
                ["field:uncertainty.top_targets"])

    def _blocked(self):
        snap = self._snap()
        return (f"{snap.get('blocked_count', 0)} sampling action(s) were "
                "blocked by safety/governance/boundaries.", 0.8,
                ["field:blocked_count"])

    def _improved(self):
        snap = self._snap()
        info = snap.get("information_gain") or {}
        mean = info.get("mean_observed_gain")
        if mean is None:
            return ("No sampling outcomes have been scored yet.", 0.4,
                    ["field:information_gain"])
        verb = "improved" if mean > 0 else ("did not improve" if mean <= 0
                                            else "was unchanged for")
        return (f"On average, sampling {verb} the measured metrics "
                f"(mean observed gain {mean}).", 0.7,
                ["field:information_gain.mean_observed_gain"])

    def _override(self):
        snap = self._snap()
        curiosity = snap.get("curiosity") or {}
        suppressed = curiosity.get("suppressed_by_safety", False)
        return ("No. Curiosity is an intrinsic sampling-pressure metric, not "
                "a desire in the human sense, and it can never override "
                "safety or governance"
                + (" (it is currently suppressed by safety)." if suppressed
                   else "; safety and governance always dominate."), 0.9,
                ["field:curiosity.suppressed_by_safety"])

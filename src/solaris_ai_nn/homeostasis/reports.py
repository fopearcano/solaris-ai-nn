"""Homeostasis reports and queries -- careful words for pressure numbers.

The report covers variables, needs, drives, valence, Being/Not-Being
tension, conflicts, candidates (kept and suppressed), and safety decisions,
with mandatory limitations. The query interface answers seven fixed
questions in safe vocabulary: "the need estimator assigned high pressure
to...", never "the system wanted...". ClaimGuard re-scans at save time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

from ..language.query import normalize
from ..language.reporting import ExperimentReportBuilder, SessionReport
from ..language.schemas import QueryResult

HOMEOSTASIS_LIMITATIONS = [
    "Needs and drives are numeric pressure estimates computed from listed "
    "variables; they are not commands, wants, or feelings.",
    "Valence is feedback polarity (the running sign of reaction/outcome "
    "events), not emotion.",
    "Being/Not-Being tension is an operational continuity metric, not "
    "metaphysical proof of existence.",
    "Desire candidates are suggestions that map to the formal Solaris "
    "Desire signal; nothing in this layer executes actions or overrides "
    "governance.",
    "No claim of will, free agency, or consciousness is made or supported.",
]


class HomeostasisReportBuilder:
    """Builds the report from a HomeostaticRegulator."""

    def __init__(self, regulator: Any) -> None:
        self.regulator = regulator

    def build(self) -> SessionReport:
        regulator = self.regulator
        snap = regulator.snapshot()
        result = regulator.last_result
        candidates = (result.desire_candidates if result else [])
        report = (
            ExperimentReportBuilder(title="Homeostasis report")
            .add_metadata(updates=regulator.updates,
                          dominant_need=snap["summary"]["dominant_need"],
                          dominant_drive=snap["summary"]["dominant_drive"])
            .add_section("homeostatic_variables", {
                "most_urgent": [v.to_dict() for v in
                                regulator.state.most_urgent(5)],
                "variable_count": len(regulator.state.variables),
            })
            .add_section("dominant_needs",
                         (result.need_state.to_dict()["needs"][:5]
                          if result else ["no update has run yet"]))
            .add_section("drive_pressures", snap["drives"])
            .add_section("valence_trend", snap["valence"])
            .add_section("being_not_being_tension",
                         snap["auto_determination"]["current"])
            .add_section("conflicts",
                         [c.to_dict() for c in (result.conflicts
                                                if result else [])]
                         or ["none detected"])
            .add_section("desire_candidates",
                         [c.to_dict() for c in candidates
                          if not c.blocked] or ["none synthesized"])
            .add_section("suppressed_desires",
                         [{"proposal": c.proposal,
                           "reason": c.blocked_reason}
                          for c in candidates if c.blocked]
                         or ["none suppressed"])
            .add_section("safety_governance_decisions", snap["safety"])
            .add_section("inner_map_relation", result.map_update
                         if result else None)
        )
        for limitation in HOMEOSTASIS_LIMITATIONS:
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

        report = self.build()
        check = self.regulator.safety.validate_report_text(
            report.to_markdown())
        scan = save_report(report, json_path, md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict(),
                "anthropomorphism_check": check.to_dict()}


class HomeostasisQueryInterface:
    """Seven fixed queries answered in safe vocabulary."""

    def __init__(self, regulator: Any) -> None:
        self.regulator = regulator
        self._handlers: Dict[str, Callable[[], "tuple[str, float]"]] = {
            "what is the dominant need": self._dominant_need,
            "why was this desire suggested": self._why_desire,
            "what drive is strongest": self._strongest_drive,
            "what conflict blocked action": self._conflict,
            "what is the auto-determination state": self._auto,
            "why did the system recommend rest": self._why_rest,
            "why did the system recommend safe shutdown": self._why_shutdown,
        }

    def supported_queries(self) -> List[str]:
        return sorted(self._handlers)

    def answer(self, query: str) -> QueryResult:
        key = normalize(query).replace("auto determination",
                                       "auto-determination")
        handler = self._handlers.get(key)
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence = handler()
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, confidence=confidence)

    # -- handlers ------------------------------------------------------------

    def _dominant_need(self) -> "tuple[str, float]":
        result = self.regulator.last_result
        dominant = result.need_state.dominant() if result else None
        if dominant is None:
            return ("No need currently carries measurable pressure; the "
                    "estimator has insufficient deviation to report.", 0.4)
        return (f"The need estimator assigned the highest pressure to "
                f"{dominant.type!r} (intensity {dominant.intensity}, "
                f"urgency {dominant.urgency}), derived from: "
                f"{', '.join(dominant.source_variables)}.", 0.9)

    def _why_desire(self) -> "tuple[str, float]":
        best = self.regulator.synthesis.best()
        if best is None:
            return ("No Desire candidate is currently active, so there is "
                    "nothing to explain.", 0.3)
        return (f"The system suggested a Desire object proposing "
                f"{best.proposal!r} (motivation {best.motivation}, "
                f"confidence {best.confidence}) because the need(s) "
                f"{', '.join(best.source_needs) or 'none'} and drive(s) "
                f"{', '.join(best.source_drives) or 'none'} assigned it "
                "pressure. It is a suggestion; nothing was executed.", 0.9)

    def _strongest_drive(self) -> "tuple[str, float]":
        dominant = self.regulator.drives.state.dominant()
        if dominant is None:
            return ("No drive currently carries pressure.", 0.4)
        return (f"The drive resolver prioritized {dominant.category!r} "
                f"(pressure {dominant.pressure}), fed by: "
                f"{', '.join(dominant.contributing_needs) or 'decay only'}.",
                0.9)

    def _conflict(self) -> "tuple[str, float]":
        result = self.regulator.last_result
        conflicts = result.conflicts if result else []
        if not conflicts:
            return ("No conflict suppressed anything in the last update.",
                    0.6)
        worst = max(conflicts, key=lambda c: c.severity)
        return (f"A {worst.kind!r} conflict resolved toward "
                f"{worst.winner!r} (rule: {worst.resolution_rule}); the "
                f"suppressed proposals were "
                f"{', '.join(worst.suppressed_desires) or 'none'} because: "
                f"{worst.reason}.", 0.9)

    def _auto(self) -> "tuple[str, float]":
        tension = self.regulator.auto.state.current
        return (f"Operational Being/Not-Being reading: being pressure "
                f"{tension.being_pressure}, not-being pressure "
                f"{tension.not_being_pressure}, tension {tension.tension}, "
                f"implication {tension.action_implication!r}. This is a "
                "continuity metric, not a metaphysical claim.", 0.85)

    def _why_rest(self) -> "tuple[str, float]":
        regulator = self.regulator
        candidates = [c for c in regulator.synthesis.last_candidates
                      if c.proposal == "rest"]
        if not candidates:
            return ("Rest has not been suggested; energy and fatigue "
                    "pressure are within range.", 0.5)
        candidate = candidates[0]
        return (f"Rest was suggested because the need estimator assigned "
                f"high pressure to {', '.join(candidate.source_needs)} "
                f"(energy variable: "
                f"{regulator.state.value('body_energy', 1.0)}, fatigue: "
                f"{regulator.state.value('fatigue')}). It is a suggestion, "
                "not an executed action.", 0.85)

    def _why_shutdown(self) -> "tuple[str, float]":
        auto = self.regulator.auto.state
        if auto.shutdown_recommendations == 0:
            return ("Safe shutdown has not been recommended in this run.",
                    0.6)
        tension = auto.current
        return (f"Safe shutdown was recommended "
                f"{auto.shutdown_recommendations}x because not-being "
                f"pressure reached {tension.not_being_pressure} "
                f"({'; '.join(tension.reasons[:1])}). "
                "It is a recommendation only: the ops supervisor/watchdog "
                "decides whether to stop.", 0.85)

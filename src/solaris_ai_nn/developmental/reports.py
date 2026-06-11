"""Developmental reports and queries -- cautious words for long-run
numbers.

The report covers runtime age, epochs, memory layers, growth, drift,
milestones, phase-transition candidates, and the structural-change
headline, with mandatory limitations and ClaimGuard before saving. The
query interface answers eight fixed questions in observational voice:
"The runtime recorded...", "This is a phase-transition candidate, not
proof of emergence."
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

from ..language.query import normalize
from ..language.reporting import ExperimentReportBuilder, SessionReport
from ..language.schemas import QueryResult

DEVELOPMENTAL_LIMITATIONS = [
    "Epoch labels, growth classifications, and phase-transition "
    "candidates are measurements over recorded metrics; they prove "
    "nothing about consciousness, life, or emergence.",
    "Simulated-time runs compress months into seconds; their history is "
    "marked simulated and never merged with real wall-clock history.",
    "Memory compression preserves evidence summaries; detail below the "
    "summary resolution is intentionally discarded and said so.",
    "The runtime learns by persistence (repetition, prediction failure, "
    "consolidation, pruning) -- no human feedback, reward training, or "
    "external model shaped these numbers.",
    "Structural change is measured, not assumed; a stagnation label is "
    "as valid a finding as a growth label.",
]


class DevelopmentalReportBuilder:
    """Builds the long-horizon report from a DevelopmentalRuntime."""

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime

    def build(self) -> SessionReport:
        runtime = self.runtime
        snap = runtime.snapshot()
        summary = snap["summary"]
        metrics = snap["metrics"]
        stagnation_warning = (
            f"{summary['stagnation_windows']} consecutive stagnation "
            "window(s); no structural change is being measured"
            if summary["stagnation_windows"] >= 3
            else "no stagnation warning")
        report = (
            ExperimentReportBuilder(title="Developmental report")
            .add_metadata(
                epoch=summary["current_epoch"],
                age_hours=summary["developmental_age_hours"],
                simulated_time=summary["simulated_time"])
            .add_section("runtime_age", {
                "age_hours": summary["developmental_age_hours"],
                "simulated_vs_real": ("simulated time"
                                      if summary["simulated_time"]
                                      else "real wall-clock time"),
                "clock": snap["clock"]})
            .add_section("current_epoch", summary["current_epoch"])
            .add_section("epoch_history", snap["epochs"])
            .add_section("memory_layer_summary", snap["memory"])
            .add_section("growth_metrics", snap["growth"])
            .add_section("drift_metrics", snap["drift"])
            .add_section("milestones", snap["milestones"])
            .add_section("phase_transition_candidates", snap["phases"])
            .add_section("long_horizon_metrics", metrics)
            .add_section("structural_change_score",
                         summary["structural_change_score"])
            .add_section("stagnation_warning", stagnation_warning)
            .add_section("next_recommended_observation_window",
                         self._next_window(summary))
        )
        for limitation in DEVELOPMENTAL_LIMITATIONS:
            report.add_limitation(limitation)
        return report.build()

    @staticmethod
    def _next_window(summary: Dict[str, Any]) -> str:
        age_hours = float(summary["developmental_age_hours"] or 0.0)
        if age_hours < 24:
            return ("continue to the 24h-equivalent mark, then compare "
                    "growth snapshots")
        if age_hours < 24 * 7:
            return ("observe through one week equivalent; watch habit "
                    "stability and consolidation counts")
        if age_hours < 24 * 30:
            return ("observe through one month equivalent; watch drift "
                    "velocity and pruning stability")
        return ("month-scale soak: review fossil memory and epoch "
                "history at weekly intervals")

    def to_dict(self) -> Dict[str, Any]:
        return self.build().to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        return self.build().to_markdown()

    def save(self, json_path: Union[str, Path],
             md_path: Union[str, Path]) -> Dict[str, Any]:
        from ..language.serialization import save_report

        markdown = self.to_markdown()
        safety = self.runtime.safety.validate_report(markdown)
        if not safety.safe:
            raise ValueError("developmental report blocked: "
                             + "; ".join(safety.violations))
        scan = save_report(self.build(), json_path, md_path)
        self.runtime.last_report_path = str(md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}


class DevelopmentalQueryInterface:
    """Eight fixed queries answered in observational voice."""

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime
        self._handlers: Dict[str, Callable[[], "tuple[str, float]"]] = {
            "what developmental epoch is active": self._epoch,
            "what changed over time": self._changed,
            "what milestones were recorded": self._milestones,
            "what is fossil memory": self._fossil,
            "is the system growing or just accumulating data":
                self._growing,
            "what drift was detected": self._drift,
            "what structural changes happened": self._structural,
            "what survived across restarts": self._survived,
        }

    def supported_queries(self) -> List[str]:
        return sorted(self._handlers)

    def answer(self, query: str) -> QueryResult:
        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that "
                      "query. Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence = handler()
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, confidence=confidence)

    # -- handlers ---------------------------------------------------------------

    def _epoch(self) -> "tuple[str, float]":
        state = self.runtime.epochs.state
        return (f"The active developmental epoch label is "
                f"{state.current!r} (after {len(state.transitions)} "
                "transition(s)). An epoch is a label over recorded "
                "metrics, not proof of development.", 0.9)

    def _changed(self) -> "tuple[str, float]":
        latest = self.runtime.growth.latest()
        if latest is None:
            return ("The runtime recorded no growth observations yet.",
                    0.5)
        moved = [f"{k} {v:+g}" for k, v in latest.deltas.items()
                 if v][:5]
        return ("The structure changed according to these metrics: "
                + ("; ".join(moved) if moved else "none moved this "
                   "window")
                + f". Window classification: {latest.classification}.",
                0.85)

    def _milestones(self) -> "tuple[str, float]":
        milestones = self.runtime.milestones.registry.milestones
        if not milestones:
            return ("The runtime recorded no milestones yet.", 0.6)
        parts = [f"{m.type} ({'simulated' if m.simulated else 'real'})"
                 for m in milestones[-5:]]
        return (f"The runtime recorded {len(milestones)} milestone(s); "
                "most recent: " + "; ".join(parts)
                + ". Each references its evidence.", 0.9)

    def _fossil(self) -> "tuple[str, float]":
        state = self.runtime.memory.state()
        return (f"Fossil memory holds {state.fossil_count} rare "
                "transformation milestone(s) -- firsts and identity/"
                "safety events kept indefinitely, append-only, while "
                "routine events compress into summaries.", 0.9)

    def _growing(self) -> "tuple[str, float]":
        latest = self.runtime.growth.latest()
        if latest is None:
            return ("No evidence of structural growth was detected yet; "
                    "no observation windows have completed.", 0.6)
        if latest.classification in ("accumulation", "stagnation"):
            return (f"The latest window classified as "
                    f"{latest.classification}: data volume "
                    f"{'grew' if latest.classification == 'accumulation' else 'did not grow'} "
                    "but structural metrics did not move. No evidence "
                    "of structural growth was detected in this window.",
                    0.85)
        return (f"The latest window classified as "
                f"{latest.classification} with structural change score "
                f"{latest.structural_change_score}. This is a "
                "measurement over recorded metrics, not proof of "
                "development.", 0.85)

    def _drift(self) -> "tuple[str, float]":
        latest = self.runtime.drift.latest()
        if latest is None:
            return ("No drift observations were recorded yet.", 0.5)
        return (f"The drift monitor classified the latest window as "
                f"{latest.classification!r} with mean drift velocity "
                f"{latest.drift_velocity}. "
                + ("; ".join(latest.warnings)
                   if latest.warnings else
                   "Slow drift is expected adaptation.") + ".", 0.85)

    def _structural(self) -> "tuple[str, float]":
        metrics = self.runtime.metrics()
        return (f"The runtime recorded structural change score "
                f"{metrics.get('structural_change_score', 0.0)}, "
                f"{metrics.get('consolidation_count', 0)} "
                f"consolidation(s), and "
                f"{metrics.get('fossil_memory_count', 0)} fossil "
                "record(s). Any phase-transition candidate in the "
                "report is a hypothesis, not proof of emergence.", 0.85)

    def _survived(self) -> "tuple[str, float]":
        clock = self.runtime.clock
        memory = self.runtime.memory.state()
        return (f"Across {len(clock.restart_gaps)} restart gap(s), the "
                "persisted state survived: "
                f"{memory.cold_count} cold schema(s), "
                f"{memory.fossil_count} fossil record(s), the epoch "
                "history, and the identity anchors. Continuity here is "
                "operational runtime continuity, nothing more.", 0.85)

"""LatentReportBuilder -- the written account of offline processing.

Everything a latent run did, in one report: transitions, cycles, replays,
counterfactuals, anticipation accuracy, Mysterium changes, complexity
pressure, consolidation, suggestions, mutations, and safety decisions --
with mandatory limitations and the offline framing made explicit. Markdown
is saved through the language layer, so ClaimGuard scans every report.

The ``explanations()`` block also provides the controlled latent phrasing
("During offline replay, the system simulated ..."): replay is always named
as offline simulation, never as experience.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport

LATENT_LIMITATIONS = [
    "\"Sleep\" and \"dream\" name bounded maintenance and sandboxed replay; "
    "no human-like sleep, dreaming, or subjective experience is implied.",
    "Counterfactual outcomes are offline simulations over remembered "
    "windows; they are not observations and carry no evidential weight "
    "about the world.",
    "Mysterium is a numeric unknown-pressure estimate computed from listed "
    "reasons; it does not measure anything mystical.",
    "Anticipation uses frequency/recency statistics; accuracy reflects "
    "pattern regularity, not understanding.",
]


@dataclass
class LatentReportBuilder:
    """Accumulates latent evidence, then renders dict / JSON / Markdown."""

    run_id: str = ""
    session_id: str = ""
    sections: Dict[str, Any] = field(default_factory=dict)

    # -- collectors --------------------------------------------------------------

    def add(self, name: str, data: Any) -> "LatentReportBuilder":
        if data is not None:
            self.sections[name] = data
        return self

    def collect(self,
                controller: Any = None,
                sleep_cycle: Any = None,
                dream_cycle: Any = None,
                replay_engine: Any = None,
                anticipation: Any = None,
                mysterium: Any = None,
                complexity: Any = None,
                store: Any = None,
                safety: Any = None,
                scheduler: Any = None) -> "LatentReportBuilder":
        """Pull the standard sections from the latent components."""
        if controller is not None:
            snap = controller.snapshot()
            self.add("mode_transitions", {
                "counts": snap.get("mode_counts"),
                "recent": snap.get("recent_transitions"),
                "last_wake_summary": snap.get("last_wake_summary")})
        if sleep_cycle is not None:
            self.add("sleep_cycles", sleep_cycle.snapshot())
        if dream_cycle is not None:
            snap = dream_cycle.snapshot()
            self.add("dream_counterfactual_simulations", snap)
            last = snap.get("last_result") or {}
            if last.get("offline_suggestions"):
                self.add("offline_suggestions", last["offline_suggestions"])
            self.add("production_mutations", {
                "count": last.get("production_mutations", 0),
                "allowed": snap.get("allow_production_mutation", False)})
        if replay_engine is not None:
            self.add("replay_windows", replay_engine.to_report())
        if anticipation is not None:
            self.add("anticipation_accuracy", anticipation.snapshot())
        if mysterium is not None:
            self.add("mysterium_pressure", mysterium.snapshot())
        if complexity is not None:
            self.add("complexity_pressure", complexity.snapshot())
        if store is not None:
            self.add("memory_consolidation", store.snapshot())
        if safety is not None:
            self.add("safety_decisions", safety.snapshot())
        if scheduler is not None:
            self.add("scheduler", scheduler.snapshot())
        return self

    # -- controlled latent explanations -----------------------------------------

    def explanations(self) -> Dict[str, str]:
        """Deterministic sentences about the latent run, honestly hedged."""
        out: Dict[str, str] = {}
        transitions = self.sections.get("mode_transitions") or {}
        recent = transitions.get("recent") or []
        if recent:
            # Prefer the most recent entry into a latent/quiet mode -- that
            # is the decision worth explaining (waking is just the return).
            interesting = [t for t in recent if t["to_mode"] in
                           ("quiet", "sleep", "consolidation", "replay",
                            "dream")]
            last = (interesting or recent)[-1]
            out["mode_entry"] = (
                f"The system entered {last['to_mode']} mode because: "
                f"{last['reason']}.")
        else:
            out["mode_entry"] = ("The system has insufficient transition "
                                 "data to explain a mode entry.")

        replays = self.sections.get("replay_windows") or {}
        if replays.get("replays"):
            out["replay"] = (
                f"During offline replay, the system simulated "
                f"{replays['events_replayed']} remembered event(s) across "
                f"{replays['replays']} window(s) in an isolated sandbox; "
                f"{replays.get('suggestion_changes', 0)} window(s) changed "
                "the suggested action.")
        else:
            out["replay"] = ("No offline replay has run yet, so the system "
                             "does not know how replay would change its "
                             "suggestions.")

        dreams = self.sections.get("dream_counterfactual_simulations") or {}
        last_dream = dreams.get("last_result") or {}
        if last_dream.get("counterfactuals_tested"):
            kinds = ", ".join(last_dream.get("counterfactual_kinds", []))
            out["counterfactual"] = (
                "During offline replay, the system simulated counterfactual "
                f"variant(s) ({kinds}) of remembered windows; mean "
                f"divergence was {last_dream.get('mean_divergence', 0.0)}. "
                "These are simulations, not observations.")
        else:
            out["counterfactual"] = ("No counterfactual has been simulated "
                                     "yet.")

        anticipation = self.sections.get("anticipation_accuracy") or {}
        if anticipation.get("prediction_count"):
            out["anticipation"] = (
                f"Anticipation made {anticipation['prediction_count']} "
                f"prediction(s): {anticipation['hit_count']} hit, "
                f"{anticipation['miss_count']} missed (rolling accuracy "
                f"{anticipation['rolling_accuracy']}).")
        else:
            out["anticipation"] = ("No predictions have been scored yet, so "
                                   "anticipation accuracy is not known.")

        mysterium = self.sections.get("mysterium_pressure") or {}
        reasons = mysterium.get("recent_reasons") or []
        if reasons:
            last_reason = reasons[-1]
            direction = ("increased" if last_reason["delta"] > 0
                         else "decreased")
            out["unknown_pressure"] = (
                f"Unknown pressure {direction} to "
                f"{mysterium.get('pressure')} most recently because: "
                f"{last_reason['reason']}.")
        else:
            out["unknown_pressure"] = ("Unknown pressure has not changed "
                                       "yet; the system does not know what "
                                       "it does not know here.")

        consolidation = self.sections.get("memory_consolidation") or {}
        if consolidation.get("schema_count"):
            out["consolidation"] = (
                f"Consolidation distilled {consolidation['schema_count']} "
                "schema(s) from repeated trace patterns.")
        else:
            out["consolidation"] = "Nothing has been consolidated yet."
        return out

    # -- renderers -----------------------------------------------------------------

    def build(self) -> SessionReport:
        builder = (ExperimentReportBuilder(title="Latent cognition report")
                   .add_metadata(run_id=self.run_id,
                                 session_id=self.session_id,
                                 offline="all latent output is offline "
                                         "simulated processing"))
        order = ["mode_transitions", "sleep_cycles", "replay_windows",
                 "dream_counterfactual_simulations", "anticipation_accuracy",
                 "mysterium_pressure", "complexity_pressure",
                 "memory_consolidation", "offline_suggestions",
                 "production_mutations", "safety_decisions", "scheduler"]
        for name in order:
            if name in self.sections:
                builder.add_section(name, self.sections[name])
        for name, data in self.sections.items():
            if name not in order:
                builder.add_section(name, data)
        builder.add_section("explanations", self.explanations())
        for limitation in LATENT_LIMITATIONS:
            builder.add_limitation(limitation)
        return builder.build()

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

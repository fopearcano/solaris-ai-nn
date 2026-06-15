"""Perceptual metabolism runtime -- regulate continuous sensory exposure.

:class:`PerceptualMetabolismRuntime` reads the plural-sensorium state (and, if
available, live-field source health and a feeder-SDK monitor snapshot) and runs
one bounded metabolic tick: it updates perceptual needs and the energy budget,
regulates sensory homeostasis, allocates the attention economy, detects overload
and deprivation, regulates novelty appetite, analyses the source diet, and
estimates consolidation pressure. All outputs are *internal* regulation
recommendations: the runtime polls no hardware, starts no feeder, modifies no
source, and executes nothing in the real world.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .attention_economy import AttentionEconomy
from .consolidation_pressure import ConsolidationPressureEstimator
from .deprivation import DeprivationDetector
from .energy_budget import TASKS, PerceptualEnergyBudget
from .needs import PerceptualNeedModel
from .novelty_appetite import NoveltyAppetiteRegulator
from .overload import OverloadDetector
from .safety import PerceptualMetabolismSafetyValidator
from .sensory_homeostasis import SensoryHomeostasisRegulator
from .source_diet import SourceDietAnalyzer


class MetabolismMilestone:
    FIRST_NEED_PRESSURE = "first_perceptual_need_pressure"
    FIRST_OVERLOAD = "first_sensory_overload"
    FIRST_DEPRIVATION = "first_sensory_deprivation"
    FIRST_SOURCE_DIET_SHIFT = "first_source_diet_shift"
    FIRST_CONSOLIDATION_PRESSURE = "first_consolidation_pressure"
    FIRST_ATTENTION_REALLOCATION = "first_attention_economy_reallocation"
    FIRST_RECEPTOR_RECOVERY_CYCLE = "first_receptor_recovery_cycle"
    FIRST_SILENCE_AS_STIMULUS = "first_silence_as_stimulus_integration"

    ALL = (FIRST_NEED_PRESSURE, FIRST_OVERLOAD, FIRST_DEPRIVATION,
           FIRST_SOURCE_DIET_SHIFT, FIRST_CONSOLIDATION_PRESSURE,
           FIRST_ATTENTION_REALLOCATION, FIRST_RECEPTOR_RECOVERY_CYCLE,
           FIRST_SILENCE_AS_STIMULUS)


@dataclass
class PerceptualMetabolismRuntime:
    """The bounded metabolic regulation loop (internal-only recommendations)."""

    state_dir: str = ".solaris_ai_nn_state"
    sensorium: Any = None
    live_field: Any = None
    feeder_monitor_snapshot: Optional[Dict[str, Any]] = None
    max_ticks: int = 120
    max_runtime_s: float = 30.0
    budget_per_tick: float = 12.0
    overload_threshold: int = 50
    deprivation_threshold: float = 0.15
    enable_consolidation_recommendation: bool = True
    enable_attention_reallocation: bool = True
    dry_run: bool = False

    needs: PerceptualNeedModel = field(default_factory=PerceptualNeedModel)
    budget: PerceptualEnergyBudget = field(default=None, init=False)
    homeostasis: SensoryHomeostasisRegulator = field(
        default_factory=SensoryHomeostasisRegulator)
    attention: AttentionEconomy = field(default_factory=AttentionEconomy)
    overload: OverloadDetector = field(default=None, init=False)
    deprivation: DeprivationDetector = field(default_factory=DeprivationDetector)
    novelty: NoveltyAppetiteRegulator = field(
        default_factory=NoveltyAppetiteRegulator)
    diet: SourceDietAnalyzer = field(default_factory=SourceDietAnalyzer)
    consolidation: ConsolidationPressureEstimator = field(
        default_factory=ConsolidationPressureEstimator)
    safety: PerceptualMetabolismSafetyValidator = field(
        default_factory=PerceptualMetabolismSafetyValidator)

    milestones: List[str] = field(default_factory=list, init=False)
    recommendations: List[Dict[str, Any]] = field(default_factory=list,
                                                  init=False)
    ticks_run: int = field(default=0, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _prev_dominant_class: Optional[str] = field(default=None, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.budget = PerceptualEnergyBudget(budget_per_tick=self.budget_per_tick)
        self.overload = OverloadDetector(
            events_per_tick_threshold=self.overload_threshold)
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    def _source_health(self) -> Any:
        return getattr(self.live_field, "health", None)

    def _milestone(self, name: str) -> None:
        if name not in self.milestones:
            self.milestones.append(name)

    def update(self, *, events_this_tick: int = 0,
               tick: int = 0) -> Dict[str, Any]:
        """Run one bounded metabolic tick over the current sensorium state."""
        if self._refused:
            return {"refused": True, "reason": "unbounded metabolic loop"}
        self.ticks_run += 1
        sensorium = self.sensorium
        field_state = (sensorium.sensory_field.state()
                       if sensorium is not None
                       and hasattr(sensorium, "sensory_field") else None)
        receptors = (list(sensorium.receptors.values())
                     if sensorium is not None else [])
        source_health = self._source_health()

        # 1. Needs.
        self.needs.update(field_state, receptors, tick=tick)
        dominant = self.needs.dominant()
        if dominant and dominant.pressure > 0.0:
            self._milestone(MetabolismMilestone.FIRST_NEED_PRESSURE)

        # 2. Energy budget (priority tasks always requested).
        budget_result = self.budget.allocate(list(TASKS))

        # 3. Homeostasis.
        homeostasis_state = self.homeostasis.regulate(
            field_state, receptors, source_health=source_health)

        # 4. Attention economy.
        attention_state = None
        if self.enable_attention_reallocation:
            attention_state = self.attention.allocate(
                field_state, receptors, self.needs)
            if attention_state.reallocation_count > 0:
                self._milestone(MetabolismMilestone.FIRST_ATTENTION_REALLOCATION)

        # 5. Overload.
        overload_events = self.overload.detect(
            events_this_tick=events_this_tick, sensorium=sensorium,
            source_health=source_health)
        if overload_events:
            self._milestone(MetabolismMilestone.FIRST_OVERLOAD)
            self._warn_auto_regeneration(overload_events)

        # 6. Deprivation.
        deprivation_events = self.deprivation.detect(
            sensorium=sensorium, source_health=source_health)
        if deprivation_events:
            self._milestone(MetabolismMilestone.FIRST_DEPRIVATION)
            self._milestone(MetabolismMilestone.FIRST_SILENCE_AS_STIMULUS)

        # 7. Novelty appetite.
        novelty_state = self.novelty.update(sensorium, field_state=field_state) \
            if sensorium is not None else None

        # 8. Source diet.
        diet_balance = (self.diet.analyze(sensorium, source_health=source_health)
                        if sensorium is not None else None)
        if diet_balance and diet_balance.dominant_class \
                and diet_balance.dominant_class != self._prev_dominant_class:
            if self._prev_dominant_class is not None:
                self._milestone(MetabolismMilestone.FIRST_SOURCE_DIET_SHIFT)
            self._prev_dominant_class = diet_balance.dominant_class

        # 9. Consolidation pressure.
        consolidation_state = None
        if self.enable_consolidation_recommendation and sensorium is not None:
            consolidation_state = self.consolidation.estimate(
                sensorium, overloaded=bool(overload_events),
                source_silent=bool(
                    source_health and getattr(source_health, "silent_sources",
                                              lambda: [])()))
            if consolidation_state.pressure > 0.0:
                self._milestone(MetabolismMilestone.FIRST_CONSOLIDATION_PRESSURE)

        if any(getattr(r, "adaptation_state", "") == "recovering"
               for r in receptors):
            self._milestone(MetabolismMilestone.FIRST_RECEPTOR_RECOVERY_CYCLE)

        self._collect_recommendations(homeostasis_state, overload_events,
                                      deprivation_events, consolidation_state)
        self._last = {
            "tick": tick,
            "field_state": field_state.to_dict() if field_state else {},
            "needs": self.needs.to_dict(),
            "energy_budget": budget_result.to_dict(),
            "homeostasis": homeostasis_state.to_dict(),
            "attention": attention_state.to_dict() if attention_state else {},
            "overload": self.overload.state.to_dict(),
            "deprivation": self.deprivation.state.to_dict(),
            "novelty_appetite": novelty_state.to_dict() if novelty_state else {},
            "source_diet": diet_balance.to_dict() if diet_balance else {},
            "consolidation": (consolidation_state.to_dict()
                              if consolidation_state else {}),
        }
        return self._last

    def run_bounded(self, max_ticks: Optional[int] = None) -> Dict[str, Any]:
        """Run repeated metabolic ticks over the (static) sensorium state."""
        if self._refused:
            return {"refused": True}
        started = time.time()
        n = min(self.max_ticks, max_ticks or self.max_ticks)
        for tick in range(n):
            if time.time() - started > self.max_runtime_s:
                break
            self.update(tick=tick)
        return {"refused": False, "ticks_run": self.ticks_run, "last": self._last}

    def _warn_auto_regeneration(self, overload_events: List[Any]) -> None:
        for ev in overload_events:
            if "auto_regeneration" in " ".join(ev.responses) \
                    or ev.kind in ("source_corruption_flood",
                                   "report_artifact_bloat",
                                   "memory_growth_spike"):
                self.recommendations.append({
                    "target": "auto_regeneration", "kind": "warning",
                    "detail": ev.kind,
                    "note": "recommend hygiene/quarantine; never delete raw "
                            "evidence"})

    def latent_replay_recommendations(self) -> List[str]:
        if self.sensorium is None:
            return []
        return self.consolidation.latent_replay_recommendations(self.sensorium)

    def _collect_recommendations(self, homeostasis_state: Any,
                                 overload_events: List[Any],
                                 deprivation_events: List[Any],
                                 consolidation_state: Any) -> None:
        for rec in homeostasis_state.recommendations:
            self.recommendations.append({"target": "homeostasis",
                                         "kind": rec.action,
                                         "detail": rec.reason})
        for ev in overload_events:
            self.recommendations.append({"target": "overload", "kind": ev.kind,
                                         "responses": ev.responses})
        for ev in deprivation_events:
            self.recommendations.append({"target": "deprivation",
                                         "kind": ev.kind,
                                         "responses": ev.responses})
        if consolidation_state is not None and \
                consolidation_state.recommendation != "no_consolidation_needed":
            self.recommendations.append({
                "target": "consolidation",
                "kind": consolidation_state.recommendation,
                "pressure": consolidation_state.pressure})

    # -- status ---------------------------------------------------------------

    def metabolism_status(self) -> Dict[str, Any]:
        last = self._last
        dominant = self.needs.dominant()
        diet = last.get("source_diet", {})
        consolidation = last.get("consolidation", {})
        return {
            "perceptual_metabolism_enabled": True,
            "perceptual_need_count": len(self.needs.needs),
            "dominant_perceptual_need": dominant.need_type if dominant else None,
            "dominant_need_pressure": round(dominant.pressure, 4)
            if dominant else 0.0,
            "overload_state": self.overload.state.overloaded,
            "overload_event_count": len(self.overload.state.events),
            "deprivation_state": self.deprivation.state.deprived,
            "deprivation_event_count": len(self.deprivation.state.events),
            "source_diet_diversity": diet.get("diet_diversity", 0.0),
            "modality_dominance_score": diet.get("modality_dominance", 0.0),
            "human_label_dominance_score": diet.get("human_label_dominance",
                                                    0.0),
            "attention_allocation_state": last.get("attention", {}).get(
                "allocation_count", 0),
            "attention_reallocation_count": self.attention.state.reallocation_count
            if self.attention.state else 0,
            "consolidation_pressure_score": consolidation.get("pressure", 0.0),
            "novelty_appetite_pressure": last.get("novelty_appetite", {}).get(
                "novelty_fatigue", 0.0),
            "recommendation_count": len(self.recommendations),
            "latest_metabolism_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "PERCEPTUAL_METABOLISM_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.metabolism_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import PerceptualMetabolismReportBuilder

        return PerceptualMetabolismReportBuilder(self).write()

"""Long-horizon developmental runtime -- bounded cycles, persistent growth history.

:class:`LongHorizonDevelopmentalRuntime` orchestrates bounded developmental cycles
over the full sensorium-native stack (Prompts 41-52). Each tick it collects the
upstream module statuses, advances the operational life cycle, updates the growth
state, detects maturation markers / phase transitions / plateaus / regressions,
builds operational life history, manages epochs, and (periodically) analyzes growth
vs accumulation. State persists across restarts. It starts no feeders, controls no
hardware, modifies no source, performs no external action, uses no human teaching,
and claims no life/consciousness/personhood.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .developmental_epoch import (
    DevelopmentalEpoch,
    EpochBoundary,
    EpochSummary,
    EpochTransitionReason,
)
from .developmental_memory import DevelopmentalMemoryStore
from .growth_state import DevelopmentalGrowthState
from .life_cycle import LifeCycleClock, LifeCyclePhase
from .life_history import LifeHistoryBuilder
from .maturation import MaturationDetector
from .phase_transition import PhaseTransitionDetector
from .plateau import PlateauDetector
from .regression import RegressionDetector
from .reports import DevelopmentalLifeReportBuilder
from .safety import DevelopmentalLifeSafetyValidator
from .structural_growth import StructuralGrowthAnalyzer

# Module name -> status method to read its summary.
_STATUS_METHODS = {
    "plural_sensorium": "plural_sensorium_status",
    "perceptual_metabolism": "metabolism_status",
    "perceptual_ontogenesis": "ontogenesis_status",
    "semiogenesis": "semiogenesis_status",
    "sensorium_cognition": "cognition_status",
    "self_boundary": "self_boundary_status",
    "desire_formation": "desire_status",
    "action_reaction": "action_reaction_status",
}


@dataclass
class LongHorizonDevelopmentalRuntime:
    """The bounded long-horizon developmental loop (persistent, internal-only)."""

    state_dir: str = ".solaris_ai_nn_development"
    modules: Dict[str, Any] = field(default_factory=dict)
    max_runtime_s: float = 30.0
    max_ticks: int = 120
    epoch_tick_span: int = 4
    checkpoint_interval_ticks: int = 5
    allow_live_read_only: bool = False
    require_governance_for_live: bool = True
    dry_run: bool = False
    report_only: bool = False
    fixture_mode: bool = True

    clock: LifeCycleClock = field(default_factory=LifeCycleClock)
    growth: DevelopmentalGrowthState = field(
        default_factory=DevelopmentalGrowthState)
    maturation: MaturationDetector = field(default_factory=MaturationDetector)
    transition_detector: PhaseTransitionDetector = field(
        default_factory=PhaseTransitionDetector)
    plateau_detector: PlateauDetector = field(default_factory=PlateauDetector)
    regression_detector: RegressionDetector = field(
        default_factory=RegressionDetector)
    growth_analyzer: StructuralGrowthAnalyzer = field(
        default_factory=StructuralGrowthAnalyzer)
    life_history: LifeHistoryBuilder = field(default_factory=LifeHistoryBuilder)
    memory: DevelopmentalMemoryStore = field(default=None, init=False)
    safety: DevelopmentalLifeSafetyValidator = field(
        default_factory=DevelopmentalLifeSafetyValidator)

    epochs: List[DevelopmentalEpoch] = field(default_factory=list, init=False)
    dim_history: List[Dict[str, float]] = field(default_factory=list,
                                                init=False)
    composite_history: List[float] = field(default_factory=list, init=False)
    transitions: List[Any] = field(default_factory=list, init=False)
    plateaus: List[Any] = field(default_factory=list, init=False)
    regressions: List[Any] = field(default_factory=list, init=False)
    accumulation_warnings: int = field(default=0, init=False)
    growth_report: Any = field(default=None, init=False)
    milestones: List[str] = field(default_factory=list, init=False)
    ticks_run: int = field(default=0, init=False)
    _prev_dims: Dict[str, float] = field(default_factory=dict, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.memory = DevelopmentalMemoryStore(state_dir=self.state_dir,
                                               persist=not self.dry_run)
        self.memory.load_index()  # state survives restart
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    def _collect_statuses(self) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for name, component in self.modules.items():
            if component is None:
                continue
            if isinstance(component, dict):
                out[name] = component
                continue
            method = _STATUS_METHODS.get(name)
            if method and hasattr(component, method):
                try:
                    out[name] = getattr(component, method)()
                except Exception:
                    out[name] = {}
            elif hasattr(component, "snapshot"):
                out[name] = component.snapshot()
        return out

    def _open_epoch(self, tick: int, reason: str, detail: str = "") -> None:
        epoch = DevelopmentalEpoch(
            epoch_index=len(self.epochs), start_tick=tick,
            open_boundary=EpochBoundary(reason=reason, detail=detail))
        self.epochs.append(epoch)

    def update(self, *, tick: int = 0) -> Dict[str, Any]:
        """Run one bounded developmental tick over the upstream module states."""
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        self.ticks_run += 1
        if tick == 0 and not self.epochs:
            self.clock.enter(LifeCyclePhase.BOOT, tick=tick)
            self._open_epoch(tick, EpochTransitionReason.TIME_ELAPSED, "boot")

        statuses = self._collect_statuses()

        # 1. Advance the operational life cycle.
        self.clock.advance(tick=tick)
        self.memory.record_life_cycle(self.clock.state.events[-1].to_dict())

        # 2. Update growth state.
        self.growth.update(statuses, prior=self._prev_dims)
        self.memory.record_growth_state(self.growth.to_dict())
        self.dim_history.append(dict(self.growth.dimensions))
        self.composite_history.append(self.growth.composite())

        # 3. Maturation markers.
        markers = self.maturation.detect(statuses, tick=tick)
        for m in self.maturation.markers:
            self.memory.record_maturation(m.to_dict())

        # 4. Phase transitions.
        self.transitions = self.transition_detector.detect(
            prior_dims=self._prev_dims, current_dims=self.growth.dimensions)
        for t in self.transition_detector.confident_transitions():
            self.memory.record_phase_transition(t.to_dict())

        # 5. Plateaus.
        self.plateaus = self.plateau_detector.detect(
            composite_history=self.composite_history, statuses=statuses)
        for p in self.plateaus:
            self.memory.record_plateau(p.to_dict())

        # 6. Regressions.
        self.regressions = self.regression_detector.detect(
            prior_dims=self._prev_dims, current_dims=self.growth.dimensions,
            statuses=statuses)
        for r in self.regressions:
            self.memory.record_regression(r.to_dict())

        # 7. Life history.
        self.life_history.build_from_tick(
            statuses, maturation_markers=markers, regressions=self.regressions,
            plateaus=self.plateaus, tick=tick)

        # 8. Epoch management (close/open on span, transition, plateau, regression).
        self._manage_epochs(tick)

        # 9. Growth vs accumulation (periodic).
        if self.ticks_run % max(1, self.checkpoint_interval_ticks) == 0 \
                or self.ticks_run >= min(self.max_ticks, 1):
            self._analyze_growth(statuses)

        self._prev_dims = dict(self.growth.dimensions)
        self.memory.write_index()
        self._last = {
            "tick": tick,
            "phase": self.clock.state.phase,
            "epoch_count": len(self.epochs),
            "composite_growth": self.growth.composite(),
            "maturation_marker_count": len(self.maturation.markers),
            "transition_count": len(
                self.transition_detector.confident_transitions()),
            "plateau_count": self.memory.index.plateau_count,
            "regression_count": self.memory.index.regression_count,
        }
        return self._last

    def _manage_epochs(self, tick: int) -> None:
        if not self.epochs:
            return
        current = self.epochs[-1]
        reason = None
        if self.regressions:
            reason = EpochTransitionReason.REGRESSION_DETECTED
        elif self.plateaus:
            reason = EpochTransitionReason.PLATEAU_DETECTED
        elif self.transition_detector.confident_transitions():
            reason = EpochTransitionReason.PREDICTION_IMPROVEMENT
        elif tick - current.start_tick >= self.epoch_tick_span:
            reason = EpochTransitionReason.TIME_ELAPSED
        if reason is not None and not current.closed:
            current.summary = EpochSummary(
                composite_growth=self.growth.composite(),
                increased_dimensions=self.growth.increased_dimensions(),
                maturation_marker_count=len(self.maturation.markers))
            current.close(tick, EpochBoundary(reason=reason,
                                              evidence_refs=["growth_state"]))
            self.memory.record_epoch(current.to_dict())
            self._open_epoch(tick, reason)

    def _analyze_growth(self, statuses: Dict[str, Dict[str, Any]]) -> None:
        # An accumulation warning: many ticks but flat composite growth.
        if len(self.composite_history) >= 3 and \
                max(self.composite_history) - min(self.composite_history) < 0.02:
            self.accumulation_warnings += 1
        self.growth_report = self.growth_analyzer.analyze(
            dim_history=self.dim_history, statuses=statuses,
            regression_count=self.memory.index.regression_count,
            accumulation_warnings=self.accumulation_warnings)

    def run_bounded(self, max_ticks: Optional[int] = None) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True}
        started = time.time()
        n = min(self.max_ticks, max_ticks or self.max_ticks)
        for tick in range(n):
            if time.time() - started > self.max_runtime_s:
                break
            self.update(tick=tick)
        # Close the final open epoch on completion.
        if self.epochs and not self.epochs[-1].closed:
            self.epochs[-1].close(
                self.ticks_run,
                EpochBoundary(reason=EpochTransitionReason.OPERATOR_CHECKPOINT))
            self.memory.record_epoch(self.epochs[-1].to_dict())
        return {"refused": False, "ticks_run": self.ticks_run,
                "last": self._last}

    def restart(self) -> None:
        """Record a restart; reload persisted index; note discontinuity."""
        self.clock.restart(tick=self.ticks_run)
        self.memory.load_index()
        self.regression_detector.add_restart_discontinuity()

    # -- integration views ----------------------------------------------------

    def architecture_proposals(self) -> List[Dict[str, Any]]:
        from ..architecture_evolution import developmental_revision_proposals

        return developmental_revision_proposals(self.developmental_status())

    def developmental_status(self) -> Dict[str, Any]:
        gr = (self.growth_report.result.verdict
              if self.growth_report is not None else "inconclusive")
        gr_score = (self.growth_report.result.structural_growth_score
                    if self.growth_report is not None else 0.0)
        report = self.growth_report
        return {
            "developmental_life_enabled": True,
            "current_life_cycle_phase": self.clock.state.phase,
            "life_cycle_phase_count": len(self.clock.state.phases_visited),
            "current_epoch_id": (self.epochs[-1].epoch_id if self.epochs
                                 else None),
            "developmental_epoch_count": len(self.epochs),
            "maturation_marker_count": len(self.maturation.markers),
            "weak_maturation_marker_count": len(self.maturation.weak_markers),
            "phase_transition_count": len(
                self.transition_detector.confident_transitions()),
            "plateau_count": self.memory.index.plateau_count,
            "regression_count": self.memory.index.regression_count,
            "structural_growth_status": gr,
            "structural_growth_score": gr_score,
            "accumulation_warning_count": self.accumulation_warnings,
            "composite_growth": self.growth.composite(),
            "durable_prediction_improvement_score": (
                report.durable_prediction_improvement if report else 0.0),
            "durable_action_effect_learning_score": (
                report.durable_action_effect_learning if report else 0.0),
            "durable_concept_stability_score": (
                report.durable_concept_stability if report else 0.0),
            "durable_sign_stability_score": (
                report.durable_sign_stability if report else 0.0),
            "continuity_recovery_count": self.clock.state.restart_count,
            "developmental_safety_block_count": self.safety.rejected_count,
            "latest_developmental_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "DEVELOPMENTAL_LIFE_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.developmental_status()

    def write_artifacts(self) -> Dict[str, Any]:
        return DevelopmentalLifeReportBuilder(self).write()

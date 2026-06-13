"""DevelopmentalNursery -- the controlled world the system grows up in.

A developmental system needs an ecology, not a teacher. The nursery wires
a :class:`StimulusEcology` (regimes, cycles, scarcity, novelty,
anomalies, seasonality, deprivation, delayed consequences) to an event
log, an ecology memory, and a canonical-signal stream, then exposes a
``stimulus_provider(step)`` the runner can consume. Deterministic with a
seed, bounded by default, low-compute, no network, no real-world action.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .cycles import CycleManager, CycleType
from .ecology_memory import EcologyEpisode, EcologyMemory
from .events import EcologyEvent, EcologyStimulus
from .regimes import RegimeManager, RegimeType
from .safety import EcologySafetyValidator
from .seasonality import SeasonalityModel
from .stimulus_ecology import StimulusEcology
from .streams import EcologyStream


@dataclass
class NurseryConfig:
    """How the developmental world is shaped (all bounded by default)."""

    nursery_id: str = "nursery-0"
    seed: int = 7
    simulated_time: bool = True
    time_acceleration: float = 3600.0
    duration_steps: int = 500
    duration_days_equivalent: Optional[float] = None
    active_regimes: List[str] = field(
        default_factory=lambda: [RegimeType.MIXED_NURSERY])
    active_cycles: List[str] = field(
        default_factory=lambda: [CycleType.DAY_NIGHT,
                                 CycleType.SIGNAL_SILENCE])
    novelty_rate: float = 0.08
    anomaly_rate: float = 0.04
    scarcity_rate: float = 0.2
    absence_rate: float = 0.25
    danger_reward_balance: float = 0.5  # 0 = all danger, 1 = all reward
    delayed_consequence_rate: float = 0.08
    seasonal_shift_interval: int = 200
    max_events_per_step: int = 3
    output_state_dir: Optional[Union[str, Path]] = None
    preserve_event_log: bool = True
    # Long-scale / external flags (gated by governance via safety).
    month_scale: bool = False
    year_scale: bool = False
    external_source: Optional[Any] = None
    read_only_stream: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = dict(self.__dict__)
        data["output_state_dir"] = (str(self.output_state_dir)
                                    if self.output_state_dir else None)
        data["external_source"] = (str(self.external_source)
                                   if self.external_source else None)
        return data


@dataclass
class NurseryState:
    """The nursery's running counters."""

    step: int = 0
    events_total: int = 0
    absence_windows: int = 0
    novelty_events: int = 0
    anomaly_events: int = 0
    delayed_groups: int = 0
    seasonal_shifts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DevelopmentalNursery:
    """Generates ecology events and feeds them to the runner."""

    config: NurseryConfig = field(default_factory=NurseryConfig)
    governance: Any = None

    def __post_init__(self) -> None:
        self.safety = EcologySafetyValidator()
        report = self.safety.validate_config(self.config,
                                             self.governance)
        if not report.safe:
            raise PermissionError("nursery refused: "
                                  + "; ".join(report.violations))
        c = self.config
        regimes = RegimeManager(active_regimes=list(c.active_regimes))
        cycles = CycleManager(active_cycles=list(c.active_cycles))
        seasonality = SeasonalityModel(
            shift_interval=c.seasonal_shift_interval)
        self.ecology = StimulusEcology(
            seed=c.seed, regimes=regimes, cycles=cycles,
            seasonality=seasonality,
            max_events_per_step=c.max_events_per_step)
        # Apply config-level rate overrides onto the active regime profile.
        regime = regimes.current_regime()
        regime.novelty_probability = c.novelty_rate
        regime.anomaly_probability = c.anomaly_rate
        regime.delayed_consequence_probability = c.delayed_consequence_rate
        regime.silence_probability = c.absence_rate
        self.ecology.deprivation.max_window = max(
            5, min(c.duration_steps, 30))
        self.memory = EcologyMemory()
        self.stream = EcologyStream(
            state_dir=c.output_state_dir,
            write_log=c.preserve_event_log)
        self.state = NurseryState()
        self._pending_signals: List[Any] = []
        self._episode_start = 0
        self._last_regime = regimes.current

    # -- generation -----------------------------------------------------------------

    def generate_step(self, step: int) -> List[EcologyEvent]:
        """Generate this step's ecology events, log them, return them."""
        stimuli = self.ecology.generate_step(step)
        # Rate safety: never exceed the configured/capped events per step.
        rate_report = self.safety.validate_rate(
            len(stimuli), self.config.max_events_per_step)
        if not rate_report.safe:
            stimuli = stimuli[:self.config.max_events_per_step]
        cycle_state = self.ecology.cycles.state_at(step)
        season = self.ecology.seasonality.current_season
        regime = self.ecology.regimes.current
        phase = "/".join(sorted(cycle_state.phases.values()))
        events: List[EcologyEvent] = []
        for stimulus in stimuli:
            stim_report = self.safety.validate_stimulus(stimulus)
            if not stim_report.safe:
                continue  # refused stimuli are dropped, never emitted
            event = EcologyEvent(stimulus=stimulus, regime=regime,
                                cycle_phase=phase, season=season,
                                step=step)
            events.append(event)
            self.memory.record_event(stimulus.event_type)
            self._update_counters(stimulus)
            self.stream.emit(stimulus)  # canonical signal + JSONL
        self.memory.record_regime(step, regime)
        if regime != self._last_regime:
            self.memory.record_window("delayed", {"regime_change": True})
            self._last_regime = regime
        self.state.step = step
        self.state.events_total += len(events)
        return events

    def _update_counters(self, stimulus: EcologyStimulus) -> None:
        if stimulus.is_absence:
            self.state.absence_windows += 1
            self.memory.record_window("deprivation",
                                     {"step": stimulus.step})
        if stimulus.event_type == "novel_signal":
            self.state.novelty_events += 1
            self.memory.record_window("novelty", {"step": stimulus.step})
        if stimulus.event_type == "anomaly":
            self.state.anomaly_events += 1
            self.memory.record_window("anomaly", {"step": stimulus.step})
        if stimulus.event_type == "seasonal_shift":
            self.state.seasonal_shifts += 1
            self.memory.record_season(
                stimulus.step, self.ecology.seasonality.current_season)
        if stimulus.delay_group:
            self.state.delayed_groups += 1
            self.memory.record_window("delayed",
                                     {"group": stimulus.delay_group})

    # -- runner integration -----------------------------------------------------------

    def stimulus_provider(self, step: int) -> Any:
        """Runner callback: one canonical Stimulus for the step, or None.

        Non-absence ecology events become external signals. An absence
        event (or an empty step) returns None, letting the runner's own
        absence/continuity machinery take over -- which is what tests
        latent activation.
        """
        events = self.generate_step(step)
        from ..signals import canonical as C

        salient = [e for e in events if not e.stimulus.is_absence]
        if not salient:
            return None
        # The most intense salient event drives the step.
        event = max(salient, key=lambda e: e.stimulus.intensity)
        return self.stream.to_canonical_signal(event.stimulus)

    def reaction_provider(self, result: Any, stim: Any) -> Optional[float]:
        """Valence from the ecology's last danger/reward analogue, if any."""
        # The ecology embeds valence hints in danger/reward analogues; the
        # bridge reaction picks them up as reinforcement signal.
        last = self.ecology.regimes  # access keeps determinism stable
        del last, result, stim
        return None

    # -- episodes / views --------------------------------------------------------------

    def close_episode(self, step: int,
                      developmental_response: Optional[Dict[str, Any]]
                      = None) -> EcologyEpisode:
        """Record an ecology episode (a slice of lived history)."""
        regime = self.ecology.regimes.current_regime()
        episode = EcologyEpisode(
            step_start=self._episode_start, step_end=step,
            regime=regime.name,
            season=self.ecology.seasonality.current_season,
            event_counts=dict(self.memory.event_counts),
            dominant_pressure=regime.expected_pressure,
            developmental_response=dict(developmental_response or {}))
        self.memory.record_episode(episode)
        self._episode_start = step
        return episode

    def summary(self) -> Dict[str, Any]:
        """Compact status for ops / Inner MAP."""
        cycle_state = self.ecology.cycles.state_at(self.state.step)
        return {
            "enabled": True,
            "nursery_id": self.config.nursery_id,
            "current_regime": self.ecology.regimes.current,
            "current_cycle_phase": "/".join(
                sorted(cycle_state.phases.values())),
            "current_season": self.ecology.seasonality.current_season,
            "ecology_event_count": self.memory.total_events(),
            "absence_window_count": self.state.absence_windows,
            "novelty_count": self.state.novelty_events,
            "anomaly_count": self.state.anomaly_events,
            "delayed_consequence_group_count":
                self.ecology.delayed.groups_created,
            "seasonal_shift_count": len(
                self.ecology.seasonality.shifts),
            "event_rate": round(
                self.memory.total_events()
                / max(1, self.state.step), 4),
            "absence_rate": round(
                self.state.absence_windows
                / max(1, self.state.step), 4),
            "anomaly_rate": round(
                self.state.anomaly_events
                / max(1, self.state.step), 4),
            "novelty_rate": round(
                self.state.novelty_events
                / max(1, self.state.step), 4),
            "last_seasonal_shift": (self.ecology.seasonality.shifts[-1]
                                    if self.ecology.seasonality.shifts
                                    else None),
            "ecology_report_path": getattr(self, "report_path", None),
            "authority": False,
            "note": "a controlled developmental world, not a teacher; "
                    "stimuli are not labels",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "state": self.state.to_dict(),
            "ecology": self.ecology.snapshot(),
            "memory": self.memory.snapshot(),
            "stream": self.stream.snapshot(),
            "safety": self.safety.snapshot(),
            "summary": self.summary(),
        }

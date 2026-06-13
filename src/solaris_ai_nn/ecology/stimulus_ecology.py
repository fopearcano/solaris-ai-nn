"""StimulusEcology -- the world's physics, one step at a time.

Given the current regime, cycle phase, and season, the ecology decides
what (if anything) the world emits this step: a regular or repeated
signal, a novel one, an anomaly, a danger/reward analogue, a boundary
event, a scheduled delayed consequence, or silence. It is deterministic
with the seed, low-compute, and produces only :class:`EcologyStimulus`
objects -- never labels, commands, or real-world effects.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .anomalies import AnomalyGenerator
from .cycles import CycleManager
from .delayed_consequence import DelayedConsequenceModel
from .deprivation import DeprivationModel
from .events import EcologyEventType, EcologyStimulus
from .novelty import NoveltyGenerator
from .regimes import EcologyRegime, RegimeManager
from .scarcity import ScarcityModel
from .seasonality import SeasonalityModel

# A small fixed alphabet of recurring base patterns the world reuses.
_BASE_PATTERNS = ("pattern_a", "pattern_b", "pattern_c", "pattern_d")


@dataclass
class StimulusEcology:
    """The per-step event generator. Deterministic, bounded, label-free."""

    seed: int = 7
    regimes: RegimeManager = field(default_factory=RegimeManager)
    cycles: CycleManager = field(default_factory=CycleManager)
    seasonality: SeasonalityModel = field(
        default_factory=SeasonalityModel)
    scarcity: ScarcityModel = field(default_factory=ScarcityModel)
    max_events_per_step: int = 3

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)
        self.novelty = NoveltyGenerator(rng=self.rng)
        self.anomalies = AnomalyGenerator(rng=self.rng)
        self.deprivation = DeprivationModel(rng=self.rng)
        self.delayed = DelayedConsequenceModel(rng=self.rng)
        self.events_generated = 0
        self._last_pattern: Optional[str] = None

    # -- the per-step world -----------------------------------------------------------

    def generate_step(self, step: int) -> List[EcologyStimulus]:
        """All ecology stimuli for one step (possibly empty: silence)."""
        cycle_state = self.cycles.update(step)
        season, shifted = self.seasonality.update(step)
        regime = self.regimes.current_regime()
        season_profile = self.seasonality.profile(season)
        freq_mult, int_mult = self.cycles.modulation(cycle_state)
        events: List[EcologyStimulus] = []

        # Seasonal-shift marker (rare, slow).
        if shifted:
            events.append(self._make(
                step, EcologyEventType.SEASONAL_SHIFT, season_profile,
                int_mult, payload=f"season:{season}",
                metadata={"season": season}))

        # 1. Due delayed consequences fire first (cross-time links).
        for record in self.delayed.due_at(step):
            events.append(self._make(
                step, EcologyEventType.DELAYED_CONSEQUENCE,
                season_profile, int_mult,
                payload=record["consequence_type"],
                valence_hint=record["consequence_valence"],
                delay_group=record["group_id"],
                metadata={"resolves": record["kind"]}))

        # 2. Deprivation / silence windows dominate when active.
        depr_kind = self.deprivation.step_window()
        absence_rate = (regime.silence_probability
                        * season_profile["absence_mult"]
                        / max(0.3, freq_mult))
        after_anomaly = bool(self.anomalies.anomalies
                             and self.anomalies.anomalies[-1]["step"]
                             == step - 1)
        if depr_kind is None:
            depr_kind = self.deprivation.maybe_start(
                step, absence_rate, after_anomaly=after_anomaly)
        if depr_kind is not None:
            self.scarcity.observe(had_signal=False, had_reward=False,
                                  expected_signal=True,
                                  in_scarcity_phase=True)
            events.append(self._make(
                step, EcologyEventType.ABSENCE_WINDOW, season_profile,
                int_mult, payload="absence", intensity_override=0.0,
                metadata={"deprivation": depr_kind}))
            return self._cap_and_count(events)

        # 3. A signal arrives (or this is a quiet step).
        emitted_signal = False
        emitted_reward = False
        if self.rng.random() < min(0.95, regime.pattern_recurrence
                                   * freq_mult):
            stimulus, emitted_reward = self._signal_event(
                step, regime, season_profile, int_mult)
            events.append(stimulus)
            emitted_signal = True

        # 4. Novelty (bounded).
        if self.rng.random() < min(0.5, regime.novelty_probability
                                   * season_profile["novelty_mult"]):
            proposal = self.novelty.propose(step)
            if proposal is not None:
                events.append(self._make(
                    step, EcologyEventType.NOVEL_SIGNAL, season_profile,
                    int_mult, payload=proposal["pattern_id"],
                    novelty_hint=1.0,
                    recurrence_id=proposal["pattern_id"]))

        # 5. Anomaly (controlled perturbation, bounded).
        anomaly = self.anomalies.maybe_anomaly(
            step, regime.anomaly_probability,
            established_pattern=self._last_pattern)
        if anomaly is not None:
            events.append(self._make(
                step, EcologyEventType.ANOMALY, season_profile,
                int_mult, payload=anomaly["kind"], novelty_hint=0.9,
                metadata={"anomaly_id": anomaly["anomaly_id"],
                          "is_error": False}))

        # 6. Boundary event.
        if self.rng.random() < min(0.5, regime.boundary_probability):
            events.append(self._make(
                step, EcologyEventType.BOUNDARY_EVENT, season_profile,
                int_mult, payload="boundary"))

        # 7. Maybe schedule a new delayed consequence for later.
        if self.rng.random() < min(0.5,
                                   regime.delayed_consequence_probability):
            delay = int(season_profile["delay_steps"])
            self.delayed.schedule(step, delay=delay)

        # Scarcity bookkeeping for a non-deprived step.
        self.scarcity.observe(
            had_signal=emitted_signal, had_reward=emitted_reward,
            expected_signal=(regime.pattern_recurrence > 0.5),
            in_scarcity_phase=("scarcity" in cycle_state.phases.values()))
        return self._cap_and_count(events)

    # -- helpers --------------------------------------------------------------------

    def _signal_event(self, step: int, regime: EcologyRegime,
                      season_profile: Dict[str, float],
                      int_mult: float,
                      ) -> "tuple[EcologyStimulus, bool]":
        """A regular/repeated/danger/reward signal. Returns (stim, reward?)."""
        roll = self.rng.random()
        danger_p = regime.danger_probability * season_profile[
            "danger_mult"]
        reward_p = regime.reward_probability * season_profile[
            "reward_mult"]
        if roll < danger_p:
            return (self._make(
                step, EcologyEventType.DANGER_ANALOGUE, season_profile,
                int_mult, payload="danger", valence_hint=-0.6), False)
        if roll < danger_p + reward_p:
            return (self._make(
                step, EcologyEventType.REWARD_ANALOGUE, season_profile,
                int_mult, payload="reward", valence_hint=0.7), True)
        # Otherwise a (probably repeated) base pattern.
        pattern = self.rng.choice(_BASE_PATTERNS)
        is_break = (self._last_pattern is not None
                    and self.rng.random() > regime.pattern_recurrence)
        event_type = (EcologyEventType.PATTERN_BREAK if is_break
                      else EcologyEventType.REPEATED_PATTERN)
        self.novelty.observe_recurrence(pattern)
        self._last_pattern = pattern
        return (self._make(
            step, event_type, season_profile, int_mult,
            payload=pattern, recurrence_id=pattern,
            expected_pattern_id=pattern), False)

    def _make(self, step: int, event_type: str,
              season_profile: Dict[str, float], int_mult: float,
              payload: Any = None, intensity_override: float = None,
              valence_hint: Optional[float] = None,
              novelty_hint: Optional[float] = None,
              expected_pattern_id: Optional[str] = None,
              delay_group: Optional[str] = None,
              recurrence_id: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None,
              ) -> EcologyStimulus:
        intensity = (intensity_override if intensity_override is not None
                     else round(min(1.0, (0.3 + 0.5 * self.rng.random())
                                    * int_mult), 4))
        return EcologyStimulus(
            event_type=event_type, modality="ecology", payload=payload,
            intensity=intensity, step=step, valence_hint=valence_hint,
            novelty_hint=novelty_hint,
            expected_pattern_id=expected_pattern_id,
            delay_group=delay_group, recurrence_id=recurrence_id,
            metadata={"season": self.seasonality.current_season,
                      "regime": self.regimes.current,
                      **(metadata or {})})

    def _cap_and_count(self, events: List[EcologyStimulus],
                       ) -> List[EcologyStimulus]:
        capped = events[:self.max_events_per_step]
        self.events_generated += len(capped)
        return capped

    def snapshot(self) -> Dict[str, Any]:
        return {
            "events_generated": self.events_generated,
            "regimes": self.regimes.snapshot(),
            "cycles": self.cycles.snapshot(),
            "seasonality": self.seasonality.snapshot(),
            "scarcity": self.scarcity.snapshot(),
            "novelty": self.novelty.snapshot(),
            "anomalies": self.anomalies.snapshot(),
            "deprivation": self.deprivation.snapshot(),
            "delayed_consequence": self.delayed.snapshot(),
        }

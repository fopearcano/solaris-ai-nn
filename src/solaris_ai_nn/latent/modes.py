"""Latent modes -- the sleep/wake state machine. Bounded, logged, honest.

The controller tracks which processing mode the substrate is in. "Sleep" and
"dream" are engineering names for bounded offline maintenance and sandboxed
replay -- not human sleep, not subjective dreaming. The hard rule is encoded
here once: latent modes (sleep / consolidation / replay / dream) can never
execute external actions, and every transition is recorded with its reason.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LatentMode:
    AWAKE = "awake"
    QUIET = "quiet"
    SLEEP = "sleep"
    DREAM = "dream"
    CONSOLIDATION = "consolidation"
    REPLAY = "replay"
    WAKE_TRANSITION = "wake_transition"

    ALL = (AWAKE, QUIET, SLEEP, DREAM, CONSOLIDATION, REPLAY, WAKE_TRANSITION)
    # Modes in which external action execution is forbidden, absolutely.
    ACTION_BLOCKED = frozenset({SLEEP, DREAM, CONSOLIDATION, REPLAY,
                                WAKE_TRANSITION})
    # Modes that count as latent processing.
    LATENT = frozenset({SLEEP, DREAM, CONSOLIDATION, REPLAY})


# Which transitions are legal. Anything else is rejected (never silently).
VALID_TRANSITIONS: Dict[str, frozenset] = {
    LatentMode.AWAKE: frozenset({LatentMode.QUIET, LatentMode.SLEEP}),
    LatentMode.QUIET: frozenset({LatentMode.AWAKE, LatentMode.SLEEP}),
    LatentMode.SLEEP: frozenset({LatentMode.CONSOLIDATION, LatentMode.REPLAY,
                                 LatentMode.DREAM,
                                 LatentMode.WAKE_TRANSITION}),
    LatentMode.CONSOLIDATION: frozenset({LatentMode.SLEEP, LatentMode.REPLAY,
                                         LatentMode.WAKE_TRANSITION}),
    LatentMode.REPLAY: frozenset({LatentMode.SLEEP, LatentMode.DREAM,
                                  LatentMode.CONSOLIDATION,
                                  LatentMode.WAKE_TRANSITION}),
    LatentMode.DREAM: frozenset({LatentMode.SLEEP,
                                 LatentMode.WAKE_TRANSITION}),
    LatentMode.WAKE_TRANSITION: frozenset({LatentMode.AWAKE}),
}


@dataclass
class LatentTransition:
    """One recorded mode change."""

    from_mode: str
    to_mode: str
    reason: str
    step: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LatentModeState:
    """Everything the controller knows about the current mode."""

    mode: str = LatentMode.AWAKE
    previous_mode: Optional[str] = None
    transition_reason: str = "initial"
    external_input_rate: float = 0.0
    silence_duration: int = 0
    energy_proxy: float = 1.0   # crude: substrate activity headroom [0,1]
    fatigue_proxy: float = 0.0  # crude: time-since-consolidation pressure [0,1]
    last_stimulus_ts: float = 0.0
    last_action_ts: float = 0.0
    last_consolidation_ts: float = 0.0
    last_replay_ts: float = 0.0
    mode_entered_at: float = field(default_factory=time.time)
    mode_entered_step: int = 0

    def mode_duration_s(self) -> float:
        return max(0.0, time.time() - self.mode_entered_at)

    def to_dict(self) -> Dict[str, Any]:
        return {**self.__dict__, "mode_duration_s": self.mode_duration_s()}


@dataclass
class SleepWakeController:
    """Owns the mode state machine; validates and logs every transition."""

    state: LatentModeState = field(default_factory=LatentModeState)
    max_history: int = 200
    history: List[LatentTransition] = field(default_factory=list)
    last_wake_summary: Optional[Dict[str, Any]] = field(default=None,
                                                        init=False)
    counts: Dict[str, int] = field(default_factory=dict, init=False)

    # -- queries -------------------------------------------------------------

    @property
    def mode(self) -> str:
        return self.state.mode

    def is_latent(self) -> bool:
        return self.state.mode in LatentMode.LATENT

    def can_execute_external_actions(self) -> bool:
        """The one rule that matters: only awake/quiet may act outward."""
        return self.state.mode not in LatentMode.ACTION_BLOCKED

    def can_transition(self, to_mode: str) -> bool:
        return to_mode in VALID_TRANSITIONS.get(self.state.mode, frozenset())

    # -- transitions -----------------------------------------------------------

    def transition(self, to_mode: str, reason: str,
                   step: int = 0) -> LatentTransition:
        """Move to ``to_mode``; raises on an illegal transition."""
        if to_mode not in LatentMode.ALL:
            raise ValueError(f"unknown latent mode {to_mode!r}")
        if not self.can_transition(to_mode):
            raise ValueError(
                f"illegal transition {self.state.mode!r} -> {to_mode!r} "
                f"(allowed: {sorted(VALID_TRANSITIONS[self.state.mode])})")
        transition = LatentTransition(
            from_mode=self.state.mode, to_mode=to_mode, reason=reason,
            step=step)
        self.state.previous_mode = self.state.mode
        self.state.mode = to_mode
        self.state.transition_reason = reason
        self.state.mode_entered_at = time.time()
        self.state.mode_entered_step = step
        self.history.append(transition)
        self.history = self.history[-self.max_history:]
        self.counts[to_mode] = self.counts.get(to_mode, 0) + 1
        return transition

    def wake(self, summary: Dict[str, Any], reason: str = "latent cycle "
             "complete", step: int = 0) -> List[LatentTransition]:
        """Latent mode -> wake_transition (with summary) -> awake."""
        transitions = []
        if self.state.mode in LatentMode.LATENT:
            transitions.append(self.transition(LatentMode.WAKE_TRANSITION,
                                               reason, step))
        if self.state.mode == LatentMode.WAKE_TRANSITION:
            self.last_wake_summary = {"reason": reason, "step": step,
                                      **summary}
            transitions.append(self.transition(LatentMode.AWAKE,
                                               "wake transition complete",
                                               step))
        return transitions

    # -- bookkeeping -------------------------------------------------------------

    def note_stimulus(self, ts: Optional[float] = None) -> None:
        self.state.last_stimulus_ts = ts if ts is not None else time.time()
        self.state.silence_duration = 0

    def note_silence(self) -> None:
        self.state.silence_duration += 1

    def note_action(self, ts: Optional[float] = None) -> None:
        self.state.last_action_ts = ts if ts is not None else time.time()

    def note_consolidation(self) -> None:
        self.state.last_consolidation_ts = time.time()
        self.state.fatigue_proxy = 0.0

    def note_replay(self) -> None:
        self.state.last_replay_ts = time.time()

    def update_proxies(self, input_rate: float, activity_norm: float,
                       steps_since_consolidation: int) -> None:
        """Refresh the crude energy/fatigue proxies (plain numbers, no claim)."""
        self.state.external_input_rate = max(0.0, float(input_rate))
        self.state.energy_proxy = max(0.0, min(
            1.0, 1.0 - activity_norm / 20.0))
        self.state.fatigue_proxy = max(0.0, min(
            1.0, steps_since_consolidation / 500.0))

    def snapshot(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "mode_counts": dict(self.counts),
            "recent_transitions": [t.to_dict() for t in self.history[-10:]],
            "last_wake_summary": self.last_wake_summary,
            "can_execute_external_actions":
                self.can_execute_external_actions(),
        }

"""LatentScheduler -- decides when latent processing is allowed to happen.

The scheduler turns telemetry, silence, memory pressure, unknown pressure,
and operational constraints into one bounded decision at a time. It never
starts an infinite cycle (every decision carries a max_steps bound), refuses
when governance disallows latent processing, and refuses when health is
critical -- a struggling system gets supervision, not introspection.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .modes import LatentMode, SleepWakeController
from .safety import MAX_LATENT_CYCLE_STEPS, LatentSafetyValidator


class LatentDecision:
    CONTINUE_AWAKE = "continue_awake"
    ENTER_QUIET = "enter_quiet"
    ENTER_SLEEP = "enter_sleep"
    ENTER_CONSOLIDATION = "enter_consolidation"
    ENTER_REPLAY = "enter_replay"
    ENTER_DREAM = "enter_dream"
    WAKE = "wake"
    REFUSE_DUE_TO_POLICY = "refuse_due_to_policy"
    REFUSE_DUE_TO_HEALTH = "refuse_due_to_health"

    ALL = (CONTINUE_AWAKE, ENTER_QUIET, ENTER_SLEEP, ENTER_CONSOLIDATION,
           ENTER_REPLAY, ENTER_DREAM, WAKE, REFUSE_DUE_TO_POLICY,
           REFUSE_DUE_TO_HEALTH)


@dataclass
class LatentScheduleDecision:
    """One bounded scheduling decision."""

    decision: str
    reason: str = ""
    max_steps: int = 0  # the bound for any cycle this decision starts
    target_mode: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LatentScheduler:
    """Bounded, policy- and health-respecting latent scheduling."""

    controller: SleepWakeController = field(
        default_factory=SleepWakeController)
    safety: LatentSafetyValidator = field(
        default_factory=LatentSafetyValidator)
    quiet_after_silence: int = 5
    sleep_after_silence: int = 12
    consolidation_min_trace: int = 30
    replay_min_trace: int = 20
    dream_unknown_pressure: float = 0.5
    default_cycle_steps: int = 25
    max_cycle_steps: int = MAX_LATENT_CYCLE_STEPS

    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- the decision -----------------------------------------------------------

    def evaluate(self, context: Optional[Dict[str, Any]] = None,
                 ) -> LatentScheduleDecision:
        ctx = context or {}
        bound = self._bound(ctx)

        # Hard refusals first: health, then policy.
        if str(ctx.get("health_level", "ok")) == "critical":
            return self._record(LatentScheduleDecision(
                LatentDecision.REFUSE_DUE_TO_HEALTH,
                "health is critical; supervision takes priority over "
                "latent processing"))
        if not bool(ctx.get("governance_allows_latent", True)):
            return self._record(LatentScheduleDecision(
                LatentDecision.REFUSE_DUE_TO_POLICY,
                "governance does not permit latent cycles for this run"))
        if ctx.get("sidecar_publishing_active"):
            return self._record(LatentScheduleDecision(
                LatentDecision.REFUSE_DUE_TO_POLICY,
                "latent cycles are forbidden while sidecar publishing is "
                "active"))
        if ctx.get("watchdog_stop_requested") \
                or ctx.get("shutdown_requested"):
            decision = (LatentDecision.WAKE if self.controller.is_latent()
                        else LatentDecision.CONTINUE_AWAKE)
            return self._record(LatentScheduleDecision(
                decision, "a stop was requested; no new latent work"))

        # Currently latent? Decide whether it is time to wake.
        if self.controller.is_latent():
            if self.should_wake(ctx):
                return self._record(LatentScheduleDecision(
                    LatentDecision.WAKE,
                    "input resumed or the latent budget is spent",
                    target_mode=LatentMode.AWAKE))
            if self.should_enter_consolidation(ctx):
                return self._record(LatentScheduleDecision(
                    LatentDecision.ENTER_CONSOLIDATION,
                    "trace is large and unconsolidated", bound,
                    LatentMode.CONSOLIDATION))
            if self.should_enter_replay(ctx):
                return self._record(LatentScheduleDecision(
                    LatentDecision.ENTER_REPLAY,
                    "replay due (enough trace, replay budget available)",
                    bound, LatentMode.REPLAY))
            if self._dream_due(ctx):
                return self._record(LatentScheduleDecision(
                    LatentDecision.ENTER_DREAM,
                    "unknown pressure is elevated; counterfactual replay "
                    "may localize it", bound, LatentMode.DREAM))
            return self._record(LatentScheduleDecision(
                LatentDecision.WAKE, "nothing latent left to do",
                target_mode=LatentMode.AWAKE))

        # Awake/quiet: is it time to go latent at all?
        silence = int(ctx.get("silence_duration",
                              self.controller.state.silence_duration) or 0)
        if self.should_enter_sleep(ctx):
            return self._record(LatentScheduleDecision(
                LatentDecision.ENTER_SLEEP,
                f"external silence for {silence} steps", bound,
                LatentMode.SLEEP))
        if silence >= self.quiet_after_silence \
                and self.controller.mode == LatentMode.AWAKE:
            return self._record(LatentScheduleDecision(
                LatentDecision.ENTER_QUIET,
                f"input rate is low (silence {silence})",
                target_mode=LatentMode.QUIET))
        return self._record(LatentScheduleDecision(
            LatentDecision.CONTINUE_AWAKE, "normal input is flowing"))

    # -- the individual questions -------------------------------------------------

    def should_enter_sleep(self, context: Dict[str, Any]) -> bool:
        silence = int(context.get("silence_duration",
                                  self.controller.state.silence_duration)
                      or 0)
        return (silence >= self.sleep_after_silence
                and self.controller.mode in (LatentMode.AWAKE,
                                             LatentMode.QUIET))

    def should_enter_consolidation(self, context: Dict[str, Any]) -> bool:
        trace_length = int(context.get("trace_length", 0) or 0)
        consolidated_recently = bool(context.get("consolidated_recently",
                                                 False))
        return (trace_length >= self.consolidation_min_trace
                and not consolidated_recently
                and self.controller.can_transition(LatentMode.CONSOLIDATION))

    def should_enter_replay(self, context: Dict[str, Any]) -> bool:
        trace_length = int(context.get("trace_length", 0) or 0)
        replayed_recently = bool(context.get("replayed_recently", False))
        return (trace_length >= self.replay_min_trace
                and not replayed_recently
                and self.controller.can_transition(LatentMode.REPLAY))

    def _dream_due(self, context: Dict[str, Any]) -> bool:
        pressure = float(context.get("unknown_pressure", 0.0) or 0.0)
        return (pressure >= self.dream_unknown_pressure
                and bool(context.get("dream_allowed", True))
                and self.controller.can_transition(LatentMode.DREAM))

    def should_wake(self, context: Dict[str, Any]) -> bool:
        if context.get("input_resumed") or context.get("stimulus_pending"):
            return True
        budget = int(context.get("latent_steps_remaining", 1) or 0)
        return budget <= 0

    # -- helpers ---------------------------------------------------------------------

    def _bound(self, context: Dict[str, Any]) -> int:
        requested = int(context.get("latent_max_steps",
                                    self.default_cycle_steps) or
                        self.default_cycle_steps)
        return max(1, min(requested, self.max_cycle_steps))

    def _record(self, decision: LatentScheduleDecision,
                ) -> LatentScheduleDecision:
        self.decisions.append(decision.to_dict())
        self.decisions = self.decisions[-100:]
        return decision

    def snapshot(self) -> Dict[str, Any]:
        return {
            "mode": self.controller.mode,
            "thresholds": {
                "quiet_after_silence": self.quiet_after_silence,
                "sleep_after_silence": self.sleep_after_silence,
                "dream_unknown_pressure": self.dream_unknown_pressure,
                "max_cycle_steps": self.max_cycle_steps,
            },
            "recent_decisions": self.decisions[-8:],
        }

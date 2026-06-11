"""Perspective model -- where the system is looking *from*, operationally.

Eight perspective modes, each carrying two structural facts: whether
actions are allowed from that perspective (and at what scope), and what the
evidence produced under it counts as (observed, simulated, counterfactual,
inferred, unknown). Shifts are recorded with reasons; a perspective is a
recorded operating mode, not a point of view in any experiential sense.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PerspectiveMode:
    INTERNAL_RUNTIME = "internal_runtime"
    EMBODIED_SIMULATION = "embodied_simulation"
    READ_ONLY_STREAM_OBSERVER = "read_only_stream_observer"
    SOLARIS_SIDECAR_OBSERVER = "solaris_sidecar_observer"
    LATENT_OFFLINE_REPLAY = "latent_offline_replay"
    COUNTERFACTUAL_SIMULATION = "counterfactual_simulation"
    BENCHMARK_EVALUATION = "benchmark_evaluation"
    OPERATOR_REVIEW = "operator_review"

    ALL = (INTERNAL_RUNTIME, EMBODIED_SIMULATION,
           READ_ONLY_STREAM_OBSERVER, SOLARIS_SIDECAR_OBSERVER,
           LATENT_OFFLINE_REPLAY, COUNTERFACTUAL_SIMULATION,
           BENCHMARK_EVALUATION, OPERATOR_REVIEW)


# mode -> (actions_allowed, action_scope, evidence_status)
MODE_PROPERTIES: Dict[str, "tuple[bool, str, str]"] = {
    PerspectiveMode.INTERNAL_RUNTIME: (True, "internal_maintenance",
                                       "observed"),
    PerspectiveMode.EMBODIED_SIMULATION: (True, "simulation_only",
                                          "simulated"),
    PerspectiveMode.READ_ONLY_STREAM_OBSERVER: (False, "none", "observed"),
    PerspectiveMode.SOLARIS_SIDECAR_OBSERVER: (False, "none", "observed"),
    PerspectiveMode.LATENT_OFFLINE_REPLAY: (False, "none", "simulated"),
    PerspectiveMode.COUNTERFACTUAL_SIMULATION: (False, "none",
                                                "counterfactual"),
    PerspectiveMode.BENCHMARK_EVALUATION: (True, "simulation_only",
                                           "observed"),
    PerspectiveMode.OPERATOR_REVIEW: (False, "none", "observed"),
}


@dataclass
class PerspectiveState:
    """The current perspective and its structural properties."""

    mode: str = PerspectiveMode.INTERNAL_RUNTIME
    previous_mode: str = ""
    reason: str = "initial perspective"
    since: float = field(default_factory=time.time)
    actions_allowed: bool = True
    action_scope: str = "internal_maintenance"
    evidence_status: str = "observed"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PerspectiveTracker:
    """Tracks the perspective, its shifts, and their reasons."""

    state: PerspectiveState = field(default_factory=PerspectiveState)
    shifts: List[Dict[str, Any]] = field(default_factory=list)
    shift_count: int = field(default=0, init=False)

    def set_perspective(self, mode: str, reason: str = "",
                        ) -> PerspectiveState:
        if mode not in PerspectiveMode.ALL:
            raise ValueError(f"unknown perspective mode {mode!r}")
        if mode == self.state.mode:
            return self.state
        allowed, scope, evidence = MODE_PROPERTIES[mode]
        previous = self.state.mode
        self.state = PerspectiveState(
            mode=mode, previous_mode=previous,
            reason=reason or "unspecified shift",
            actions_allowed=allowed, action_scope=scope,
            evidence_status=evidence)
        self.shift_count += 1
        self.shifts.append({"from": previous, "to": mode,
                            "reason": self.state.reason,
                            "at": self.state.since})
        self.shifts = self.shifts[-50:]
        return self.state

    def infer_from_context(self, context: Optional[Dict[str, Any]] = None,
                           ) -> PerspectiveState:
        """Deterministic perspective from running-context flags."""
        ctx = dict(context or {})
        latent = str(ctx.get("latent_mode", "awake"))
        if ctx.get("counterfactual_active") or latent == "dream":
            return self.set_perspective(
                PerspectiveMode.COUNTERFACTUAL_SIMULATION,
                f"counterfactual/dream processing active "
                f"(latent_mode={latent!r})")
        if latent in ("sleep", "replay", "consolidation"):
            return self.set_perspective(
                PerspectiveMode.LATENT_OFFLINE_REPLAY,
                f"latent offline processing (latent_mode={latent!r})")
        if ctx.get("operator_review_active"):
            return self.set_perspective(PerspectiveMode.OPERATOR_REVIEW,
                                        "operator review in progress")
        if ctx.get("benchmark_active"):
            return self.set_perspective(PerspectiveMode.BENCHMARK_EVALUATION,
                                        "benchmark evaluation running")
        if ctx.get("embodied"):
            return self.set_perspective(PerspectiveMode.EMBODIED_SIMULATION,
                                        "embodied GridWorld simulation")
        if ctx.get("stream_active"):
            return self.set_perspective(
                PerspectiveMode.READ_ONLY_STREAM_OBSERVER,
                "read-only stream ingestion active")
        if ctx.get("sidecar_attached"):
            return self.set_perspective(
                PerspectiveMode.SOLARIS_SIDECAR_OBSERVER,
                "Solaris_Ai sidecar attached, observe-only")
        return self.set_perspective(PerspectiveMode.INTERNAL_RUNTIME,
                                    "default internal runtime")

    # -- views --------------------------------------------------------------------

    def actions_allowed(self) -> bool:
        return self.state.actions_allowed

    def evidence_status(self) -> str:
        return self.state.evidence_status

    def stuck_duration_s(self) -> float:
        return round(time.time() - self.state.since, 3)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "current": self.state.to_dict(),
            "shift_count": self.shift_count,
            "recent_shifts": self.shifts[-5:],
            "stuck_duration_s": self.stuck_duration_s(),
            "note": ("a perspective is a recorded operating mode, not a "
                     "point of view in any experiential sense"),
        }

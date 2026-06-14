"""Conscience spine -- the canonical orchestration order of one step.

The :class:`ConscienceSpine` defines the phase order that preserves the
Solaris spine: Stimulus -> Push -> Desire -> ActionCandidate -> (executive +
safety) -> ActionSuggestion -> Reaction -> Memory/World Model/Inner MAP.
Every phase is optional/configurable, a missing module is *skipped* with a
clear status (never a crash), and every phase emits a trace event. This is an
orchestration spine, not a metaphysical claim.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class SpinePhase:
    HEARTBEAT = "heartbeat"
    READ_ONLY_SENSORY_POLL = "read_only_sensory_poll"
    STIMULUS_INGESTION = "stimulus_ingestion"
    PUSH_GENERATION = "push_generation"
    DESIRE_SYNTHESIS = "desire_synthesis"
    ACTION_CANDIDATE_GENERATION = "action_candidate_generation"
    EXECUTIVE_ARBITRATION = "executive_arbitration"
    SAFETY_GOVERNANCE_VALIDATION = "safety_governance_validation"
    MOTOR_ACTION_FIREWALL = "motor_action_firewall"
    ACTION_SUGGESTION = "action_suggestion"
    REACTION_COLLECTION = "reaction_collection"
    MEMORY_UPDATE = "memory_update"
    WORLD_MODEL_UPDATE = "world_model_update"
    PROTO_LANGUAGE_UPDATE = "proto_language_update"
    HYPOTHESIS_UPDATE = "hypothesis_update"
    LOGOS_SCAN = "logos_scan"
    AUTOREGENERATION_SCAN = "autoregeneration_scan"
    INNER_MAP_UPDATE = "inner_map_update"
    TELEMETRY_CHECKPOINT = "telemetry_checkpoint"
    LATENT_OR_CONSOLIDATION_WINDOW = "latent_or_consolidation_window"

    # The canonical order in which phases run each step.
    ORDER = (HEARTBEAT, READ_ONLY_SENSORY_POLL,
             STIMULUS_INGESTION, PUSH_GENERATION, DESIRE_SYNTHESIS,
             ACTION_CANDIDATE_GENERATION, EXECUTIVE_ARBITRATION,
             SAFETY_GOVERNANCE_VALIDATION, MOTOR_ACTION_FIREWALL,
             ACTION_SUGGESTION,
             REACTION_COLLECTION, MEMORY_UPDATE, WORLD_MODEL_UPDATE,
             PROTO_LANGUAGE_UPDATE, HYPOTHESIS_UPDATE, LOGOS_SCAN,
             AUTOREGENERATION_SCAN, INNER_MAP_UPDATE, TELEMETRY_CHECKPOINT,
             LATENT_OR_CONSOLIDATION_WINDOW)
    ALL = ORDER


class PhaseStatus:
    RAN = "ran"
    SKIPPED = "skipped"
    DEGRADED = "degraded"
    SKIPPED_CADENCE = "skipped_cadence"

    ALL = (RAN, SKIPPED, DEGRADED, SKIPPED_CADENCE)


@dataclass
class SpineEvent:
    """One trace event from running (or skipping) a phase."""

    phase: str
    status: str
    step: int = 0
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SpineTrace:
    """A bounded record of phase events and per-phase status counts."""

    events: List[SpineEvent] = field(default_factory=list)
    phase_counts: Dict[str, int] = field(default_factory=dict)
    status_counts: Dict[str, int] = field(default_factory=dict)

    def record(self, event: SpineEvent) -> None:
        self.events.append(event)
        self.events = self.events[-2000:]
        if event.status == PhaseStatus.RAN:
            self.phase_counts[event.phase] = (
                self.phase_counts.get(event.phase, 0) + 1)
        self.status_counts[event.status] = (
            self.status_counts.get(event.status, 0) + 1)

    def to_dict(self) -> Dict[str, Any]:
        return {"phase_counts": dict(self.phase_counts),
                "status_counts": dict(self.status_counts),
                "recent": [e.to_dict() for e in self.events[-8:]]}


@dataclass
class ConscienceSpine:
    """Runs the canonical phase order; missing phases are skipped safely."""

    trace: SpineTrace = field(default_factory=SpineTrace)
    last_phase: Optional[str] = field(default=None, init=False)

    def run_step(self, step: int,
                 handlers: Dict[str, Callable[[int], Any]],
                 enabled: Optional[Dict[str, bool]] = None) -> SpineTrace:
        """Run each phase in order; ``handlers`` maps phase -> callable.

        A handler returns a PhaseStatus string (or None -> ran). A missing
        handler is skipped. A raising handler is recorded as degraded, never
        propagated.
        """
        enabled = enabled or {}
        for phase in SpinePhase.ORDER:
            if enabled.get(phase) is False:
                self._emit(phase, PhaseStatus.SKIPPED, step, "disabled")
                continue
            handler = handlers.get(phase)
            if handler is None:
                self._emit(phase, PhaseStatus.SKIPPED, step,
                           "no module/handler")
                continue
            try:
                result = handler(step)
            except Exception as exc:  # never crash the spine
                self._emit(phase, PhaseStatus.DEGRADED, step,
                           f"handler error: {exc}")
                continue
            status = (result if result in PhaseStatus.ALL
                      else PhaseStatus.RAN)
            detail = "" if result in PhaseStatus.ALL else str(result or "")
            self._emit(phase, status, step, detail[:120])
            self.last_phase = phase
        return self.trace

    def _emit(self, phase: str, status: str, step: int, detail: str) -> None:
        self.trace.record(SpineEvent(phase=phase, status=status, step=step,
                                     detail=detail))

    def snapshot(self) -> Dict[str, Any]:
        return {"last_phase": self.last_phase, **self.trace.to_dict()}

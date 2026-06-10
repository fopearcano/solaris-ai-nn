"""SleepCycle -- bounded maintenance while nothing is happening outside.

"Sleep" here means: external actions paused, heartbeat continuing, the trace
consolidated into schemas, high activity allowed to settle, and a written
account at the end. Not human sleep -- a maintenance window.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..memory.consolidation import MemoryConsolidator
from .latent_memory import (
    ConsolidatedSchema,
    LatentMemoryRecord,
    LatentMemoryStore,
)
from .safety import LatentSafetyValidator


@dataclass
class SleepCycleResult:
    """What one sleep cycle actually did."""

    steps_run: int = 0
    external_actions_executed: int = 0  # structurally zero
    consolidation: Dict[str, Any] = field(default_factory=dict)
    schemas_created: int = 0
    schema_summaries: List[str] = field(default_factory=list)
    activity_before: float = 0.0
    activity_after: float = 0.0
    stabilized: bool = False
    offline: bool = True
    duration_s: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SleepCycle:
    """Bounded consolidation/maintenance over the bridge's own trace."""

    bridge: Any  # SolarisNeuralBridge
    store: Optional[LatentMemoryStore] = None
    safety: LatentSafetyValidator = field(
        default_factory=LatentSafetyValidator)
    consolidator: MemoryConsolidator = field(
        default_factory=MemoryConsolidator)
    stabilize_above_norm: float = 5.0
    stabilize_factor: float = 0.95

    cycles_run: int = field(default=0, init=False)
    last_result: Optional[SleepCycleResult] = field(default=None, init=False)

    def run(self, max_steps: int,
            context: Optional[Dict[str, Any]] = None) -> SleepCycleResult:
        """One bounded sleep cycle; never loops past ``max_steps``."""
        if not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError("a sleep cycle requires a positive bounded "
                             "max_steps")
        ctx = context or {}
        started = time.time()
        result = SleepCycleResult(
            activity_before=self.bridge.substrate_state_norm())

        # 1. Consolidate the trace into a report + schemas.
        report = self.consolidator.consolidate(self.bridge.trace)
        result.consolidation = report.to_dict()
        for schema in self._schemas_from_habits():
            if self.store is not None:
                self.store.upsert_schema(schema)
            result.schemas_created += 1
            result.schema_summaries.append(schema.summary())

        # 2. Maintenance ticks: heartbeat continues; high activity settles.
        #    No external input is processed and no action is executed --
        #    there is simply no code path for either in this loop.
        for _ in range(max_steps):
            result.steps_run += 1
            self.bridge.telemetry.heartbeat()
            norm = self.bridge.substrate_state_norm()
            if norm > self.stabilize_above_norm:
                state = [float(x) * self.stabilize_factor
                         for x in self.bridge.substrate.get_state()]
                self.bridge.substrate.set_state(state)
                result.stabilized = True
            elif result.stabilized:
                break  # settled: no reason to burn the remaining budget

        result.activity_after = self.bridge.substrate_state_norm()
        result.duration_s = round(time.time() - started, 6)
        self.cycles_run += 1
        self.last_result = result

        if self.store is not None:
            self.store.record_cycle(LatentMemoryRecord(
                cycle_type="sleep", steps_run=result.steps_run,
                substrate_response={
                    "activity_before": result.activity_before,
                    "activity_after": result.activity_after,
                    "stabilized": result.stabilized},
                schema_summaries=result.schema_summaries,
                production_mutated=result.stabilized,  # state settle only
                mysterium_change=-0.04 if result.schemas_created else 0.0))
        return result

    def _schemas_from_habits(self, top: int = 5) -> List[ConsolidatedSchema]:
        """Distil the strongest habit pathways into consolidated schemas."""
        habit = self.bridge.habit
        ranked = sorted(habit.weights.items(), key=lambda kv: abs(kv[1]),
                        reverse=True)[:top]
        schemas = []
        for (pattern, action), weight in ranked:
            count = habit.counts.get((pattern, action), 0)
            if count < 2:
                continue  # one-off pairings are not schemas yet
            schemas.append(ConsolidatedSchema(
                pattern=str(pattern), dominant_action=str(action),
                support_count=int(count),
                average_valence=round(float(weight), 4)))
        return schemas

    def snapshot(self) -> Dict[str, Any]:
        return {
            "cycles_run": self.cycles_run,
            "last_result": (self.last_result.to_dict()
                            if self.last_result else None),
            "external_actions_executed": 0,  # structurally
        }

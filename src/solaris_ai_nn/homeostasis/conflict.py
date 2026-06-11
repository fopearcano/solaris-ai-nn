"""Need conflicts -- detected, scored, and resolved by fixed priority.

When needs pull in opposite directions (curiosity vs safety, reward approach
vs exhaustion, consolidation vs sensing, ...), the resolver picks the safe
side using a fixed priority ladder -- governance/safety first, exploration
last -- and records exactly which desire proposals were suppressed and why.
Nothing is silently dropped.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .needs import NeedState, NeedType

# The fixed resolution ladder (lower index wins).
RESOLUTION_PRIORITY = (
    "governance_safety",
    "emergency_stop",
    "continuity_health",
    "embodiment_safety",
    "energy_exhaustion",
    "need_intensity",
    "exploration_curiosity",
)


@dataclass
class NeedConflict:
    """One detected opposition between needs (or a need and a constraint)."""

    kind: str
    parties: List[str]
    winner: str
    suppressed: List[str] = field(default_factory=list)
    suppressed_desires: List[str] = field(default_factory=list)
    severity: float = 0.0
    resolution_rule: str = ""
    reason: str = ""
    conflict_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ConflictResolver:
    """Detects and resolves need conflicts; keeps the suppression record."""

    resolved_total: int = field(default=0, init=False)
    history: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def resolve(self, need_state: NeedState,
                context: Optional[Dict[str, Any]] = None,
                ) -> List[NeedConflict]:
        ctx = context or {}
        conflicts: List[NeedConflict] = []
        get = need_state.by_type

        def both(a: str, b: str) -> bool:
            need_a, need_b = get(a), get(b)
            return (need_a is not None and need_b is not None
                    and need_a.intensity > 0.1 and need_b.intensity > 0.1)

        # 1. Curiosity/exploration vs safety: safety wins, always.
        for curious in (NeedType.REDUCE_UNCERTAINTY,
                        NeedType.INCREASE_EXPLORATION):
            for safe in (NeedType.AVOID_DANGER, NeedType.RESPECT_BOUNDARY):
                if both(curious, safe):
                    conflicts.append(self._suppress(
                        kind="curiosity_vs_safety",
                        parties=[curious, safe], winner=safe,
                        loser=get(curious),
                        rule="governance_safety",
                        reason="safety pressure outranks curiosity on the "
                               "fixed priority ladder"))

        # 2. Reward approach vs energy/exhaustion: energy wins when low.
        reward = get(NeedType.APPROACH_REWARD)
        energy = get(NeedType.RESTORE_ENERGY)
        if reward is not None and energy is not None \
                and (energy.intensity >= 0.5
                     or "exhaustion" in reward.inhibited_by):
            conflicts.append(self._suppress(
                kind="energy_vs_reward",
                parties=[NeedType.RESTORE_ENERGY, NeedType.APPROACH_REWARD],
                winner=NeedType.RESTORE_ENERGY, loser=reward,
                rule="energy_exhaustion",
                reason="energy restoration outranks reward approach under "
                       "exhaustion"))

        # 3. Consolidation vs active sensing: higher intensity wins.
        if both(NeedType.CONSOLIDATE_MEMORY, NeedType.SEEK_SIGNAL):
            consolidate = get(NeedType.CONSOLIDATE_MEMORY)
            seek = get(NeedType.SEEK_SIGNAL)
            winner, loser = ((consolidate, seek)
                             if consolidate.intensity >= seek.intensity
                             else (seek, consolidate))
            conflicts.append(self._suppress(
                kind="consolidation_vs_sensing",
                parties=[consolidate.type, seek.type], winner=winner.type,
                loser=loser, rule="need_intensity",
                reason=f"{winner.type} carries the higher intensity "
                       f"({winner.intensity} vs {loser.intensity})"))

        # 4. Exploration vs stabilization: stabilization wins ties.
        if both(NeedType.INCREASE_EXPLORATION,
                NeedType.INCREASE_STABILIZATION):
            explore = get(NeedType.INCREASE_EXPLORATION)
            stabilize = get(NeedType.INCREASE_STABILIZATION)
            if explore.intensity > stabilize.intensity + 0.2:
                winner, loser = explore, stabilize
                rule = "need_intensity"
                reason = "exploration pressure clearly dominates"
            else:
                winner, loser = stabilize, explore
                rule = "exploration_curiosity"
                reason = ("stabilization wins ties: exploration is the "
                          "lowest rung of the priority ladder")
            conflicts.append(self._suppress(
                kind="exploration_vs_stabilization",
                parties=[explore.type, stabilize.type], winner=winner.type,
                loser=loser, rule=rule, reason=reason))

        # 5. Sidecar publishing vs observe-only governance.
        observe = get(NeedType.REMAIN_OBSERVE_ONLY)
        if observe is not None and ctx.get("publish_suggestion_desired"):
            conflicts.append(NeedConflict(
                kind="publish_vs_observe_only",
                parties=["publish_suggestions",
                         NeedType.REMAIN_OBSERVE_ONLY],
                winner=NeedType.REMAIN_OBSERVE_ONLY,
                suppressed=["publish_suggestions"],
                suppressed_desires=["publish_suggestions"],
                severity=0.8, resolution_rule="governance_safety",
                reason="observe-only governance outranks any publishing "
                       "pressure"))

        # 6. Continuity vs safe shutdown: a requested stop wins.
        continuity = get(NeedType.MAINTAIN_CONTINUITY)
        if continuity is not None and (ctx.get("safe_shutdown_requested")
                                       or ctx.get("emergency_stop")):
            conflicts.append(self._suppress(
                kind="continuity_vs_shutdown",
                parties=[NeedType.MAINTAIN_CONTINUITY, "safe_shutdown"],
                winner="safe_shutdown", loser=continuity,
                rule="emergency_stop",
                reason="a requested stop outranks the continuity need; "
                       "dying well is part of continuity"))

        # 7. Plasticity vs stability (context-driven).
        if ctx.get("plasticity_proposed") \
                and get(NeedType.INCREASE_STABILIZATION) is not None:
            conflicts.append(NeedConflict(
                kind="plasticity_vs_stability",
                parties=["plasticity", NeedType.INCREASE_STABILIZATION],
                winner=NeedType.INCREASE_STABILIZATION,
                suppressed=["plasticity"], suppressed_desires=[],
                severity=0.5, resolution_rule="continuity_health",
                reason="stabilization pressure defers parameter mutation"))

        self.resolved_total += len(conflicts)
        for conflict in conflicts:
            self.history.append(conflict.to_dict())
        self.history = self.history[-100:]
        return conflicts

    @staticmethod
    def _suppress(kind: str, parties: List[str], winner: str, loser: Any,
                  rule: str, reason: str) -> NeedConflict:
        return NeedConflict(
            kind=kind, parties=parties, winner=winner,
            suppressed=[loser.type],
            suppressed_desires=list(loser.possible_desires),
            severity=round(min(1.0, loser.intensity + 0.2), 4),
            resolution_rule=rule, reason=reason)

    def suppressed_desires(self,
                           conflicts: List[NeedConflict]) -> Dict[str, str]:
        """proposal -> reason, for everything the conflicts suppressed."""
        out: Dict[str, str] = {}
        for conflict in conflicts:
            for proposal in conflict.suppressed_desires:
                out[proposal] = (f"{conflict.kind}: {conflict.reason} "
                                 f"(rule: {conflict.resolution_rule})")
        return out

    def snapshot(self) -> Dict[str, Any]:
        return {"resolved_total": self.resolved_total,
                "recent": self.history[-5:],
                "priority_ladder": list(RESOLUTION_PRIORITY)}

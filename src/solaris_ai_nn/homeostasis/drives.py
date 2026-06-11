"""Drives -- needs aggregated into ten numeric pressure channels.

A drive is not "wanting": it is a decaying scalar pressure per category,
computed from the needs that feed it. The resolver exposes a fixed-order
drive vector (for substrate modulation) and a Desire-proposal bias dict
(for suggestion biasing) -- both deterministic for the same inputs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .needs import NeedState, NeedType
from .variables import clamp01

DRIVE_CATEGORIES = (
    "continuity_drive", "energy_drive", "safety_drive", "curiosity_drive",
    "consolidation_drive", "exploration_drive", "stabilization_drive",
    "embodiment_drive", "social_observation_drive", "governance_drive",
)

NEED_TO_DRIVE: Dict[str, str] = {
    NeedType.MAINTAIN_CONTINUITY: "continuity_drive",
    NeedType.STABILIZE_AFTER_RESTART: "continuity_drive",
    NeedType.RESTORE_ENERGY: "energy_drive",
    NeedType.AVOID_DANGER: "safety_drive",
    NeedType.RESPECT_BOUNDARY: "safety_drive",
    NeedType.REDUCE_UNCERTAINTY: "curiosity_drive",
    NeedType.CONSOLIDATE_MEMORY: "consolidation_drive",
    NeedType.PRUNE_REDUNDANCY: "consolidation_drive",
    NeedType.INCREASE_EXPLORATION: "exploration_drive",
    NeedType.SEEK_SIGNAL: "exploration_drive",
    NeedType.INCREASE_STABILIZATION: "stabilization_drive",
    NeedType.APPROACH_REWARD: "embodiment_drive",
    NeedType.REMAIN_OBSERVE_ONLY: "social_observation_drive",
    NeedType.REQUEST_OPERATOR_REVIEW: "governance_drive",
}

# How drive pressure biases Desire proposals (proposal -> weight).
DRIVE_TO_PROPOSALS: Dict[str, Dict[str, float]] = {
    "continuity_drive": {"checkpoint_now": 1.0, "stabilize": 0.5},
    "energy_drive": {"rest": 1.0, "reduce_activity": 0.6},
    "safety_drive": {"avoid_danger": 1.0, "remain_observe_only": 0.4,
                     "stabilize": 0.3},
    "curiosity_drive": {"run_replay": 0.7, "explore_safely": 0.6,
                        "look": 0.4},
    "consolidation_drive": {"consolidate_memory": 1.0, "rest": 0.3},
    "exploration_drive": {"explore_safely": 1.0, "seek_signal": 0.8,
                          "look": 0.5},
    "stabilization_drive": {"stabilize": 1.0, "reduce_activity": 0.5},
    "embodiment_drive": {"approach_reward": 1.0, "look": 0.2},
    "social_observation_drive": {"remain_observe_only": 1.0},
    "governance_drive": {"request_operator_review": 1.0},
}


@dataclass
class Drive:
    """One numeric pressure channel."""

    category: str
    pressure: float = 0.0
    priority: float = 0.0
    contributing_needs: List[str] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DriveState:
    """All ten drives, with the dominant one named."""

    drives: Dict[str, Drive] = field(default_factory=lambda: {
        category: Drive(category=category) for category in DRIVE_CATEGORIES})

    def dominant(self) -> Optional[Drive]:
        active = [d for d in self.drives.values() if d.pressure > 0]
        if not active:
            return None
        return max(active, key=lambda d: (d.priority, d.pressure,
                                          d.category))

    def vector(self) -> List[float]:
        """Fixed-order drive pressures (deterministic)."""
        return [round(self.drives[c].pressure, 6) for c in DRIVE_CATEGORIES]

    def to_dict(self) -> Dict[str, Any]:
        dominant = self.dominant()
        return {
            "drives": {c: self.drives[c].to_dict()
                       for c in DRIVE_CATEGORIES},
            "vector_order": list(DRIVE_CATEGORIES),
            "vector": self.vector(),
            "dominant": dominant.category if dominant else None,
            "note": "drives are numeric pressures, not wants",
        }


# Safety/governance/continuity drives carry structural priority bumps so a
# tie never resolves toward curiosity.
_PRIORITY_BONUS = {
    "governance_drive": 0.5, "safety_drive": 0.4, "continuity_drive": 0.3,
    "energy_drive": 0.2, "social_observation_drive": 0.15,
}


@dataclass
class DriveResolver:
    """Aggregates needs into drives; decays stale pressure."""

    decay_factor: float = 0.85
    state: DriveState = field(default_factory=DriveState)

    def aggregate(self, need_state: NeedState) -> DriveState:
        """Fold the current needs into the drive pressures."""
        now = time.time()
        fed: Dict[str, List[float]] = {}
        contributors: Dict[str, List[str]] = {}
        for need in need_state.needs:
            category = NEED_TO_DRIVE.get(need.type)
            if category is None:
                continue
            fed.setdefault(category, []).append(need.intensity)
            contributors.setdefault(category, []).append(need.type)
        for category in DRIVE_CATEGORIES:
            drive = self.state.drives[category]
            if category in fed:
                drive.pressure = round(clamp01(max(fed[category])), 6)
                drive.contributing_needs = sorted(set(
                    contributors[category]))
                drive.updated_at = now
            else:  # stale drives decay toward zero
                drive.pressure = round(drive.pressure * self.decay_factor, 6)
                if drive.pressure < 0.01:
                    drive.pressure = 0.0
                    drive.contributing_needs = []
            drive.priority = round(clamp01(
                drive.pressure + _PRIORITY_BONUS.get(category, 0.0)
                * (1.0 if drive.pressure > 0 else 0.0)), 6)
        return self.state

    def conflicts(self) -> List[Dict[str, Any]]:
        """Drive pairs pulling in opposite directions, both active."""
        pairs = [("exploration_drive", "stabilization_drive"),
                 ("curiosity_drive", "safety_drive"),
                 ("embodiment_drive", "energy_drive")]
        out = []
        for a, b in pairs:
            da, db = self.state.drives[a], self.state.drives[b]
            if da.pressure > 0.3 and db.pressure > 0.3:
                out.append({"between": [a, b],
                            "pressures": [da.pressure, db.pressure]})
        return out

    def drive_vector(self) -> np.ndarray:
        return np.asarray(self.state.vector(), dtype=float)

    def desire_bias(self) -> Dict[str, float]:
        """Proposal -> bias weight from the current drive pressures."""
        bias: Dict[str, float] = {}
        for category in DRIVE_CATEGORIES:
            pressure = self.state.drives[category].pressure
            if pressure <= 0:
                continue
            for proposal, weight in DRIVE_TO_PROPOSALS[category].items():
                bias[proposal] = round(
                    bias.get(proposal, 0.0) + pressure * weight, 6)
        return dict(sorted(bias.items()))

    def snapshot(self) -> Dict[str, Any]:
        return {**self.state.to_dict(), "conflicts": self.conflicts()}

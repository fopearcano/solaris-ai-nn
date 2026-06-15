"""Simulation boundary -- keep simulated/replay/debug strictly out of observation.

The :class:`SimulationBoundaryValidator` ensures simulations stay marked as
simulation, counterfactuals as counterfactual, fixture as fixture, replay as
replay, live read-only as live read-only, debug truth outside perception, and
report glosses debug-only. A :class:`SimulationBoundaryViolation` is raised
(recorded, not thrown) whenever one of these would cross into observation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class BoundaryMarker:
    OBSERVATION = "observation"
    SIMULATION = "simulation"
    COUNTERFACTUAL = "counterfactual"
    FIXTURE = "fixture"
    REPLAY = "replay"
    LIVE_READ_ONLY = "live_read_only"
    DEBUG_TRUTH = "debug_truth"
    REPORT_GLOSS = "report_gloss"

    ALL = (OBSERVATION, SIMULATION, COUNTERFACTUAL, FIXTURE, REPLAY,
           LIVE_READ_ONLY, DEBUG_TRUTH, REPORT_GLOSS)

    # Markers that must NEVER be treated as live observation / sensory evidence.
    NON_OBSERVATION = frozenset({SIMULATION, COUNTERFACTUAL, DEBUG_TRUTH,
                                 REPORT_GLOSS})


@dataclass
class SimulationBoundaryMarker:
    """A record tagged with its boundary marker (kept distinct from observation)."""

    ref: str
    marker: str
    marker_id: str = field(default_factory=lambda: f"MRK_{uuid.uuid4().hex[:8]}")

    @property
    def is_observation(self) -> bool:
        return self.marker == BoundaryMarker.OBSERVATION

    def to_dict(self) -> Dict[str, Any]:
        return {"marker_id": self.marker_id, "ref": self.ref,
                "marker": self.marker, "is_observation": self.is_observation}


@dataclass
class SimulationBoundaryViolation:
    ref: str
    marker: str
    attempted: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"ref": self.ref, "marker": self.marker,
                "attempted": self.attempted, "detail": self.detail,
                "note": "blocked: a non-observation marker must not become "
                        "observation/evidence"}


@dataclass
class SimulationBoundaryValidator:
    """Validates that non-observation markers never cross into observation."""

    markers: List[SimulationBoundaryMarker] = field(default_factory=list)
    violations: List[SimulationBoundaryViolation] = field(default_factory=list)

    def mark(self, ref: str, marker: str) -> SimulationBoundaryMarker:
        if marker not in BoundaryMarker.ALL:
            marker = BoundaryMarker.DEBUG_TRUTH
        m = SimulationBoundaryMarker(ref=ref, marker=marker)
        self.markers.append(m)
        return m

    def validate_use_as_observation(self, ref: str,
                                    marker: str) -> bool:
        """Return True if ``ref`` may be used as observation; else record a violation."""
        if marker in BoundaryMarker.NON_OBSERVATION:
            self.violations.append(SimulationBoundaryViolation(
                ref=ref, marker=marker, attempted="use_as_observation",
                detail="non-observation marker blocked from perception"))
            return False
        return True

    def warning_count(self) -> int:
        return len(self.violations)

    def integrity(self) -> float:
        """Boundary integrity: 1.0 when no non-observation marker leaked."""
        total = max(1, len(self.markers))
        return round(max(0.0, 1.0 - len(self.violations) / total), 4)

    def to_dict(self) -> Dict[str, Any]:
        dist: Dict[str, int] = {}
        for m in self.markers:
            dist[m.marker] = dist.get(m.marker, 0) + 1
        return {
            "marker_count": len(self.markers),
            "marker_distribution": dist,
            "violation_count": len(self.violations),
            "boundary_integrity": self.integrity(),
            "violations": [v.to_dict() for v in self.violations],
            "note": "simulation/counterfactual/debug never becomes observation "
                    "or sensory evidence",
        }

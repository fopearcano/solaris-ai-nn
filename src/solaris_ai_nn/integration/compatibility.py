"""Compatibility report types for the Solaris_Ai integration.

The probe (``solaris_probe.py``) inspects a Solaris_Ai-like runtime by duck
typing and summarises what it found here. Compatibility levels, in increasing
order of usefulness:

* ``unavailable``     -- nothing usable was found
* ``minimal``         -- an object exists but its bus is missing/unusable
* ``bus_observable``  -- a bus with subscribe+publish; signals can be observed
* ``sidecar_ready``   -- bus + stimulate/react + snapshot; the sidecar can mount
* ``full_test_ready`` -- sidecar_ready + lifecycle + inner_map + signal classes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

UNAVAILABLE = "unavailable"
MINIMAL = "minimal"
BUS_OBSERVABLE = "bus_observable"
SIDECAR_READY = "sidecar_ready"
FULL_TEST_READY = "full_test_ready"

# Ordered worst -> best, for comparisons.
COMPATIBILITY_LEVELS = (UNAVAILABLE, MINIMAL, BUS_OBSERVABLE, SIDECAR_READY,
                        FULL_TEST_READY)


def level_at_least(level: str, minimum: str) -> bool:
    """True if ``level`` is at or above ``minimum`` in the ordering."""
    return COMPATIBILITY_LEVELS.index(level) >= COMPATIBILITY_LEVELS.index(minimum)


@dataclass
class FeatureStatus:
    """Presence (and detail) of one probed feature."""

    name: str
    present: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "present": self.present, "detail": self.detail}


@dataclass
class SolarisCompatibilityReport:
    """What a probed Solaris_Ai-like runtime offers, and what it lacks."""

    level: str = UNAVAILABLE
    features: List[FeatureStatus] = field(default_factory=list)
    signal_classes: List[str] = field(default_factory=list)
    bus_subscriptions: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def feature(self, name: str) -> FeatureStatus:
        for f in self.features:
            if f.name == name:
                return f
        return FeatureStatus(name=name, present=False, detail="not probed")

    def has(self, name: str) -> bool:
        return self.feature(name).present

    def missing_features(self) -> List[str]:
        return [f.name for f in self.features if not f.present]

    def is_compatible(self, minimum: str = BUS_OBSERVABLE) -> bool:
        """True if the probed runtime meets at least ``minimum``."""
        return level_at_least(self.level, minimum)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "features": [f.to_dict() for f in self.features],
            "missing": self.missing_features(),
            "signal_classes": list(self.signal_classes),
            "bus_subscriptions": dict(self.bus_subscriptions),
            "notes": list(self.notes),
        }

    def summary(self) -> str:
        missing = self.missing_features()
        parts = [f"compatibility level: {self.level}"]
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if self.signal_classes:
            parts.append(f"signal classes: {len(self.signal_classes)}")
        return "; ".join(parts)

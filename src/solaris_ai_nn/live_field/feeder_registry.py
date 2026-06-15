"""Live feeder registry -- a local catalogue of feeders Solaris may read.

The registry records, per feeder, where its output is, what modality it carries,
how often it is expected to fire, and whether it requires governance. It is local
and passive: it never starts a feeder and never controls hardware, and a missing
feeder output is reported, not silently ignored.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .feeder_contract import LiveFeederMode, LiveFeederTrust


class LiveFeederStatus:
    REGISTERED = "registered"
    PRESENT = "present"
    MISSING = "missing"
    DISABLED = "disabled"

    ALL = (REGISTERED, PRESENT, MISSING, DISABLED)


@dataclass
class LiveFeederDescriptor:
    """Describes one live feeder (where Solaris reads, never controls)."""

    feeder_id: str
    source_id: str
    modality: str
    mode: str
    output_path: str
    input_path: Optional[str] = None
    expected_event_rate: float = 0.0  # events per second (0 = unknown)
    expected_silence_window_s: float = 30.0
    trust_level: str = LiveFeederTrust.UNKNOWN
    read_only: bool = True
    source_mutable_by_solaris: bool = False
    enabled: bool = True
    requires_governance: bool = False
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.mode not in LiveFeederMode.ALL:
            self.mode = LiveFeederMode.UNKNOWN
        self.read_only = True
        self.source_mutable_by_solaris = False
        if self.mode in LiveFeederMode.REAL_WORLD:
            self.requires_governance = True

    def status(self) -> str:
        if not self.enabled:
            return LiveFeederStatus.DISABLED
        if self.output_path and os.path.exists(self.output_path):
            return LiveFeederStatus.PRESENT
        return LiveFeederStatus.MISSING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feeder_id": self.feeder_id,
            "source_id": self.source_id,
            "modality": self.modality,
            "mode": self.mode,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "expected_event_rate": self.expected_event_rate,
            "expected_silence_window_s": self.expected_silence_window_s,
            "trust_level": self.trust_level,
            "read_only": True,
            "source_mutable_by_solaris": False,
            "enabled": self.enabled,
            "requires_governance": self.requires_governance,
            "status": self.status(),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LiveFeederDescriptor":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class LiveFeederRegistry:
    """A local, passive registry of feeder descriptors."""

    live_root: str = ".solaris_ai_nn_live"
    feeders: Dict[str, LiveFeederDescriptor] = field(default_factory=dict)

    @property
    def path(self) -> str:
        return os.path.join(self.live_root, "feeder_registry.json")

    def register(self, descriptor: LiveFeederDescriptor) -> None:
        self.feeders[descriptor.feeder_id] = descriptor

    def get(self, feeder_id: str) -> Optional[LiveFeederDescriptor]:
        return self.feeders.get(feeder_id)

    def enabled_feeders(self) -> List[LiveFeederDescriptor]:
        return [f for f in self.feeders.values() if f.enabled]

    def missing_feeders(self) -> List[LiveFeederDescriptor]:
        return [f for f in self.feeders.values()
                if f.status() == LiveFeederStatus.MISSING]

    def present_feeders(self) -> List[LiveFeederDescriptor]:
        return [f for f in self.feeders.values()
                if f.status() == LiveFeederStatus.PRESENT]

    def requires_governance(self) -> bool:
        return any(f.requires_governance for f in self.enabled_feeders())

    def save(self) -> str:
        os.makedirs(self.live_root, exist_ok=True)
        payload = {"saved_at": time.time(),
                   "feeders": [f.to_dict() for f in self.feeders.values()]}
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        return self.path

    @classmethod
    def load(cls, live_root: str = ".solaris_ai_nn_live",
             ) -> "LiveFeederRegistry":
        registry = cls(live_root=live_root)
        if os.path.isfile(registry.path):
            try:
                with open(registry.path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for row in data.get("feeders", []):
                    registry.register(LiveFeederDescriptor.from_dict(row))
            except (OSError, json.JSONDecodeError):
                pass
        return registry

    def snapshot(self) -> Dict[str, Any]:
        return {
            "feeder_count": len(self.feeders),
            "present_count": len(self.present_feeders()),
            "missing_count": len(self.missing_feeders()),
            "requires_governance": self.requires_governance(),
            "feeders": [f.to_dict() for f in self.feeders.values()],
        }

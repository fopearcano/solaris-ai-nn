"""Live feeder registry -- describes external read-only feeders (never controls).

:class:`LiveFeederRegistry` describes the external, operator-run feeders that write
JSONL events. It describes feeders only: Solaris must not start, stop, or edit
them. Unknown feeders are marked blocked/untrusted, and any feeder claiming
``solaris_may_control=true`` is blocked.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .birth_profile import (
    ALLOWED_FIRST_BIRTH_SOURCES,
    FORBIDDEN_FIRST_BIRTH_SOURCES,
)

REGISTRY_FILENAME = "FEEDER_REGISTRY.json"


class FeederStatus:
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"

    ALL = (ALLOWED, BLOCKED, UNTRUSTED, UNKNOWN)


class FeederTrustLevel:
    OPERATOR_TRUSTED = "operator_trusted"
    PROVISIONAL = "provisional"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"

    ALL = (OPERATOR_TRUSTED, PROVISIONAL, UNTRUSTED, UNKNOWN)


@dataclass
class LiveFeederRecord:
    """One feeder description (Solaris reads its output only)."""

    feeder_id: str
    source_id: str = ""
    modality: str = ""
    channel: str = ""
    description: str = ""
    writes_to: str = ""
    read_only: bool = True
    started_externally: bool = True
    solaris_may_control: bool = False
    expected_event_rate: str = ""
    privacy_level: str = "low"
    trust_level: str = FeederTrustLevel.PROVISIONAL
    allowed: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.trust_level not in FeederTrustLevel.ALL:
            self.trust_level = FeederTrustLevel.UNKNOWN

    @property
    def status(self) -> str:
        if self.solaris_may_control or not self.read_only \
                or not self.started_externally:
            return FeederStatus.BLOCKED
        if self.source_id in FORBIDDEN_FIRST_BIRTH_SOURCES:
            return FeederStatus.BLOCKED
        if self.source_id not in ALLOWED_FIRST_BIRTH_SOURCES:
            return FeederStatus.UNTRUSTED
        if self.trust_level == FeederTrustLevel.UNTRUSTED:
            return FeederStatus.UNTRUSTED
        return FeederStatus.ALLOWED if self.allowed else FeederStatus.BLOCKED

    @property
    def blocks_birth(self) -> bool:
        return self.solaris_may_control or not self.read_only

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feeder_id": self.feeder_id, "source_id": self.source_id,
            "modality": self.modality, "channel": self.channel,
            "description": self.description, "writes_to": self.writes_to,
            "read_only": self.read_only,
            "started_externally": self.started_externally,
            "solaris_may_control": self.solaris_may_control,
            "expected_event_rate": self.expected_event_rate,
            "privacy_level": self.privacy_level, "trust_level": self.trust_level,
            "allowed": self.allowed, "status": self.status,
            "blocks_birth": self.blocks_birth,
            "limitations": list(self.limitations)}


@dataclass
class LiveFeederRegistry:
    """Loads + indexes the feeder registry (describe-only)."""

    records: List[LiveFeederRecord] = field(default_factory=list)
    path: str = ""
    present: bool = False

    @classmethod
    def load(cls, state_dir: str,
             registry_path: Optional[str] = None) -> "LiveFeederRegistry":
        path = registry_path or os.path.join(state_dir, "feeders",
                                              REGISTRY_FILENAME)
        if not os.path.isfile(path):
            return cls(records=[], path=path, present=False)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return cls(records=[], path=path, present=True)
        records = []
        for r in data.get("feeders", []) or []:
            records.append(LiveFeederRecord(
                feeder_id=str(r.get("feeder_id", "")),
                source_id=str(r.get("source_id", "")),
                modality=str(r.get("modality", "")),
                channel=str(r.get("channel", "")),
                description=str(r.get("description", "")),
                writes_to=str(r.get("writes_to", "")),
                read_only=bool(r.get("read_only", True)),
                started_externally=bool(r.get("started_externally", True)),
                solaris_may_control=bool(r.get("solaris_may_control", False)),
                expected_event_rate=str(r.get("expected_event_rate", "")),
                privacy_level=str(r.get("privacy_level", "low")),
                trust_level=str(r.get("trust_level",
                                      FeederTrustLevel.PROVISIONAL)),
                allowed=bool(r.get("allowed", True)),
                limitations=list(r.get("limitations", []))))
        return cls(records=records, path=path, present=True)

    def get(self, source_id: str) -> Optional[LiveFeederRecord]:
        for r in self.records:
            if r.source_id == source_id:
                return r
        return None

    def is_registered(self, source_id: str) -> bool:
        return self.get(source_id) is not None

    def blocking(self) -> List[LiveFeederRecord]:
        return [r for r in self.records if r.blocks_birth]

    def index(self) -> Dict[str, Any]:
        return {
            "live_feeder_count": len(self.records),
            "allowed_count": sum(1 for r in self.records
                                 if r.status == FeederStatus.ALLOWED),
            "blocked_count": sum(1 for r in self.records
                                 if r.status == FeederStatus.BLOCKED),
            "untrusted_count": sum(1 for r in self.records
                                   if r.status == FeederStatus.UNTRUSTED),
            "blocks_birth_count": len(self.blocking()),
            "present": self.present, "path": self.path,
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["feeders"] = [r.to_dict() for r in self.records]
        d["note"] = ("registry describes feeders only; Solaris never starts, "
                     "stops, or edits feeders; unknown feeders are untrusted and "
                     "control-granting feeders are blocked")
        return d


def feeder_registry_template() -> Dict[str, Any]:
    """A safe feeder registry template for the allowed first-birth sources."""
    feeders = []
    specs = [
        ("chronos_absence", "chronos", "time/absence",
         "wall-clock ticks and absence/silence events"),
        ("machine_body", "machine_body", "scalar",
         "local machine scalar state (load, uptime) provided read-only"),
        ("local_environment_manual", "environment", "manual",
         "manually-provided local environment readings"),
        ("local_weather_readonly_external", "weather", "scalar",
         "operator-provided read-only local weather scalars"),
        ("project_artifact_field", "artifact", "field",
         "read-only summary of local project artifact counts"),
        ("operator_pulse", "operator", "pulse",
         "operator pulse as a stimulus event, never a command"),
    ]
    for source_id, modality, channel, desc in specs:
        feeders.append({
            "feeder_id": f"feeder_{source_id}",
            "source_id": source_id, "modality": modality, "channel": channel,
            "description": desc,
            "writes_to": f".solaris_ai_nn_live/inbox/{source_id}.jsonl",
            "read_only": True, "started_externally": True,
            "solaris_may_control": False,
            "expected_event_rate": "low",
            "privacy_level": "low",
            "trust_level": "operator_trusted", "allowed": True,
            "limitations": ["read-only; Solaris never starts or controls this "
                            "feeder"]})
    return {"feeders": feeders,
            "note": "template feeder registry; all feeders are external, "
                    "read-only, operator-started, and never controlled by "
                    "Solaris"}

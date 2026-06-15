"""Feeder monitor -- watch feeder output files read-only.

:class:`FeederMonitor` inspects feeder output JSONL files (existence, recency,
event count, invalid count, silence duration, size, schema version, and privacy /
safety warnings) and produces a :class:`FeederMonitorSnapshot`. It reads output
only; it never starts or stops a feeder and never modifies feeder output.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .validators import EnvelopeValidator


@dataclass
class FeederOutputHealth:
    path: str
    exists: bool
    event_count: int = 0
    invalid_event_count: int = 0
    last_event_timestamp: Optional[float] = None
    silence_duration_s: float = 0.0
    file_size: int = 0
    schema_version: Optional[str] = None
    updated_recently: bool = False
    privacy_warnings: List[str] = field(default_factory=list)
    safety_warnings: List[str] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return self.exists and self.event_count > 0 and self.updated_recently

    @property
    def silent(self) -> bool:
        return self.exists and not self.updated_recently

    def to_dict(self) -> Dict[str, Any]:
        return {**{k: v for k, v in self.__dict__.items()},
                "active": self.active, "silent": self.silent}


@dataclass
class FeederMonitorSnapshot:
    outputs: List[FeederOutputHealth] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def active_count(self) -> int:
        return sum(1 for o in self.outputs if o.active)

    @property
    def silent_count(self) -> int:
        return sum(1 for o in self.outputs if o.silent)

    @property
    def invalid_event_count(self) -> int:
        return sum(o.invalid_event_count for o in self.outputs)

    @property
    def privacy_warning_count(self) -> int:
        return sum(len(o.privacy_warnings) for o in self.outputs)

    @property
    def safety_warning_count(self) -> int:
        return sum(len(o.safety_warnings) for o in self.outputs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_count": len(self.outputs),
            "active_count": self.active_count,
            "silent_count": self.silent_count,
            "invalid_event_count": self.invalid_event_count,
            "privacy_warning_count": self.privacy_warning_count,
            "safety_warning_count": self.safety_warning_count,
            "outputs": [o.to_dict() for o in self.outputs],
            "timestamp": self.timestamp,
        }


@dataclass
class FeederMonitor:
    """Reads feeder output files and reports their health (read-only)."""

    silence_window_s: float = 60.0
    validator: EnvelopeValidator = field(default_factory=EnvelopeValidator)

    def monitor(self, paths: List[str], *,
                now: Optional[float] = None) -> FeederMonitorSnapshot:
        now = now if now is not None else time.time()
        outputs = [self._monitor_one(p, now) for p in paths]
        return FeederMonitorSnapshot(outputs=outputs)

    def _monitor_one(self, path: str, now: float) -> FeederOutputHealth:
        if not os.path.isfile(path):
            return FeederOutputHealth(path=path, exists=False)
        try:
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
        except OSError:
            return FeederOutputHealth(path=path, exists=False)
        count = invalid = 0
        last_ts: Optional[float] = None
        schema_version: Optional[str] = None
        privacy: List[str] = []
        safety: List[str] = []
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    invalid += 1
                    continue
                if not self.validator.validate(record).valid:
                    invalid += 1
                    continue
                count += 1
                ts = record.get("timestamp")
                if isinstance(ts, (int, float)):
                    last_ts = ts
                schema_version = record.get("schema_version", schema_version)
                for pf in record.get("privacy_flags", []):
                    if pf in ("unknown_privacy_risk", "contains_human_text") \
                            and pf not in privacy:
                        privacy.append(pf)
                for sf in record.get("safety_flags", []):
                    if "violation" in str(sf) and sf not in safety:
                        safety.append(sf)
        # Updated-recently is based on the file's mtime, not event timestamps
        # (event timestamps may be simulated).
        updated_recently = (now - mtime) <= self.silence_window_s
        silence = max(0.0, now - mtime)
        return FeederOutputHealth(
            path=path, exists=True, event_count=count,
            invalid_event_count=invalid, last_event_timestamp=last_ts,
            silence_duration_s=round(silence, 3), file_size=size,
            schema_version=schema_version, updated_recently=updated_recently,
            privacy_warnings=privacy, safety_warnings=safety)

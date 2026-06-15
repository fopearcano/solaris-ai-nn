"""Local feeder validators -- check feeder output without running the feeder.

These validators inspect the JSONL files that local feeder scripts produce. They
never run a feeder and never modify its output: they confirm the file exists, the
JSONL parses, each record is a valid read-only event envelope with provenance, the
timestamps and modality are valid, and there is no command interpretation or
executable payload.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .feeder_contract import LiveFeederContract

_EXEC_KEYS = ("__exec__", "command", "shell", "eval", "system", "subprocess")


@dataclass
class FeederValidationResult:
    valid: bool
    path: str
    event_count: int = 0
    invalid_count: int = 0
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def _validate_jsonl(path: str, *, max_lines: int = 2000,
                    require_modality: bool = True) -> FeederValidationResult:
    if not os.path.isfile(path):
        return FeederValidationResult(False, path, reasons=["output path "
                                                            "missing"])
    contract = LiveFeederContract()
    events = invalid = 0
    reasons: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                reasons.append(f"invalid json at line {i}")
                continue
            if not isinstance(record, dict):
                invalid += 1
                continue
            # Read-only / immutability must be asserted (default true is ok).
            if record.get("read_only") is False:
                invalid += 1
                reasons.append(f"line {i}: read_only is false")
            if record.get("source_mutable_by_solaris") is True:
                invalid += 1
                reasons.append(f"line {i}: source_mutable_by_solaris is true")
            if any(k in record for k in _EXEC_KEYS):
                invalid += 1
                reasons.append(f"line {i}: executable/command payload rejected")
            ok, why = contract.validate_record(record)
            if require_modality and not record.get("modality") \
                    and not record.get("features"):
                ok = False
                why = why + ["missing modality/features"]
            if not ok:
                invalid += 1
                reasons.extend(f"line {i}: {w}" for w in why)
            else:
                events += 1
    return FeederValidationResult(
        valid=(invalid == 0 and events >= 0), path=path, event_count=events,
        invalid_count=invalid, reasons=reasons[:50])


@dataclass
class ManualLogFeederValidator:
    """Validates manual text-log feeder output (text is observation, not cmd)."""

    def validate(self, path: str) -> FeederValidationResult:
        return _validate_jsonl(path, require_modality=False)


@dataclass
class WatchedFolderFeederValidator:
    """Validates watched-folder feeder output (file-presence/change events)."""

    def validate(self, path: str) -> FeederValidationResult:
        return _validate_jsonl(path)


@dataclass
class SystemRhythmFeederValidator:
    """Validates local system-rhythm feeder output (machine rhythm features)."""

    def validate(self, path: str) -> FeederValidationResult:
        return _validate_jsonl(path)


@dataclass
class FeatureDropboxFeederValidator:
    """Validates normalized feature-dropbox output."""

    def validate(self, path: str) -> FeederValidationResult:
        return _validate_jsonl(path)

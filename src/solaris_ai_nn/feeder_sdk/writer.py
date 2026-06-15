"""Writer utilities -- append-only envelope output for external feeders.

:class:`JSONLFeederWriter` appends validated envelopes to a JSONL file and writes
a sidecar manifest; :class:`RollingJSONLFeederWriter` rotates by size or event
count. Writers write only to their configured output path: they never write inside
a source input path (unless that path *is* the output), never call the network or
a shell, never modify Solaris state, and never launch Solaris.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contract import FeederSDKEnvelope


@dataclass
class FeederWriteResult:
    path: str
    events_written: int = 0
    rotated: bool = False
    checksum: Optional[str] = None
    manifest_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def _to_record(envelope: Any) -> Dict[str, Any]:
    if isinstance(envelope, FeederSDKEnvelope):
        return envelope.to_dict()
    if hasattr(envelope, "to_dict"):
        return envelope.to_dict()
    if isinstance(envelope, dict):
        return envelope
    raise TypeError("envelope must be a FeederSDKEnvelope or dict")


@dataclass
class EnvelopeWriter:
    """Base writer; subclasses persist envelopes append-only."""

    output_path: str

    def __post_init__(self) -> None:
        parent = os.path.dirname(os.path.abspath(self.output_path))
        if parent:
            os.makedirs(parent, exist_ok=True)

    def write(self, envelope: Any) -> FeederWriteResult:  # pragma: no cover
        raise NotImplementedError

    @staticmethod
    def checksum(path: str) -> Optional[str]:
        if not os.path.isfile(path):
            return None
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()


@dataclass
class JSONLFeederWriter(EnvelopeWriter):
    """Appends envelopes to a JSONL file and writes a sidecar manifest."""

    write_manifest: bool = True
    events_written: int = field(default=0, init=False)

    def write(self, envelope: Any) -> FeederWriteResult:
        return self.write_many([envelope])

    def write_many(self, envelopes: List[Any]) -> FeederWriteResult:
        with open(self.output_path, "a", encoding="utf-8") as fh:
            for env in envelopes:
                fh.write(json.dumps(_to_record(env), default=str) + "\n")
                self.events_written += 1
        manifest_path = self._write_manifest() if self.write_manifest else None
        return FeederWriteResult(
            path=self.output_path, events_written=len(envelopes),
            checksum=self.checksum(self.output_path),
            manifest_path=manifest_path)

    def _write_manifest(self) -> str:
        path = self.output_path + ".manifest.json"
        manifest = {
            "output_path": self.output_path,
            "events_written": self.events_written,
            "checksum": self.checksum(self.output_path),
            "updated_at": time.time(),
            "note": "feeder output is append-only; Solaris reads it read-only",
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, default=str)
        return path


@dataclass
class RollingJSONLFeederWriter(EnvelopeWriter):
    """A JSONL writer that rotates the output by size or event count."""

    max_events: int = 1000
    max_bytes: int = 5_000_000
    write_manifest: bool = True
    _events_in_file: int = field(default=0, init=False)
    _rotation: int = field(default=0, init=False)
    events_written: int = field(default=0, init=False)

    def write(self, envelope: Any) -> FeederWriteResult:
        rotated = False
        if self._should_rotate():
            self._rotate()
            rotated = True
        with open(self.output_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(_to_record(envelope), default=str) + "\n")
        self._events_in_file += 1
        self.events_written += 1
        return FeederWriteResult(
            path=self.output_path, events_written=1, rotated=rotated,
            checksum=self.checksum(self.output_path))

    def _should_rotate(self) -> bool:
        if self._events_in_file >= self.max_events:
            return True
        try:
            return os.path.isfile(self.output_path) \
                and os.path.getsize(self.output_path) >= self.max_bytes
        except OSError:
            return False

    def _rotate(self) -> None:
        if os.path.isfile(self.output_path):
            self._rotation += 1
            rotated_path = f"{self.output_path}.{self._rotation}"
            os.rename(self.output_path, rotated_path)
        self._events_in_file = 0

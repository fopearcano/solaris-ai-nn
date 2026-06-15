"""Replay tools -- replay a recorded envelope stream into a new local stream.

:class:`FeederReplay` reads an existing JSONL envelope stream and writes a new one,
preserving or simulating timestamps, applying a speed factor and optional jitter,
and bounded by max events / runtime. Replay is local-only, never modifies the
original, and marks every replayed event in its provenance.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .clock import JitterModel


@dataclass
class ReplayClock:
    """Maps original timestamps to replay timestamps under a speed factor."""

    speed_factor: float = 1.0
    use_simulated_time: bool = False
    _origin: Optional[float] = field(default=None, init=False)

    def map(self, original_ts: float, index: int) -> float:
        if self.use_simulated_time:
            return round(index / max(1e-9, self.speed_factor), 6)
        if self._origin is None:
            self._origin = original_ts
        return round(self._origin
                     + (original_ts - self._origin) / max(1e-9,
                                                          self.speed_factor), 6)


@dataclass
class ReplayResult:
    source_path: str
    output_path: str
    events_replayed: int = 0
    source_modified: bool = False
    bounded_stop: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class FeederReplay:
    """Replays one JSONL envelope stream into a new output stream."""

    speed_factor: float = 1.0
    use_simulated_time: bool = False
    max_events: int = 5000
    max_runtime_s: float = 30.0
    jitter: Optional[JitterModel] = None

    def replay(self, source_path: str, output_path: str) -> ReplayResult:
        result = ReplayResult(source_path=source_path, output_path=output_path)
        if not os.path.isfile(source_path):
            result.bounded_stop = "source missing"
            return result
        before = self._checksum(source_path)
        clock = ReplayClock(speed_factor=self.speed_factor,
                            use_simulated_time=self.use_simulated_time)
        parent = os.path.dirname(os.path.abspath(output_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        started = time.time()
        with open(source_path, "r", encoding="utf-8", errors="replace") as src, \
                open(output_path, "w", encoding="utf-8") as out:
            for i, line in enumerate(src):
                if result.events_replayed >= self.max_events:
                    result.bounded_stop = "max_events reached"
                    break
                if time.time() - started > self.max_runtime_s:
                    result.bounded_stop = "max_runtime reached"
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                original_ts = float(record.get("timestamp", i))
                new_ts = clock.map(original_ts, i)
                if self.jitter is not None:
                    new_ts = self.jitter.apply(new_ts)
                record["timestamp"] = new_ts
                prov = dict(record.get("provenance") or {})
                prov["replayed"] = True
                prov["original_timestamp"] = original_ts
                prov["replay_source"] = source_path
                record["provenance"] = prov
                meta = dict(record.get("metadata") or {})
                meta["replayed"] = True
                record["metadata"] = meta
                out.write(json.dumps(record, default=str) + "\n")
                result.events_replayed += 1
        # The original file must be unchanged.
        result.source_modified = (self._checksum(source_path) != before)
        return result

    @staticmethod
    def _checksum(path: str) -> str:
        import hashlib

        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

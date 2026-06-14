"""JSONL stream adapter -- read an append-only JSONL source, read-only.

The :class:`JSONLStreamAdapter` reads new lines from an append-only JSONL file,
remembering the last byte offset, parsing a bounded number of events per poll,
skipping malformed lines with a warning, and preserving each raw line's hash.
It never truncates, locks, or modifies the file, and it detects rotation.
"""

from __future__ import annotations

import json
import os
from typing import Any

from .adapters import AdapterResult, SensoryAdapter
from .modality import SensoryModality, classify_modality


class JSONLStreamAdapter(SensoryAdapter):
    name = "jsonl_stream_adapter"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self._offset = 0
        self._modality = classify_modality(config.source_type,
                                            config.modality_hint).modality

    def _poll(self) -> AdapterResult:
        path = self.config.path
        result = AdapterResult()
        if not path or not os.path.isfile(path):
            result.read_errors = 1
            result.note = "source missing"
            return result
        if self._too_large():
            result.note = "file exceeds max_file_size_mb; skipped"
            return result
        size = os.path.getsize(path)
        # Rotation/truncation: file shrank below our offset -> reset and report.
        if size < self._offset:
            result.rotated = True
            self._offset = 0
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(self._offset)
            read = 0
            while read < self.config.max_events_per_poll:
                line = fh.readline()
                if not line:
                    break  # EOF
                stripped = line.strip()
                if not stripped:
                    continue
                read += 1
                try:
                    payload = json.loads(stripped)
                except Exception:
                    result.malformed += 1
                    result.events.append(self._make_event(
                        modality=self._modality, raw_line=stripped,
                        payload=None, malformed=True,
                        metadata={"warning": "malformed json line"}))
                    continue
                hint = None
                if isinstance(payload, dict):
                    hint = payload.get("valence_hint")
                result.events.append(self._make_event(
                    modality=self._modality, raw_line=stripped,
                    payload=payload,
                    external_valence_hint=(float(hint)
                                           if isinstance(hint, (int, float))
                                           else None)))
            self._offset = fh.tell()
        return result

    def snapshot(self) -> dict:
        return {**super().snapshot(), "offset": self._offset}

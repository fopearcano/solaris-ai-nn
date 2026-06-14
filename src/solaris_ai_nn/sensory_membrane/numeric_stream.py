"""Numeric stream adapter -- parse CSV-like numeric rows with the stdlib only.

The :class:`NumericStreamAdapter` reads ``timestamp,value`` or named-column
CSV rows using the standard library (no pandas), normalizes values, and labels
a simple trend per poll (rising / falling / stable / spike / missing).
Malformed rows become warning events.
"""

from __future__ import annotations

import csv
import os
from typing import Any, Dict, List, Optional

from .adapters import AdapterResult, SensoryAdapter
from .modality import SensoryModality


class NumericStreamAdapter(SensoryAdapter):
    name = "numeric_stream_adapter"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self._offset = 0
        self._last_value: Optional[float] = None
        self._header: Optional[List[str]] = None

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
        if size < self._offset:
            result.rotated = True
            self._offset = 0
            self._header = None
        with open(path, "r", encoding="utf-8", errors="replace",
                  newline="") as fh:
            fh.seek(self._offset)
            read = 0
            while read < self.config.max_events_per_poll:
                raw_line = fh.readline()
                if not raw_line:
                    break  # EOF
                line = raw_line.strip()
                if not line:
                    continue
                read += 1
                self._handle_row(line, result)
            self._offset = fh.tell()
        return result

    def _handle_row(self, line: str, result: AdapterResult) -> None:
        try:
            row = next(csv.reader([line]))
        except Exception:
            result.malformed += 1
            return
        # A non-numeric first row is treated as a header.
        if self._header is None and not self._looks_numeric(row):
            self._header = [c.strip() for c in row]
            return
        values = self._parse_values(row)
        if not values:
            result.malformed += 1
            result.events.append(self._make_event(
                modality=SensoryModality.NUMERIC, raw_line=line,
                malformed=True, metadata={"warning": "malformed numeric row"}))
            return
        primary = self._primary(values)
        trend = self._trend(primary)
        self._last_value = primary
        result.events.append(self._make_event(
            modality=SensoryModality.NUMERIC, raw_line=line,
            numeric_values=values,
            metadata={"trend": trend, "primary": primary}))

    @staticmethod
    def _looks_numeric(row: List[str]) -> bool:
        numeric = 0
        for cell in row:
            try:
                float(cell)
                numeric += 1
            except (TypeError, ValueError):
                pass
        return numeric >= 1

    def _parse_values(self, row: List[str]) -> Dict[str, float]:
        values: Dict[str, float] = {}
        for i, cell in enumerate(row):
            try:
                val = float(cell)
            except (TypeError, ValueError):
                continue
            name = (self._header[i] if self._header and i < len(self._header)
                    else f"col{i}")
            values[name] = val
        return values

    @staticmethod
    def _primary(values: Dict[str, float]) -> float:
        for key in ("value", "val", "y"):
            if key in values:
                return values[key]
        # Otherwise the last numeric column (skip a leading timestamp).
        items = list(values.values())
        return items[-1] if items else 0.0

    def _trend(self, current: float) -> str:
        if self._last_value is None:
            return "stable"
        delta = current - self._last_value
        scale = max(1e-9, abs(self._last_value))
        rel = delta / scale
        if abs(rel) >= 1.0:
            return "spike"
        if rel > 0.05:
            return "rising"
        if rel < -0.05:
            return "falling"
        return "stable"

    def snapshot(self) -> dict:
        return {**super().snapshot(), "offset": self._offset,
                "last_value": self._last_value}

"""Text stream adapter -- read new text lines as environmental stimuli.

The :class:`TextStreamAdapter` reads a bounded number of new text lines,
preserving each line's raw hash and timestamp. Text is classified as a
*textual environmental stimulus* -- world input, not operator input. It may be
processed symbolically later, but it is never executed and never a command.
"""

from __future__ import annotations

import os
from typing import Any

from .adapters import AdapterResult, SensoryAdapter
from .modality import SensoryModality


class TextStreamAdapter(SensoryAdapter):
    name = "text_stream_adapter"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self._offset = 0

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
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(self._offset)
            read = 0
            while read < self.config.max_events_per_poll:
                line = fh.readline()
                if not line:
                    break  # EOF
                text = line.rstrip("\n")
                if not text.strip():
                    continue
                read += 1
                # Environmental text -- explicitly NOT an operator command.
                result.events.append(self._make_event(
                    modality=SensoryModality.TEXTUAL, raw_line=text,
                    payload=text,
                    metadata={"classification":
                              "textual_environmental_stimulus",
                              "is_operator_command": False}))
            self._offset = fh.tell()
        return result

    def snapshot(self) -> dict:
        return {**super().snapshot(), "offset": self._offset}

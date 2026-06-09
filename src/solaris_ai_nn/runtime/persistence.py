"""Optional JSONL persistence -- the only "storage layer" in this scaffold.

No database. Long runs can append newline-delimited JSON records to a file and
read them back later. Persistence is opt-in: pass a :class:`JsonlWriter` to a
component that supports it, or leave it ``None`` for pure in-memory operation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, Union


@dataclass
class JsonlWriter:
    """Append-only JSON-lines writer.

    Args:
        path: Destination file (created/truncated on first open).
    """

    path: Union[str, Path]
    _fh: Any = field(default=None, repr=False, init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "w", encoding="utf-8")

    def write(self, record: Dict[str, Any]) -> None:
        """Append one record as a JSON line and flush."""
        if self._fh is None:
            raise RuntimeError("writer is closed")
        self._fh.write(json.dumps(record, default=str) + "\n")
        self._fh.flush()

    def close(self) -> None:
        """Close the underlying file handle (idempotent)."""
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "JsonlWriter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def read_jsonl(path: Union[str, Path]) -> Iterator[Dict[str, Any]]:
    """Yield records from a JSONL file written by :class:`JsonlWriter`."""
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)

"""Artifact index -- a read-only catalogue of local artifacts.

:class:`ArtifactIndexer` walks the known local state/artifact directories and
records each file's path, type, size, modification time, checksum, readability,
and safety/evidence relevance. It never modifies, deletes, or hides artifacts:
corrupted or unreadable files are recorded with a ``corrupted`` flag, and large
files are checksummed by streaming chunks rather than being loaded fully into
memory.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Default directories the indexer knows about (relative to the project root).
DEFAULT_DIRECTORIES = (
    ".solaris_ai_nn_state",
    ".solaris_ai_nn_pilot1",
    ".solaris_ai_nn_pilot2",
    ".solaris_ai_nn_pilot3",
    ".solaris_ai_nn_pilot4",
    ".solaris_ai_nn_research",
    ".solaris_ai_nn_architecture",
    ".solaris_ai_nn_operator",
)

# Files larger than this are checksummed by streaming, never loaded in full.
LARGE_FILE_BYTES = 1_000_000
_CHUNK = 65_536

_SAFETY_HINTS = ("safety", "red_team", "assurance", "invariant", "incident",
                 "firewall", "boundary")
_EVIDENCE_HINTS = ("report", "ledger", "result", "review", "roadmap", "adr",
                   "snapshot", "analysis", "dossier", "provenance", "evidence")


def _artifact_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {".json": "json", ".jsonl": "jsonl", ".md": "markdown",
            ".txt": "text", ".csv": "csv"}.get(ext, "other")


@dataclass
class ArtifactRecord:
    path: str
    artifact_type: str
    size: int
    modified_time: float
    checksum: Optional[str]
    readable: bool
    corrupted: bool
    safety_relevance: bool
    evidence_relevance: bool
    large: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ArtifactIndex:
    records: List[ArtifactRecord] = field(default_factory=list)

    def add(self, record: ArtifactRecord) -> None:
        self.records.append(record)

    def corrupted(self) -> List[ArtifactRecord]:
        return [r for r in self.records if r.corrupted]

    def safety_relevant(self) -> List[ArtifactRecord]:
        return [r for r in self.records if r.safety_relevance]

    def by_type(self, artifact_type: str) -> List[ArtifactRecord]:
        return [r for r in self.records if r.artifact_type == artifact_type]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_count": len(self.records),
            "corrupted_count": len(self.corrupted()),
            "safety_relevant_count": len(self.safety_relevant()),
            "records": [r.to_dict() for r in self.records],
        }


@dataclass
class ArtifactIndexer:
    """Indexes local artifacts without modifying them."""

    directories: List[str] = field(
        default_factory=lambda: list(DEFAULT_DIRECTORIES))

    def index(self) -> ArtifactIndex:
        index = ArtifactIndex()
        for directory in self.directories:
            if not directory or not os.path.isdir(directory):
                continue
            for root, _dirs, files in os.walk(directory):
                for name in sorted(files):
                    index.add(self._index_file(os.path.join(root, name)))
        return index

    def _index_file(self, path: str) -> ArtifactRecord:
        low = path.lower()
        atype = _artifact_type(path)
        safety = any(h in low for h in _SAFETY_HINTS)
        evidence = any(h in low for h in _EVIDENCE_HINTS)
        try:
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
        except OSError:
            return ArtifactRecord(
                path=path, artifact_type=atype, size=0, modified_time=0.0,
                checksum=None, readable=False, corrupted=True,
                safety_relevance=safety, evidence_relevance=evidence)
        large = size > LARGE_FILE_BYTES
        checksum, readable, corrupted = self._checksum(path)
        return ArtifactRecord(
            path=path, artifact_type=atype, size=size, modified_time=mtime,
            checksum=checksum, readable=readable, corrupted=corrupted,
            safety_relevance=safety, evidence_relevance=evidence, large=large)

    def _checksum(self, path: str):
        """Stream the file in chunks; never load it fully into memory."""
        digest = hashlib.sha256()
        try:
            with open(path, "rb") as fh:
                while True:
                    chunk = fh.read(_CHUNK)
                    if not chunk:
                        break
                    digest.update(chunk)
            return digest.hexdigest(), True, False
        except OSError:
            return None, False, True

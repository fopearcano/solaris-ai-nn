"""Implementation-artifact reader -- read-only ingestion of local evidence.

:class:`ImplementationArtifactReader` reads Markdown/JSON/JSONL/diff/test-output/
changed-file-list artifacts from local paths or in-memory payloads, computes a
basic checksum, and detects missing/empty/corrupt artifacts. It is strictly
read-only: it modifies no artifact, executes no code, and calls no Git/GitHub.
Corrupt artifacts are preserved as evidence (recorded, never dropped).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ArtifactIntegrityIssue:
    """A recorded integrity problem with an artifact (preserved as evidence)."""

    artifact_id: str
    kind: str  # missing | empty | corrupt | unreadable
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_id": self.artifact_id, "kind": self.kind,
                "detail": self.detail}


@dataclass
class ArtifactReadResult:
    """The outcome of reading one artifact (read-only)."""

    artifact_id: str
    ok: bool
    kind: str = ""  # markdown | json | jsonl | diff | text | list | object
    payload: Any = None
    checksum: str = ""
    issue: Optional[ArtifactIntegrityIssue] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_id": self.artifact_id, "ok": self.ok,
                "kind": self.kind, "checksum": self.checksum,
                "has_payload": self.payload is not None,
                "issue": self.issue.to_dict() if self.issue else None}


def _checksum(value: Any) -> str:
    try:
        blob = (value if isinstance(value, str)
                else json.dumps(value, sort_keys=True, default=str))
    except Exception:
        blob = str(value)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


@dataclass
class ImplementationArtifactReader:
    """Reads local artifacts read-only; records integrity issues as evidence."""

    issues: List[ArtifactIntegrityIssue] = field(default_factory=list)

    def read_payload(self, artifact_id: str, payload: Any) -> ArtifactReadResult:
        """Read an in-memory payload (dict/list/str), detecting empties."""
        if payload is None:
            issue = ArtifactIntegrityIssue(artifact_id, "missing",
                                           "no payload supplied")
            self.issues.append(issue)
            return ArtifactReadResult(artifact_id, False, issue=issue)
        if isinstance(payload, str) and not payload.strip():
            issue = ArtifactIntegrityIssue(artifact_id, "empty",
                                           "empty text payload")
            self.issues.append(issue)
            return ArtifactReadResult(artifact_id, False, kind="text",
                                      payload=payload, issue=issue)
        if isinstance(payload, (list, dict)) and len(payload) == 0:
            issue = ArtifactIntegrityIssue(artifact_id, "empty",
                                           "empty collection payload")
            self.issues.append(issue)
            return ArtifactReadResult(artifact_id, False,
                                      kind="object", payload=payload,
                                      issue=issue)
        kind = ("list" if isinstance(payload, list)
                else "object" if isinstance(payload, dict)
                else "diff" if isinstance(payload, str) and
                ("@@" in payload or payload.lstrip().startswith(("diff ",
                                                                 "--- ", "+++ ")))
                else "text")
        return ArtifactReadResult(artifact_id, True, kind=kind, payload=payload,
                                  checksum=_checksum(payload))

    def read_file(self, artifact_id: str, path: str) -> ArtifactReadResult:
        """Read an artifact from a local path (read-only)."""
        if not path or not os.path.isfile(path):
            issue = ArtifactIntegrityIssue(artifact_id, "missing",
                                           f"file not found: {path!r}")
            self.issues.append(issue)
            return ArtifactReadResult(artifact_id, False, issue=issue)
        try:
            with open(path, encoding="utf-8") as fh:
                raw = fh.read()
        except Exception as exc:  # pragma: no cover - environment dependent
            issue = ArtifactIntegrityIssue(artifact_id, "unreadable", str(exc))
            self.issues.append(issue)
            return ArtifactReadResult(artifact_id, False, issue=issue)
        if not raw.strip():
            issue = ArtifactIntegrityIssue(artifact_id, "empty", "empty file")
            self.issues.append(issue)
            return ArtifactReadResult(artifact_id, False, kind="text",
                                      payload=raw, issue=issue)
        lower = path.lower()
        if lower.endswith(".json"):
            try:
                payload = json.loads(raw)
                return ArtifactReadResult(artifact_id, True, kind="json",
                                          payload=payload,
                                          checksum=_checksum(raw))
            except Exception as exc:
                issue = ArtifactIntegrityIssue(artifact_id, "corrupt",
                                               f"invalid JSON: {exc}")
                self.issues.append(issue)  # preserved as evidence
                return ArtifactReadResult(artifact_id, False, kind="json",
                                          payload=raw, issue=issue)
        if lower.endswith(".jsonl"):
            records, bad = [], 0
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    bad += 1
            if bad:
                issue = ArtifactIntegrityIssue(artifact_id, "corrupt",
                                               f"{bad} invalid JSONL line(s)")
                self.issues.append(issue)
            return ArtifactReadResult(artifact_id, bad == 0, kind="jsonl",
                                      payload=records, checksum=_checksum(raw),
                                      issue=issue if bad else None)
        kind = ("diff" if (lower.endswith((".diff", ".patch")) or "@@" in raw)
                else "markdown" if lower.endswith(".md") else "text")
        return ArtifactReadResult(artifact_id, True, kind=kind, payload=raw,
                                  checksum=_checksum(raw))

    def to_dict(self) -> Dict[str, Any]:
        return {"integrity_issue_count": len(self.issues),
                "issues": [i.to_dict() for i in self.issues],
                "read_only": True}

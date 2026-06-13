"""State hygiene -- keep the state directory healthy over long runs.

The :class:`StateHygieneManager` validates the state directory, enforces file
size budgets, archives old reports/logs, rebuilds lightweight indexes,
detects orphaned files, verifies JSON/JSONL parseability, and quarantines
corrupted records -- always *inside* the state directory, always preserving
evidence (archive/quarantine, never silent delete), and never touching
source files.
"""

from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Files that hold evidence/safety records and must never be silently dropped.
EVIDENCE_FILES = (
    "incidents.jsonl", "governance_audit.jsonl", "repair_audit.jsonl",
    "hypothesis_evidence.jsonl", "autobiographical_memory.jsonl",
)

DEFAULT_MAX_BYTES = 50 * 1024 * 1024  # 50 MB per JSONL/log before rotation


@dataclass
class StateHygieneManager:
    """Validates and tidies the state directory; archives, never deletes."""

    state_dir: Optional[Union[str, Path]] = None
    max_file_bytes: int = DEFAULT_MAX_BYTES
    findings: List[Dict[str, Any]] = field(default_factory=list)
    quarantined: List[str] = field(default_factory=list)
    archived: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = Path(self.state_dir) if self.state_dir else None
        self.quarantine_dir = (self.root / "quarantine" if self.root
                               else None)
        self.archive_dir = (self.root / "archive" if self.root else None)
        self.audit_path = (self.root / "repair_audit.jsonl" if self.root
                           else None)

    # -- inspection (non-mutating) ------------------------------------------------

    def scan(self) -> Dict[str, Any]:
        """Inspect the state directory; returns findings, mutates nothing."""
        oversized, corrupt, orphans = [], [], []
        if self.root is not None and self.root.exists():
            for path in self.root.glob("*.jsonl"):
                try:
                    if path.stat().st_size > self.max_file_bytes:
                        oversized.append(path.name)
                    if not self._parseable_jsonl(path):
                        corrupt.append(path.name)
                except OSError:
                    corrupt.append(path.name)
            for path in self.root.glob("*.json"):
                if not self._parseable_json(path):
                    corrupt.append(path.name)
        result = {"oversized": oversized, "corrupt": corrupt,
                  "orphans": orphans,
                  "state_dir_exists": bool(self.root and self.root.exists())}
        self.findings.append({"scan": result, "at": time.time()})
        self.findings = self.findings[-50:]
        return result

    @staticmethod
    def _parseable_jsonl(path: Path) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        json.loads(line)
            return True
        except (OSError, ValueError):
            return False

    @staticmethod
    def _parseable_json(path: Path) -> bool:
        try:
            json.loads(path.read_text(encoding="utf-8") or "null")
            return True
        except (OSError, ValueError):
            return False

    # -- repairs (bounded, evidence-preserving) -----------------------------------

    def _inside_state(self, path: Path) -> bool:
        if self.root is None:
            return False
        try:
            return Path(path).resolve().is_relative_to(self.root.resolve())
        except (ValueError, AttributeError):
            try:
                Path(path).resolve().relative_to(self.root.resolve())
                return True
            except ValueError:
                return False

    def archive_file(self, name: str) -> Optional[str]:
        """Move an old report/log into archive/ (never deletes)."""
        if self.root is None:
            return None
        src = self.root / name
        if not src.exists() or not self._inside_state(src):
            return None
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        dst = self.archive_dir / f"{int(time.time())}_{name}"
        shutil.move(str(src), str(dst))
        self.archived.append(name)
        self._audit("archive", name, str(dst))
        return str(dst)

    def quarantine_file(self, name: str, reason: str = "") -> Optional[str]:
        """Move a corrupted file into quarantine/ (never deletes)."""
        if self.root is None:
            return None
        src = self.root / name
        if not src.exists() or not self._inside_state(src):
            return None
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        dst = self.quarantine_dir / f"{int(time.time())}_{name}"
        shutil.move(str(src), str(dst))
        self.quarantined.append(name)
        self._audit("quarantine", name, str(dst), reason=reason)
        return str(dst)

    def rebuild_index(self, name: str, records: List[Dict[str, Any]],
                      ) -> Optional[str]:
        """Write a lightweight index file inside the state directory."""
        if self.root is None:
            return None
        path = self.root / name
        path.write_text(json.dumps(records, indent=2, default=str),
                        encoding="utf-8")
        self._audit("rebuild_index", name, str(path))
        return str(path)

    def is_evidence_file(self, name: str) -> bool:
        return Path(name).name in EVIDENCE_FILES

    def _audit(self, action: str, name: str, dst: str,
               reason: str = "") -> None:
        if self.audit_path is None:
            return
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"action": action, "file": name,
                                 "destination": dst, "reason": reason,
                                 "at": time.time()}, default=str) + "\n")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "quarantined_count": len(self.quarantined),
            "archived_count": len(self.archived),
            "max_file_bytes": self.max_file_bytes,
            "state_dir": str(self.root) if self.root else None,
            "last_scan": self.findings[-1]["scan"] if self.findings else None,
        }

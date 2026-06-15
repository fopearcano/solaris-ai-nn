"""External feature dropbox -- folders external tools drop feature files into.

A :class:`FeatureDropbox` is a set of local inbox folders (one per modality) that
external tools may drop ``.jsonl`` / ``.json`` / ``.csv`` feature files into. The
:class:`FeatureDropboxIngestor` reads those files **read-only**: it never deletes,
moves, or modifies a source file, records corrupt files instead of hiding them,
and samples/tails large files within bounds.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .feeder_contract import LiveFeederContract, LiveFeederEnvelope, LiveFeederMode

# Suggested inbox folders, by modality hint.
INBOX_MODALITIES = {
    "rf": "alien_rf",
    "echo": "alien_echo",
    "thermal": "alien_thermal",
    "vibration": "alien_vibration",
    "magnetic": "alien_magnetic",
    "human_text": "human_textual",
    "system_rhythm": "machine_rhythm",
}

_MAX_RECORDS = 1000


@dataclass
class FeatureDropboxPollResult:
    envelopes: List[LiveFeederEnvelope] = field(default_factory=list)
    files_read: List[str] = field(default_factory=list)
    corrupt_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope_count": len(self.envelopes),
            "files_read": list(self.files_read),
            "corrupt_files": list(self.corrupt_files),
            "errors": list(self.errors),
        }


@dataclass
class FeatureDropbox:
    """A set of read-only inbox folders, one per modality."""

    live_root: str = ".solaris_ai_nn_live"

    @property
    def inbox_root(self) -> str:
        return os.path.join(self.live_root, "inbox")

    def folder_for(self, name: str) -> str:
        return os.path.join(self.inbox_root, name)

    def ensure_folders(self) -> List[str]:
        created: List[str] = []
        for name in INBOX_MODALITIES:
            path = self.folder_for(name)
            os.makedirs(path, exist_ok=True)
            created.append(path)
        return created

    def list_files(self, name: str) -> List[str]:
        folder = self.folder_for(name)
        if not os.path.isdir(folder):
            return []
        out = []
        for fn in sorted(os.listdir(folder)):
            if fn.lower().endswith((".jsonl", ".json", ".csv")):
                out.append(os.path.join(folder, fn))
        return out


@dataclass
class FeatureDropboxIngestor:
    """Reads dropbox feature files into live envelopes (read-only)."""

    dropbox: FeatureDropbox = field(default_factory=FeatureDropbox)
    contract: LiveFeederContract = field(default_factory=LiveFeederContract)

    def poll(self, max_records: int = _MAX_RECORDS) -> FeatureDropboxPollResult:
        result = FeatureDropboxPollResult()
        for name, modality_hint in INBOX_MODALITIES.items():
            for path in self.dropbox.list_files(name):
                if len(result.envelopes) >= max_records:
                    return result
                self._read_file(path, name, modality_hint, result, max_records)
        return result

    def _read_file(self, path: str, inbox_name: str, modality_hint: str,
                   result: FeatureDropboxPollResult, max_records: int) -> None:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".csv":
                records = self._read_csv(path)
            elif ext == ".json":
                records = self._read_json(path)
            else:
                records = self._read_jsonl(path)
        except (OSError, json.JSONDecodeError, csv.Error):
            result.corrupt_files.append(path)
            return
        result.files_read.append(path)
        feeder_id = f"dropbox_{inbox_name}"
        for i, record in enumerate(records):
            if len(result.envelopes) >= max_records:
                break
            ok, _why = self.contract.validate_record(record)
            if not ok:
                continue
            result.envelopes.append(self.contract.build_envelope(
                record, feeder_id=feeder_id,
                feeder_mode=LiveFeederMode.EXTERNAL_FEATURE_DROP,
                source_id=str(record.get("source_id", feeder_id)),
                modality_hint=modality_hint, raw_ref=f"{path}:{i}"))

    @staticmethod
    def _read_jsonl(path: str, max_lines: int = _MAX_RECORDS,
                    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    break
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    @staticmethod
    def _read_json(path: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)][:_MAX_RECORDS]
        return [data] if isinstance(data, dict) else []

    @staticmethod
    def _read_csv(path: str, max_lines: int = _MAX_RECORDS,
                  ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8", errors="replace",
                  newline="") as fh:
            for i, row in enumerate(csv.DictReader(fh)):
                if i >= max_lines:
                    break
                rec: Dict[str, Any] = {}
                for k, v in row.items():
                    try:
                        rec[k] = float(v)
                    except (TypeError, ValueError):
                        rec[k] = v
                out.append(rec)
        return out

"""Folder poll adapter -- detect file presence/changes by stdlib polling.

The :class:`FolderPollAdapter` polls an allowed folder, detecting new files
and changed files (by size/mtime, or a content hash for small text files),
and emits ``file_presence`` / ``file_change`` events. It never modifies files,
uses no OS watcher dependency, bounds the file count and total size, and only
scans recursively when explicitly configured.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from .adapters import AdapterResult, SensoryAdapter
from .modality import SensoryModality
from .provenance import hash_text


class FolderPollAdapter(SensoryAdapter):
    name = "folder_poll_adapter"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        # path -> (size, mtime) signature seen on the last poll.
        self._seen: Dict[str, "tuple[int, float]"] = {}

    def _poll(self) -> AdapterResult:
        folder = self.config.path
        result = AdapterResult()
        if not folder or not os.path.isdir(folder):
            result.read_errors = 1
            result.note = "folder missing"
            return result
        files = self._list_files(folder)
        if len(files) > self.config.max_file_count:
            files = files[:self.config.max_file_count]
            result.note = "file count bounded"
        for path in files:
            try:
                stat = os.stat(path)
            except OSError:
                result.read_errors += 1
                continue
            sig = (stat.st_size, stat.st_mtime)
            prev = self._seen.get(path)
            if prev is None:
                modality = SensoryModality.FILE_PRESENCE
            elif prev != sig:
                modality = SensoryModality.FILE_CHANGE
            else:
                continue  # unchanged
            self._seen[path] = sig
            meta: Dict[str, Any] = {"basename": os.path.basename(path),
                                    "size": stat.st_size,
                                    "path_hash": hash_text(path)}
            payload = os.path.basename(path)
            # Optionally read a small text file's content (read-only).
            if self.config.metadata.get("read_small_text") \
                    and stat.st_size <= 4096:
                try:
                    with open(path, "r", encoding="utf-8",
                              errors="replace") as fh:
                        meta["preview"] = fh.read(512)
                except OSError:
                    result.read_errors += 1
            result.events.append(self._make_event(
                modality=modality, payload=payload,
                raw_line=f"{modality}:{os.path.basename(path)}",
                metadata=meta))
            if len(result.events) >= self.config.max_events_per_poll:
                break
        return result

    def _list_files(self, folder: str) -> list:
        out = []
        if self.config.recursive:
            for root, _dirs, names in os.walk(folder):
                for name in sorted(names):
                    out.append(os.path.join(root, name))
                    if len(out) >= self.config.max_file_count:
                        return out
        else:
            for name in sorted(os.listdir(folder)):
                path = os.path.join(folder, name)
                if os.path.isfile(path):
                    out.append(path)
                if len(out) >= self.config.max_file_count:
                    break
        return out

    def snapshot(self) -> dict:
        return {**super().snapshot(), "tracked_files": len(self._seen)}

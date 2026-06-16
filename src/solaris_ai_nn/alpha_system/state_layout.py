"""Alpha state layout -- the local directory tree for an Alpha run.

:class:`AlphaStateLayout` creates and indexes the local state directories under a
single selected state root (default ``.solaris_ai_nn_alpha/``). It creates
directories only under that root, never deletes existing state, reuses directories
that already exist, and writes an ``ALPHA_STATE_MANIFEST.json``.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_STATE_ROOT = ".solaris_ai_nn_alpha"

SUBDIRECTORIES = ("input", "fixtures", "runs", "reports", "artifacts", "claims",
                  "review", "cycle", "logs", "index")


@dataclass
class AlphaStateDirectory:
    """One state subdirectory record."""

    name: str
    path: str
    existed: bool = False
    created: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "path": self.path, "existed": self.existed,
                "created": self.created}


@dataclass
class AlphaArtifactPath:
    """A resolved path inside the alpha state tree (no I/O on construction)."""

    state_root: str
    subdir: str
    filename: str

    @property
    def path(self) -> str:
        return os.path.join(self.state_root, self.subdir, self.filename)

    def to_dict(self) -> Dict[str, Any]:
        return {"state_root": self.state_root, "subdir": self.subdir,
                "filename": self.filename, "path": self.path}


@dataclass
class AlphaStateLayout:
    """Manages the local alpha state directory tree (create-only, never delete)."""

    state_root: str = DEFAULT_STATE_ROOT
    directories: List[AlphaStateDirectory] = field(default_factory=list,
                                                   init=False)
    created_ts: float = field(default_factory=time.time, init=False)

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.state_root, "ALPHA_STATE_MANIFEST.json")

    def subdir(self, name: str) -> str:
        return os.path.join(self.state_root, name)

    def artifact_path(self, subdir: str, filename: str) -> AlphaArtifactPath:
        return AlphaArtifactPath(self.state_root, subdir, filename)

    def initialize(self) -> Dict[str, Any]:
        """Create the state root and subdirectories (reuse existing; no delete)."""
        self.directories = []
        root_existed = os.path.isdir(self.state_root)
        os.makedirs(self.state_root, exist_ok=True)
        for name in SUBDIRECTORIES:
            path = self.subdir(name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            self.directories.append(AlphaStateDirectory(
                name=name, path=path, existed=existed, created=not existed))
        manifest = self._write_manifest(root_existed)
        return manifest

    def writable(self) -> bool:
        try:
            os.makedirs(self.state_root, exist_ok=True)
            probe = os.path.join(self.state_root, ".alpha_write_probe")
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write("ok")
            os.remove(probe)
            return True
        except Exception:
            return False

    def _write_manifest(self, root_existed: bool) -> Dict[str, Any]:
        manifest = {
            "state_root": self.state_root,
            "root_existed": root_existed,
            "created_ts": self.created_ts,
            "directories": [d.to_dict() for d in self.directories],
            "deletes_state": False,
            "note": ("local alpha state tree; created only under the selected "
                     "state root; existing state is reused, never deleted"),
        }
        with open(self.manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, default=str)
        return manifest

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_root": self.state_root,
            "manifest_path": self.manifest_path,
            "directory_count": len(self.directories),
            "directories": [d.to_dict() for d in self.directories],
            "deletes_state": False,
        }

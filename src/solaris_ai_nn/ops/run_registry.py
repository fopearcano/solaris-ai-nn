"""RunRegistry -- one JSON file remembering every supervised run."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .run_manifest import OperationalRunManifest

DEFAULT_REGISTRY_PATH = ".solaris_ai_nn_runs/run_registry.json"


@dataclass
class RunRegistry:
    """Tracks current and historical operational runs."""

    path: Union[str, Path] = DEFAULT_REGISTRY_PATH

    def __post_init__(self) -> None:
        self.path = Path(self.path)

    # -- storage ----------------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"runs": {}, "order": []}
        with open(self.path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        tmp.replace(self.path)

    # -- API ----------------------------------------------------------------------

    def register_start(self, manifest: OperationalRunManifest) -> Dict[str, Any]:
        data = self._load()
        entry = {
            "run_id": manifest.run_id,
            "session_id": manifest.session_id,
            "mode": manifest.mode,
            "status": "running",
            "started_at": time.time(),
            "ended_at": None,
            "state_dir": manifest.state_dir,
            "artifact_dir": manifest.artifact_dir,
            "last_health": None,
            "last_checkpoint": None,
            "final_scorecard": None,
            "incident_count": 0,
            "graceful_shutdown": None,
        }
        data["runs"][manifest.run_id] = entry
        if manifest.run_id not in data["order"]:
            data["order"].append(manifest.run_id)
        self._save(data)
        return entry

    def register_update(self, run_id: str, status: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        data = self._load()
        entry = data["runs"].get(run_id)
        if entry is None:
            return
        if status is not None:
            entry["status"] = status
        entry.update(metadata or {})
        self._save(data)

    def register_stop(self, run_id: str, graceful: bool,
                      summary: Optional[Dict[str, Any]] = None) -> None:
        data = self._load()
        entry = data["runs"].get(run_id)
        if entry is None:
            return
        entry["status"] = "stopped" if graceful else "failed"
        entry["ended_at"] = time.time()
        entry["graceful_shutdown"] = graceful
        entry.update(summary or {})
        self._save(data)

    def list_runs(self) -> List[Dict[str, Any]]:
        data = self._load()
        return [data["runs"][rid] for rid in data["order"]
                if rid in data["runs"]]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self._load()["runs"].get(run_id)

    def latest_run(self) -> Optional[Dict[str, Any]]:
        runs = self.list_runs()
        return runs[-1] if runs else None

    def to_dict(self) -> Dict[str, Any]:
        return self._load()

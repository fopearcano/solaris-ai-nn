"""PilotRegistry -- one JSON file remembering every pilot ever run."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .pilot_manifest import PilotManifest

DEFAULT_PILOT_REGISTRY_PATH = ".solaris_ai_nn_pilots/pilot_registry.json"


@dataclass
class PilotRegistry:
    """Tracks current and historical pilots (atomic JSON writes)."""

    path: Union[str, Path] = DEFAULT_PILOT_REGISTRY_PATH

    def __post_init__(self) -> None:
        self.path = Path(self.path)

    # -- storage ----------------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"pilots": {}, "order": []}
        with open(self.path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        tmp.replace(self.path)

    # -- API ----------------------------------------------------------------------

    def register_start(self, manifest: PilotManifest) -> Dict[str, Any]:
        data = self._load()
        entry = {
            "pilot_id": manifest.pilot_id,
            "profile": manifest.profile,
            "run_id": manifest.run_id,
            "status": "running",
            "started_at": time.time(),
            "ended_at": None,
            "operator": manifest.operator,
            "state_dir": manifest.state_dir,
            "artifact_dir": manifest.artifact_dir,
            "readiness_status": None,
            "incident_count": 0,
            "final_recommendation": None,
            "report_path": None,
        }
        data["pilots"][manifest.pilot_id] = entry
        if manifest.pilot_id not in data["order"]:
            data["order"].append(manifest.pilot_id)
        self._save(data)
        return entry

    def register_update(self, pilot_id: str,
                        status: Optional[str] = None,
                        **fields: Any) -> Dict[str, Any]:
        data = self._load()
        entry = data["pilots"].get(pilot_id)
        if entry is None:
            raise KeyError(f"unknown pilot {pilot_id!r}")
        if status is not None:
            entry["status"] = status
        for key, value in fields.items():
            entry[key] = value
        self._save(data)
        return entry

    def register_stop(self, pilot_id: str, status: str = "completed",
                      **fields: Any) -> Dict[str, Any]:
        entry = self.register_update(pilot_id, status=status, **fields)
        data = self._load()
        data["pilots"][pilot_id]["ended_at"] = time.time()
        self._save(data)
        return data["pilots"][pilot_id]

    def list_pilots(self) -> List[Dict[str, Any]]:
        data = self._load()
        return [data["pilots"][pid] for pid in data["order"]]

    def get_pilot(self, pilot_id: str) -> Optional[Dict[str, Any]]:
        return self._load()["pilots"].get(pilot_id)

    def latest(self) -> Optional[Dict[str, Any]]:
        pilots = self.list_pilots()
        return pilots[-1] if pilots else None

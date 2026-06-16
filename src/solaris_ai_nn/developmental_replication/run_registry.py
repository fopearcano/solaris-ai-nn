"""Run registry -- catalogue independent developmental runs and their artifacts.

:class:`DevelopmentalRunRegistry` reads run metadata and report paths from each
run's state directory and records them as :class:`RegisteredDevelopmentalRun`
entries. It *reads* metadata and reports; it does not start runs and never
modifies source artifacts. Missing metadata is preserved as explicit
uncertainty rather than guessed.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_REPORT_FILENAMES = {
    "soak_report": "SOAK_PROTOCOL_REPORT.json",
    "evidence_dossier": "SOAK_PROTOCOL_REPORT.json",
    "post_run_autopsy": "SOAK_PROTOCOL_REPORT.json",
    "developmental_life_report": "DEVELOPMENTAL_LIFE_REPORT.json",
}

_UNKNOWN = "unknown"


@dataclass
class RunArtifactIndex:
    """Discoverable report/artifact paths for one run (uncertainty preserved)."""

    run_id: str
    state_dir: str = ""
    soak_report_path: str = ""
    evidence_dossier_path: str = ""
    post_run_autopsy_path: str = ""
    developmental_life_report_path: str = ""
    discovered: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id, "state_dir": self.state_dir,
            "soak_report_path": self.soak_report_path,
            "evidence_dossier_path": self.evidence_dossier_path,
            "post_run_autopsy_path": self.post_run_autopsy_path,
            "developmental_life_report_path":
                self.developmental_life_report_path,
            "discovered": list(self.discovered), "missing": list(self.missing),
        }


@dataclass
class RegisteredDevelopmentalRun:
    """One independent developmental run's metadata + comparison profile."""

    run_id: str
    lineage_id: str = ""
    state_dir: str = ""
    start_ts: Optional[float] = None
    end_ts: Optional[float] = None
    runtime_duration_s: Optional[float] = None
    seed: Optional[int] = None
    architecture_version: str = _UNKNOWN
    commit_hash: str = ""
    sensorium_profile: str = _UNKNOWN
    feeder_profile: str = _UNKNOWN
    fixture_live_replay: str = _UNKNOWN
    human_label_exposure: Optional[float] = None
    source_diet: Dict[str, Any] = field(default_factory=dict)
    safety_status: Dict[str, Any] = field(default_factory=dict)
    soak_report_path: str = ""
    evidence_dossier_path: str = ""
    post_run_autopsy_path: str = ""
    developmental_life_report_path: str = ""
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)
    # Structural comparison profiles (developmental_status / soak_status /
    # world_signature) -- the substance the replication lab aligns/compares.
    developmental_profile: Dict[str, Any] = field(default_factory=dict)
    soak_profile: Dict[str, Any] = field(default_factory=dict)
    world_signature: Dict[str, Any] = field(default_factory=dict)
    stack_metrics: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    uncertainty: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name, value in (("seed", self.seed),
                            ("sensorium_profile",
                             self.sensorium_profile == _UNKNOWN),
                            ("architecture_version",
                             self.architecture_version == _UNKNOWN)):
            if value in (None, True) and name not in self.uncertainty:
                self.uncertainty.append(f"missing {name}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id, "lineage_id": self.lineage_id,
            "state_dir": self.state_dir, "start_ts": self.start_ts,
            "end_ts": self.end_ts, "runtime_duration_s": self.runtime_duration_s,
            "seed": self.seed, "architecture_version": self.architecture_version,
            "commit_hash": self.commit_hash,
            "sensorium_profile": self.sensorium_profile,
            "feeder_profile": self.feeder_profile,
            "fixture_live_replay": self.fixture_live_replay,
            "human_label_exposure": self.human_label_exposure,
            "source_diet": dict(self.source_diet),
            "safety_status": dict(self.safety_status),
            "soak_report_path": self.soak_report_path,
            "evidence_dossier_path": self.evidence_dossier_path,
            "post_run_autopsy_path": self.post_run_autopsy_path,
            "developmental_life_report_path":
                self.developmental_life_report_path,
            "metrics_snapshot": dict(self.metrics_snapshot),
            "developmental_profile": dict(self.developmental_profile),
            "soak_profile": dict(self.soak_profile),
            "world_signature": dict(self.world_signature),
            "stack_metrics": dict(self.stack_metrics),
            "limitations": list(self.limitations),
            "uncertainty": list(self.uncertainty),
        }


@dataclass
class DevelopmentalRunRegistry:
    """Append-only registry of developmental runs (reads only; never runs)."""

    state_dir: str = ".solaris_ai_nn_replication"
    persist: bool = True
    runs: Dict[str, RegisteredDevelopmentalRun] = field(default_factory=dict,
                                                        init=False)
    artifact_index: Dict[str, RunArtifactIndex] = field(default_factory=dict,
                                                        init=False)

    @property
    def _registry_path(self) -> str:
        return os.path.join(self.state_dir, "run_registry.json")

    @property
    def _index_path(self) -> str:
        return os.path.join(self.state_dir, "run_artifact_index.json")

    def register(self, run: RegisteredDevelopmentalRun,
                 ) -> RegisteredDevelopmentalRun:
        self.runs[run.run_id] = run
        self.artifact_index[run.run_id] = self._index_run(run)
        if self.persist:
            self._write()
        return run

    def register_from_dict(self, run_id: str, **fields,
                           ) -> RegisteredDevelopmentalRun:
        run = RegisteredDevelopmentalRun(run_id=run_id, **fields)
        return self.register(run)

    def discover(self, run_id: str, state_dir: str, *,
                 lineage_id: str = "", **fields,
                 ) -> RegisteredDevelopmentalRun:
        """Register a run by discovering its report paths under ``state_dir``."""
        soak = self._find(state_dir, "SOAK_PROTOCOL_REPORT.json")
        dev = self._find(state_dir, "DEVELOPMENTAL_LIFE_REPORT.json")
        run = RegisteredDevelopmentalRun(
            run_id=run_id, lineage_id=lineage_id, state_dir=state_dir,
            soak_report_path=soak or "", evidence_dossier_path=soak or "",
            post_run_autopsy_path=soak or "",
            developmental_life_report_path=dev or "", **fields)
        # Lift comparison profiles out of discovered JSON when present.
        if dev and not run.developmental_profile:
            run.developmental_profile = self._load_status(dev, "status")
        if soak and not run.soak_profile:
            run.soak_profile = self._load_status(soak, "status")
        return self.register(run)

    @staticmethod
    def _find(state_dir: str, filename: str) -> Optional[str]:
        if not os.path.isdir(state_dir):
            return None
        for root, _dirs, files in os.walk(state_dir):
            if filename in files:
                return os.path.join(root, filename)
        return None

    @staticmethod
    def _load_status(path: str, key: str) -> Dict[str, Any]:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            return dict(data.get("sections", {}).get(key, {})) or {}
        except Exception:
            return {}

    def _index_run(self, run: RegisteredDevelopmentalRun) -> RunArtifactIndex:
        idx = RunArtifactIndex(run_id=run.run_id, state_dir=run.state_dir)
        mapping = [
            ("soak_report_path", run.soak_report_path),
            ("evidence_dossier_path", run.evidence_dossier_path),
            ("post_run_autopsy_path", run.post_run_autopsy_path),
            ("developmental_life_report_path",
             run.developmental_life_report_path)]
        for name, path in mapping:
            setattr(idx, name, path)
            if path and os.path.isfile(path):
                idx.discovered.append(path)
            else:
                idx.missing.append(name)
        return idx

    def _write(self) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._registry_path, "w", encoding="utf-8") as fh:
            json.dump({"run_count": len(self.runs),
                       "runs": {rid: r.to_dict()
                                for rid, r in self.runs.items()}},
                      fh, indent=2, default=str)
        with open(self._index_path, "w", encoding="utf-8") as fh:
            json.dump({rid: i.to_dict()
                       for rid, i in self.artifact_index.items()},
                      fh, indent=2, default=str)

    def load(self) -> None:
        if os.path.isfile(self._registry_path):
            with open(self._registry_path, encoding="utf-8") as fh:
                data = json.load(fh)
            for rid, payload in data.get("runs", {}).items():
                payload.pop("run_id", None)
                self.runs[rid] = RegisteredDevelopmentalRun(run_id=rid,
                                                            **payload)

    def ids(self) -> List[str]:
        return sorted(self.runs)

    def status(self) -> Dict[str, Any]:
        return {
            "registered_run_count": len(self.runs),
            "runs": self.ids(),
            "lineages": sorted({r.lineage_id for r in self.runs.values()
                                if r.lineage_id}),
            "runs_with_uncertainty": sorted(
                rid for rid, r in self.runs.items() if r.uncertainty),
            "registry_path": self._registry_path,
            "artifact_index_path": self._index_path,
        }

"""Research result store -- append-only raw results; nothing favourable hidden.

The :class:`ResearchResultStore` persists experiment designs, run results, and an
artifact index as append-only JSONL. Results record the seed, config, and module
toggles; missing artifacts are reported (not silently dropped); and no result --
favourable or not -- is ever deleted.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExperimentResult:
    """One bounded run result (variant, baseline, or ablation)."""

    experiment_id: str
    arm_label: str
    arm_kind: str  # "variant" | "baseline" | "ablation"
    seed: int = 7
    config: Dict[str, Any] = field(default_factory=dict)
    module_toggles: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    missing_artifacts: List[str] = field(default_factory=list)
    safe: bool = True
    unsafe_reason: str = ""
    result_id: str = field(
        default_factory=lambda: f"RES_{uuid.uuid4().hex[:10]}")
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RunArtifactIndex:
    """An index entry for one produced artifact (path + checksum)."""

    result_id: str
    path: str
    exists: bool = False
    checksum: str = ""
    label: str = "fixture"  # fixture | simulated | read_only | sandbox_only

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ResearchResultStore:
    """Append-only store for experiments, results, and artifacts."""

    base_dir: str = ".solaris_ai_nn_research"

    def __post_init__(self) -> None:
        self.experiments_path = os.path.join(self.base_dir, "experiments.jsonl")
        self.results_path = os.path.join(self.base_dir, "results.jsonl")
        self.artifact_index_path = os.path.join(self.base_dir,
                                                "artifact_index.jsonl")
        self.comparisons_dir = os.path.join(self.base_dir, "comparisons")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        self._results: List[ExperimentResult] = []
        self._artifacts: List[RunArtifactIndex] = []

    def _append(self, path: str, obj: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, default=str) + "\n")

    def record_experiment(self, design: Any) -> None:
        self._append(self.experiments_path,
                     design.to_dict() if hasattr(design, "to_dict")
                     else dict(design))

    def record_result(self, result: ExperimentResult) -> ExperimentResult:
        # Append-only: results are never overwritten or deleted.
        self._results.append(result)
        self._append(self.results_path, result.to_dict())
        return result

    def index_artifact(self, result_id: str, path: str,
                       label: str = "fixture") -> RunArtifactIndex:
        exists = bool(path) and os.path.exists(path)
        checksum = ""
        if exists:
            try:
                with open(path, "rb") as fh:
                    checksum = hashlib.sha256(fh.read()).hexdigest()[:16]
            except OSError:
                exists = False
        entry = RunArtifactIndex(result_id=result_id, path=path, exists=exists,
                                 checksum=checksum, label=label)
        self._artifacts.append(entry)
        self._append(self.artifact_index_path, entry.to_dict())
        return entry

    def missing_artifacts(self) -> List[str]:
        return [a.path for a in self._artifacts if not a.exists]

    def write_comparison(self, name: str, data: Dict[str, Any]) -> str:
        os.makedirs(self.comparisons_dir, exist_ok=True)
        path = os.path.join(self.comparisons_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        return path

    def results(self) -> List[ExperimentResult]:
        return list(self._results)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "result_count": len(self._results),
            "artifact_count": len(self._artifacts),
            "missing_artifacts": self.missing_artifacts(),
            "unsafe_results": [r.result_id for r in self._results
                               if not r.safe],
            "results_path": self.results_path,
            "artifact_index_path": self.artifact_index_path,
        }

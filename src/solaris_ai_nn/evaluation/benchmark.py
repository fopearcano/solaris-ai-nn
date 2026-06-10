"""Benchmark schemas -- what was run, how, and what came out.

`ExperimentManifest` pins everything needed to reproduce a run (seed, substrate,
config, features, bounds, state dir). `ExperimentResult` records what actually
happened (success, metrics, artifacts, reproducibility hash, warnings,
limitations). This is the measurement layer's contract: no run without a
manifest, no claim without a metric.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_FEATURES = {
    "plasticity": False, "embodiment": False, "language": False,
    "sidecar": False, "persistence": True, "synthesis": True, "habit": True,
}


def _git_reference() -> Optional[str]:
    """Best-effort current git ref (read from .git directly; no subprocess)."""
    try:
        head = Path(".git/HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1].strip()
            sha_path = Path(".git") / ref
            if sha_path.exists():
                return f"{ref}@{sha_path.read_text().strip()[:12]}"
            return ref
        return head[:12]
    except OSError:
        return None


@dataclass
class ExperimentManifest:
    """Everything needed to (re)run one experiment."""

    name: str
    description: str = ""
    seed: int = 7
    substrate: str = "esn"
    substrate_config: Dict[str, Any] = field(default_factory=dict)
    run_config: Dict[str, Any] = field(default_factory=dict)
    enabled_features: Dict[str, bool] = field(
        default_factory=lambda: dict(DEFAULT_FEATURES))
    max_steps: Optional[int] = 150
    max_duration_s: Optional[float] = None
    state_dir: str = ""
    expected_artifacts: List[str] = field(default_factory=list)
    safety_mode: str = "bounded"  # always bounded for benchmarks
    git_reference: Optional[str] = field(default_factory=_git_reference)
    experiment_id: str = field(
        default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id, "name": self.name,
            "description": self.description, "created_at": self.created_at,
            "seed": self.seed, "substrate": self.substrate,
            "substrate_config": dict(self.substrate_config),
            "run_config": dict(self.run_config),
            "enabled_features": dict(self.enabled_features),
            "max_steps": self.max_steps, "max_duration_s": self.max_duration_s,
            "state_dir": self.state_dir,
            "expected_artifacts": list(self.expected_artifacts),
            "safety_mode": self.safety_mode,
            "git_reference": self.git_reference,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentManifest":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class ExperimentResult:
    """What one bounded benchmark run actually produced."""

    manifest: ExperimentManifest
    success: bool = False
    error: Optional[str] = None
    started_at: float = 0.0
    ended_at: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    reproducibility_hash: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.ended_at - self.started_at)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "success": self.success, "error": self.error,
            "started_at": self.started_at, "ended_at": self.ended_at,
            "duration": self.duration,
            "metrics": dict(self.metrics),
            "artifacts": dict(self.artifacts),
            "reproducibility_hash": self.reproducibility_hash,
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentResult":
        manifest = ExperimentManifest.from_dict(data.get("manifest", {}))
        valid = set(cls.__dataclass_fields__) - {"manifest"}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in valid}
        return cls(manifest=manifest, **kwargs)


@dataclass
class BenchmarkRun:
    """One executed (manifest, result) pair plus where it was written."""

    manifest: ExperimentManifest
    result: ExperimentResult
    run_dir: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"manifest": self.manifest.to_dict(),
                "result": self.result.to_dict(), "run_dir": self.run_dir}


@dataclass
class BenchmarkSuite:
    """A named collection of results with an aggregate summary."""

    name: str = "benchmark_suite"
    results: List[ExperimentResult] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def add(self, result: ExperimentResult) -> None:
        self.results.append(result)

    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "created_at": self.created_at,
            "experiments": len(self.results),
            "succeeded": self.succeeded(), "failed": self.failed(),
            "results": [r.to_dict() for r in self.results],
        }
